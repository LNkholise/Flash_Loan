from web3 import Web3
from eth_utils import to_checksum_address
from eth_account import Account
import time
from Swap import ArbitrageBot
from AaveV3 import AaveV3Lending
from WMA import RealTimePandasWMA

#infura url
infura_url = "https://mainnet.infura.io/v3/43c7ce7ab6d34d83b755b2bcbb5314fe"

# Initialize Web3
w3 = Web3(
    Web3.HTTPProvider(
        infura_url
    )
)

# Pair contract addresses for Uniswap V2 and SushiSwap
uniswap_pair_address = "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852"  # WETH/USDT on Uniswap V2
sushiswap_pair_address = "0x06da0fd433C1A5d7a4faa01111c044910A184553"  # WETH/USDT on SushiSwap

# Convert addresses to checksum format
uniswap_pair_address = to_checksum_address(uniswap_pair_address)
sushiswap_pair_address = to_checksum_address(sushiswap_pair_address)

# WETH and USDT contract 
weth_address = Web3.to_checksum_address("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2")
usdt_address = Web3.to_checksum_address("0xdac17f958d2ee523a2206206994597c13d831ec7")

# Private key
private_key = "af40d562b85cf51a7793ae35040ffb3b172fa24d2a3dca18d0afffa553faae43"

# Create an account object from the private key
account = Account.from_key(private_key)

# Landing pool address
lending_pool_address = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"

# Set the default account
w3.eth.default_account = account.address

# aave abi path
aave_v3_abi_path = 'aave_abi.json'


# Amount to trade in ETH
amount = 2000000000000000000  # 2 ETH in we

# Threshold for arbitrage difference
threshold = 0.02

# Initialize the landing pool, swapping, and Weighted Moving averages
aave_lending = AaveV3Lending(
        infura_url=infura_url,
        private_key=private_key,
        lending_pool_address=lending_pool_address,
        aave_v3_abi_path=aave_v3_abi_path
    )

# Load the ERC20 ABI file
with open('erc20.json', 'r') as file:
    token_abi = json.load(file)

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

# Minimal ABI for ERC20 token contract, only including methods used
erc20_token_abi = token_abi

# Function to run a swap
def run_swap(weth_address, token_abi, usdt_address, private_key):
    weth_contract = web3.eth.contract(address=weth_address, abi=token_abi)
    usdt_contract = web3.eth.contract(address=usdt_address, abi=token_abi)
    
    bot = ArbitrageBot(web3, weth_contract, usdt_contract, private_key)
    weth_amount = web3.to_wei(2, 'ether')# Replace with the amount of WETH you want to use
    try:
        bot.execute_arbitrage(weth_amount)
    except Exception as e:
        print(f"An error occured: {e}")

# Function to fetch token data
def fetch_token_data(pair_contract):
    reserves = pair_contract.functions.getReserves().call()
    reserve0 = reserves[0]
    reserve1 = reserves[1]

    token0_address = pair_contract.functions.token0().call()
    token1_address = pair_contract.functions.token1().call()

    token0_contract = w3.eth.contract(address=token0_address, abi=erc20_token_abi)
    token1_contract = w3.eth.contract(address=token1_address, abi=erc20_token_abi)

    name0 = token0_contract.functions.name().call()
    symbol0 = token0_contract.functions.symbol().call()
    name1 = token1_contract.functions.name().call()
    symbol1 = token1_contract.functions.symbol().call()

    decimals0 = token0_contract.functions.decimals().call()
    decimals1 = token1_contract.functions.decimals().call()

    adjusted_reserve0 = reserve0 / (10**decimals0)
    adjusted_reserve1 = reserve1 / (10**decimals1)

    if adjusted_reserve1 > 0:
        price0_in_terms_of_1 = adjusted_reserve0 / adjusted_reserve1
    else:
        price0_in_terms_of_1 = "Infinite or Undefined"

    if adjusted_reserve0 > 0:
        price1_in_terms_of_0 = adjusted_reserve1 / adjusted_reserve0
    else:
        price1_in_terms_of_0 = "Infinite or Undefined"

    return {
        "name0": name0,
        "symbol0": symbol0,
        "name1": name1,
        "symbol1": symbol1,
        "price0_in_terms_of_1": price0_in_terms_of_1,
        "price1_in_terms_of_0": price1_in_terms_of_0
    }

# Initialize pair contracts for both exchanges
uniswap_pair_contract = w3.eth.contract(address=uniswap_pair_address, abi=pair_abi)
sushiswap_pair_contract = w3.eth.contract(address=sushiswap_pair_address, abi=pair_abi)

# Loop to continuously fetch and print prices
while True:
    try:
        # Fetch token data for both exchanges
        uniswap_data = fetch_token_data(uniswap_pair_contract)
        sushiswap_data = fetch_token_data(sushiswap_pair_contract)

        # Print the results
        print("Uniswap V2 Prices:")
        print(f"Price of 1 {uniswap_data['name0']} ({uniswap_data['symbol0']}) in {uniswap_data['name1']} ({uniswap_data['symbol1']}): {uniswap_data['price1_in_terms_of_0']}")
        print(f"Price of 1 {uniswap_data['name1']} ({uniswap_data['symbol1']}) in {uniswap_data['name0']} ({uniswap_data['symbol0']}): {uniswap_data['price0_in_terms_of_1']}")

        print("\nSushiSwap Prices:")
        print(f"Price of 1 {sushiswap_data['name0']} ({sushiswap_data['symbol0']}) in {sushiswap_data['name1']} ({sushiswap_data['symbol1']}): {sushiswap_data['price1_in_terms_of_0']}")
        print(f"Price of 1 {sushiswap_data['name1']} ({sushiswap_data['symbol1']}) in {sushiswap_data['name0']} ({sushiswap_data['symbol0']}): {sushiswap_data['price0_in_terms_of_1']}")
        
        if (uniswap_data['price1_in_terms_of_0'] - sushiswap_data['price1_in_terms_of_0']) > threshold :
        	print(f"\n\nAn arbitrage of {uniswap_data['price1_in_terms_of_0'] - sushiswap_data['price1_in_terms_of_0']} detected !\n")
        	
        	# 1. Take loan from aavev3
        	borrow_tx_hash = aave_lending.borrow('0xC02aaA39b223FE8D0A0e5C4c7eE8e1F2e2372F3', amount, 1)
   		    print(f'Borrow Transaction Hash: {borrow_tx_hash}')
            
            # 2. Execute Swap with borrowed fee
            run_swap(weth_address, erc20_token_abi, usdt_address, private_key)
        
            # 3. Repay it back
            repay_tx_hash = aave_lending.repay(asset_address, borrow_amount)
            print(f'Repay Transaction Hash: {repay_tx_hash}')

        	
        	# Print the transaction hash
        	print(f"Arbitrage executed. Transaction hash: {txn_hash}")
        else:
        	print(f"\n\nNo arbitrage detected !\n")
        	print(f"Price difference less than ${threshold}")
        # Sleep for a specified interval before fetching the data again
        time.sleep(10)  # Adjust the sleep time as needed (e.g., 60 seconds)
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(60)

