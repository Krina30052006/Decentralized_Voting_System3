from web3 import Web3
import json
import os

GANACHE_URL = "http://127.0.0.1:7545"
CONTRACT_ADDRESS = "0xFf7c2AB8F9b8cDBa733D0E37c19aF6a2b247EAf2"
ABI_PATH = r"D:\decentralized-voting-system\blockchain\artifacts\contracts\Voting.sol\Voting.json"

def test():
    try:
        web3 = Web3(Web3.HTTPProvider(GANACHE_URL))
        if not web3.is_connected():
            print("Failed to connect to Ganache")
            return

        print(f"Connected to Ganache: {web3.is_connected()}")
        print(f"Accounts: {web3.eth.accounts}")
        
        with open(ABI_PATH) as f:
            contract_json = json.load(f)
            abi = contract_json["abi"]
        
        contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
        state = contract.functions.electionState().call()
        print(f"Election State: {state}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
