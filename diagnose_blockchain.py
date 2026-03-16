from web3 import Web3
import sys
import os

# Add backend to path to import config
sys.path.append(os.path.join(os.getcwd(), 'backend'))
try:
    from config import GANACHE_URL, CONTRACT_ADDRESS, ABI_PATH
    print(f"Config loaded:")
    print(f" - URL: {GANACHE_URL}")
    print(f" - Contract: {CONTRACT_ADDRESS}")
    print(f" - ABI Path: {ABI_PATH}")
    
    web3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    
    if web3.is_connected():
        print("✅ Successfully connected to Ganache.")
        print(f" - Network ID: {web3.eth.chain_id}")
        print(f" - Block Number: {web3.eth.block_number}")
        print(f" - Accounts found: {len(web3.eth.accounts)}")
        
        # Check if contract has code
        code = web3.eth.get_code(CONTRACT_ADDRESS)
        if code == b'' or code == '0x' or code == '0x0':
            print(f"❌ No contract code found at address {CONTRACT_ADDRESS}. Is it deployed to this network?")
        else:
            print(f"✅ Contract code found at {CONTRACT_ADDRESS}.")
            
    else:
        print(f"❌ Failed to connect to Ganache at {GANACHE_URL}. Is Ganache running?")
        
except Exception as e:
    print(f"❌ Error during test: {str(e)}")
