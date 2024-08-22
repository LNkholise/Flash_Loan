from web3 import Web3
from eth_utils import to_checksum_address
from eth_account import Account
import json

class AaveV3Lending:
    def __init__(self, infura_url, private_key, lending_pool_address, aave_v3_abi_path):
        # Initialize Web3 and Account
        self.w3 = Web3(Web3.HTTPProvider(infura_url))
        self.account = Account.from_key(private_key)
        self.w3.eth.default_account = self.account.address

        # Load Aave V3 Lending Pool ABI
        with open(aave_v3_abi_path, 'r') as abi_file:
            self.lending_pool_abi = json.load(abi_file)

        # Set Lending Pool contract
        self.lending_pool_address = to_checksum_address(lending_pool_address)
        self.lending_pool = self.w3.eth.contract(
            address=self.lending_pool_address,
            abi=self.lending_pool_abi
        )

    def _get_gas_price(self):
        # Fetch the current gas price from the network
        return self.w3.eth.gas_price

    def deposit(self, asset_address, amount):
        asset_contract = self.w3.eth.contract(address=asset_address, abi=self._erc20_abi())
        # Approve the Lending Pool to spend the asset
        tx = asset_contract.functions.approve(self.lending_pool_address, amount).build_transaction({
            'chainId': 1,  # Mainnet
            'gas': 200000,
            'gasPrice': self._get_gas_price(),
            'nonce': self.w3.eth.get_transaction_count(self.account.address)
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        # Deposit into Aave
        tx = self.lending_pool.functions.deposit(asset_address, amount, self.account.address, 0).build_transaction({
            'chainId': 1,
            'gas': 200000,
            'gasPrice': self._get_gas_price(),
            'nonce': self.w3.eth.get_transaction_count(self.account.address) + 1
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self.w3.to_hex(tx_hash)

    def borrow(self, asset_address, amount, interest_rate_mode):
        tx = self.lending_pool.functions.borrow(asset_address, amount, interest_rate_mode, 0, self.account.address).build_transaction({
            'chainId': 1,
            'gas': 200000,
            'gasPrice': self._get_gas_price(),
            'nonce': self.w3.eth.get_transaction_count(self.account.address) + 2
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self.w3.to_hex(tx_hash)

    def repay(self, asset_address, amount):
        asset_contract = self.w3.eth.contract(address=asset_address, abi=self._erc20_abi())
        # Approve the Lending Pool to spend the asset
        tx = asset_contract.functions.approve(self.lending_pool_address, amount).build_transaction({
            'chainId': 1,
            'gas': 200000,
            'gasPrice': self._get_gas_price(),
            'nonce': self.w3.eth.get_transaction_count(self.account.address) + 3
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.private_key)
        self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        # Repay to Aave
        tx = self.lending_pool.functions.repay(asset_address, amount, 0, self.account.address).build_transaction({
            'chainId': 1,
            'gas': 200000,
            'gasPrice': self._get_gas_price(),
            'nonce': self.w3.eth.get_transaction_count(self.account.address) + 4
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self.w3.to_hex(tx_hash)

    def _erc20_abi(self):
        # Minimal ABI for ERC20 token
        return [
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function",
            },
            {
                "constant": True,
                "inputs": [],
                "name": "name",
                "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function",
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function",
            },
            {
                "constant": False,
                "inputs": [
                    {"internalType": "address", "name": "spender", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function",
            }
        ]

