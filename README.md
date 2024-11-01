# Flash Loan trading Bot

This project is designed for real-time arbitrage trading and interactions with Ethereum-based DeFi protocols. It utilizes Web3, Aave V3, and a custom Weighted Moving Average (WMA) calculation to analyze and execute trading opportunities.

## Prerequisites

- **Python 3.9+** (Ensure you have the correct version installed)
- **Ethereum Node Provider**: You need an Ethereum node provider (e.g., Infura or Alchemy) to interact with the blockchain. Set up an account and obtain your API key if you haven’t already.

## Setup Instructions

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your-username/Flash_Loan.git
   cd Flsh_Loan
   
2. **Create a Virtual Environment**

   ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use venv\Scripts\activate

     
3. **Install Dependencies**

   ```bash
    pip install -r requirements.txt

## Configure 

1. **Ethereum Node provider setup**
 -refer to infura.io to set an instance of the infura node for connecting to the Ethereum node(s) : 
   ```bash
    PROVIDER_URL="https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
   PRIVATE_KEY="your_private_key"

2. **Running the trading bot**
      ```bash
    python main.py

## Additional information
- **Testing**: Ensure that you test the bot on a test network (e.g., Ropsten, Rinkeby) before running it on the mainnet.
- 
- **Documentation**: For more information about each function, module, and dependency, refer to the following documentation:
  - [Web3.py Documentation](https://web3py.readthedocs.io/) - Learn about the Web3 library for interacting with Ethereum.
  - [eth-utils Documentation](https://eth-utils.readthedocs.io/) - Find utility functions for Ethereum development.
  - [eth-account Documentation](https://eth-account.readthedocs.io/) - Understand account management and transaction signing.
  - [Infura API Documentation](https://infura.io/docs) - Access Ethereum nodes with Infura’s API.
  - [Aave V3 Protocol Documentation](https://docs.aave.com/) - Explore the Aave V3 lending protocol.
  - [Pandas Documentation](https://pandas.pydata.org/pandas-docs/stable/) - Reference for data manipulation functions if using `RealTimePandasWMA`.
 
- **Code Documentation**: Check the comments in the codebase for specific details on each function and module used in this project.
