from web3 import Web3
from eth_account import Account
import json

class ArbitrageBot:
    def __init__(self, web3, weth_contract, usdt_contract, private_key):
        self.web3 = web3
        self.weth_contract = weth_contract
        self.usdt_contract = usdt_contract
        self.private_key = private_key
        self.wallet_address = self.get_wallet_address_from_private_key()

    def get_wallet_address_from_private_key(self):
        account = Account.from_key(self.private_key)
        return account.address

    def approve(self, token_contract, spender, amount):
        tx = token_contract.functions.approve(spender, amount).build_transaction({
            'from': self.wallet_address,
            'gas': 100000,
            'gasPrice': self.web3.to_wei('5', 'gwei'),
            'nonce': self.web3.eth.get_transaction_count(self.wallet_address),
        })
        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self.web3.to_hex(tx_hash)
        
    def transfer_from(self, token_contract, from_address, to_address, amount):
    	# Fetching the current gas price
    	gas_price = self.web3.to_wei(13, 'gwei')  # Increase by 2 gwei
    	
    	nonce = self.web3.eth.get_transaction_count(self.wallet_address)
    	
    	block = self.web3.eth.get_block("latest")
    	gasLimit = block.gasLimit
    	
    	# Building the transaction
    	tx = token_contract.functions.transferFrom(from_address, to_address, amount).build_transaction({
    	    'from': self.wallet_address,
    	    'gas': 200000,
    	    'gasPrice': gas_price,
    	    'nonce': nonce,
    	})
    
    	# Signing the transaction
    	signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
    
    	# Sending the transaction
    	tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    	
    	#increment the nounce for the next transaction
    	nonce += 1
    	return self.web3.to_hex(tx_hash)


    def execute_arbitrage(self, weth_amount):
        # Step 1: Approve Sushiswap to spend your WETH
        sushiswap_address = Web3.to_checksum_address("0x06da0fd433C1A5d7a4faa01111c044910A184553")
        approve_tx_hash = self.approve(self.weth_contract, sushiswap_address, weth_amount)
        print(f"Approved {weth_amount} WETH to Sushiswap. Transaction hash: {approve_tx_hash}")

        # Step 2: Transfer WETH to Sushiswap to get USDT
        transfer_tx_hash = self.transfer_from(self.weth_contract, self.wallet_address, sushiswap_address, weth_amount)
        print(f"Transferred {weth_amount} WETH to Sushiswap. Transaction hash: {transfer_tx_hash}")

        # Step 3: Approve Uniswap to spend your USDT
        usdt_balance = self.usdt_contract.functions.balanceOf(self.wallet_address).call()
        uniswap_address = Web3.to_checksum_address("0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852")
        approve_tx_hash = self.approve(self.usdt_contract, uniswap_address, usdt_balance)
        print(f"Approved {usdt_balance} USDT to Uniswap. Transaction hash: {approve_tx_hash}")

        # Step 4: Transfer USDT to Uniswap to get WETH
        transfer_tx_hash = self.transfer_from(self.usdt_contract, self.wallet_address, uniswap_address, usdt_balance)
        print(f"Transferred {usdt_balance} USDT to Uniswap. Transaction hash: {transfer_tx_hash}")
