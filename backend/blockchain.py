from web3 import Web3
import json
from config import GANACHE_URL, CONTRACT_ADDRESS, ABI_PATH

# Connect to Ganache
web3 = Web3(Web3.HTTPProvider(GANACHE_URL))

# Load ABI
with open(ABI_PATH) as f:
    contract_json = json.load(f)
    abi = contract_json["abi"]

# Connect contract
contract = web3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=abi
)

account = web3.eth.accounts[0]