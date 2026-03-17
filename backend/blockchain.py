from web3 import Web3
from config import GANACHE_URL, CONTRACT_ADDRESS, ABI_PATH
import json

web3 = Web3(Web3.HTTPProvider(GANACHE_URL))
if not web3.is_connected():
    raise Exception("Cannot connect to blockchain")

with open(ABI_PATH, 'r') as f:
    abi = json.load(f)['abi']

contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
account = web3.eth.accounts[0] if web3.eth.accounts else None
if not account:
    raise Exception("No accounts available in blockchain")