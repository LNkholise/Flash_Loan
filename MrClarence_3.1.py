from web3 import Web3
from eth_utils import to_checksum_address
from eth_account import Account
import time
import json
from Swap import ArbitrageBot
from AaveV3 import AaveV3Lending
from WMA import RealTimePandasWMA

# Infura URL for connecting to the Ethereum mainnet
infura_url = "https://mainnet.infura.io/v3/43c7ce7ab6d34d83b755b2bcbb5314fe"

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(infura_url))

# Initialize the WMA calculator with desired weights
weights = [0.1, 0.2, 0.3, 0.4]  # Example weights, feel free to tweak until perfect
wma_calculator = RealTimePandasWMA(weights)

# Convert pair contract addresses to checksum format
uniswap_pair_address = to_checksum_address("0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852")  # WETH/USDT on Uniswap V2
sushiswap_pair_address = to_checksum_address("0x06da0fd433C1A5d7a4faa01111c044910A184553")  # WETH/USDT on SushiSwap

# WETH and USDT contract addresses
weth_address = to_checksum_address("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2")
usdt_address = to_checksum_address("0xdac17f958d2ee523a2206206994597c13d831ec7")

# Private key for signing transactions
private_key = "af40d562b85cf51a7793ae35040ffb3b172fa24d2a3dca18d0afffa553faae43"

# Create an account object from the private key
account = Account.from_key(private_key)

# Lending pool address
lending_pool_address = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"

# Set the default account for Web3 transactions
w3.eth.default_account = account.address

# Path to Aave V3 ABI file
aave_v3_abi_path = 'aave_abi.json'

# Load the ERC20 ABI file
with open('erc20.json', 'r') as file:
    token_abi = json.load(file)

# Amount to trade in ETH
amount = w3.to_wei(2, 'ether')  # 2 ETH in wei

# Threshold for arbitrage difference
threshold = 0.02

# Initialize the Aave V3 lending pool
aave_lending = AaveV3Lending(
    infura_url=infura_url,
    private_key=private_key,
    lending_pool_address=lending_pool_address,
    aave_v3_abi_path=aave_v3_abi_path
)

# Minimal ABI for Uniswap V2 Pair contract, only including methods used
pair_abi = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"},
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]

# Function to fetch token data from a pair contract
def fetch_token_data(pair_contract):
    reserves = pair_contract.functions.getReserves().call()
    reserve0 = reserves[0]
    reserve1 = reserves[1]

    token0_address = pair_contract.functions.token0().call()
    token1_address = pair_contract.functions.token1().call()

    token0_contract = w3.eth.contract(address=token0_address, abi=token_abi)
    token1_contract = w3.eth.contract(address=token1_address, abi=token_abi)

    name0 = token0_contract.functions.name().call()
    symbol0 = token0_contract.functions.symbol().call()
    name1 = token1_contract.functions.name().call()
    symbol1 = token1_contract.functions.symbol().call()

    decimals0 = token0_contract.functions.decimals().call()
    decimals1 = token1_contract.functions.decimals().call()

    adjusted_reserve0 = reserve0 / (10 ** decimals0)
    adjusted_reserve1 = reserve1 / (10 ** decimals1)

    price0_in_terms_of_1 = adjusted_reserve0 / adjusted_reserve1 if adjusted_reserve1 > 0 else "Infinite or Undefined"
    price1_in_terms_of_0 = adjusted_reserve1 / adjusted_reserve0 if adjusted_reserve0 > 0 else "Infinite or Undefined"

    return {
        "name0": name0,
        "symbol0": symbol0,
        "name1": name1,
        "symbol1": symbol1,
        "price0_in_terms_of_1": price0_in_terms_of_1,
        "price1_in_terms_of_0": price1_in_terms_of_0
    }

# Function to run a swap
def run_swap(weth_address, token_abi, usdt_address, private_key):
    weth_contract = w3.eth.contract(address=weth_address, abi=token_abi)
    usdt_contract = w3.eth.contract(address=usdt_address, abi=token_abi)
    
    bot = ArbitrageBot(w3, weth_contract, usdt_contract, private_key)
    weth_amount = w3.to_wei(2, 'ether')  # Replace with the amount of WETH you want to use
    try:
        txn_hash = bot.execute_arbitrage(weth_amount)
        print(f"Arbitrage executed. Transaction hash: {txn_hash}")
    except Exception as e:
        print(f"An error occurred during swap: {e}")

# Initialize pair contracts for both exchanges
uniswap_pair_contract = w3.eth.contract(address=uniswap_pair_address, abi=pair_abi)
sushiswap_pair_contract = w3.eth.contract(address=sushiswap_pair_address, abi=pair_abi)

# Main loop to continuously fetch prices and check for arbitrage opportunities
while True:
    try:
        # Fetch token data for both exchanges
        uniswap_data = fetch_token_data(uniswap_pair_contract)
        sushiswap_data = fetch_token_data(sushiswap_pair_contract)

        # Calculate the WMA and detect sentiment
        wma, change = wma_calculator.add_data_point(uniswap_data['price1_in_terms_of_0'])

        # Print the prices from both exchanges
        print("Uniswap V2 Prices:")
        print(f"Price of 1 {uniswap_data['name0']} ({uniswap_data['symbol0']}) in {uniswap_data['name1']} ({uniswap_data['symbol1']}): {uniswap_data['price1_in_terms_of_0']}")
        print(f"Price of 1 {uniswap_data['name1']} ({uniswap_data['symbol1']}) in {uniswap_data['name0']} ({uniswap_data['symbol0']}): {uniswap_data['price0_in_terms_of_1']}")

        print("\nSushiSwap Prices:")
        print(f"Price of 1 {sushiswap_data['name0']} ({sushiswap_data['symbol0']}) in {sushiswap_data['name1']} ({sushiswap_data['symbol1']}): {sushiswap_data['price1_in_terms_of_0']}")
        print(f"Price of 1 {sushiswap_data['name1']} ({sushiswap_data['symbol1']}) in {sushiswap_data['name0']} ({sushiswap_data['symbol0']}): {sushiswap_data['price0_in_terms_of_1']}")

        # Check for arbitrage opportunities and sentiment
        price_difference = uniswap_data['price1_in_terms_of_0'] - sushiswap_data['price1_in_terms_of_0']
        if price_difference > threshold and change > 0:
            print(f"\n\nArbitrage detected: {price_difference}!\n")
            print("Positive sentiment detected.")
            
            # Execute arbitrage: Borrow -> Swap -> Repay
            aave_lending.borrow(asset=weth_address, amount=amount, interest_rate_mode=2)
            run_swap(weth_address, token_abi, usdt_address, private_key)
            aave_lending.repay(asset=weth_address, amount=amount, interest_rate_mode=2)

        elif price_difference > threshold and change <= 0:
            print("Price difference detected, but sentiment is not positive. Skipping trade.")
        else:
            print("No significant price difference detected. Skipping trade.")

    except Exception as e:
        print(f"An error occurred: {e}")

    # Wait for some time before the next iteration to avoid overloading the network
    time.sleep(10)
