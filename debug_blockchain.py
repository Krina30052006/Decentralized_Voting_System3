#!/usr/bin/env python3
"""Debug blockchain connection and contract"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config import GANACHE_URL, CONTRACT_ADDRESS, ABI_PATH
from web3 import Web3
import json

print("=== BLOCKCHAIN DEBUG ===\n")

# Check Web3 connection
print(f"Ganache URL: {GANACHE_URL}")
web3 = Web3(Web3.HTTPProvider(GANACHE_URL))
print(f"Connected: {web3.is_connected()}")

if web3.is_connected():
    # Check accounts
    accounts = web3.eth.accounts
    print(f"Available accounts: {len(accounts)}")
    if accounts:
        print(f"  First account: {accounts[0]}")
    
    # Check balance
    if accounts:
        balance = web3.eth.get_balance(accounts[0])
        print(f"  Balance of first account: {balance} wei")
    
    # Check contract address
    contract_address = Web3.to_checksum_address(CONTRACT_ADDRESS)
    print(f"\nContract address (raw): {CONTRACT_ADDRESS}")
    print(f"Contract address (checksum): {contract_address}")
    
    # Check if contract exists at that address
    code = web3.eth.get_code(contract_address)
    print(f"Code at contract address: {len(code)} bytes")
    if len(code) == 0:
        print("  WARNING: No contract code found at this address!")
    
    # Try to call a function
    try:
        with open(ABI_PATH, 'r') as f:
            abi = json.load(f)['abi']
        
        contract = web3.eth.contract(address=contract_address, abi=abi)
        count = contract.functions.getCandidatesCount().call()
        print(f"\ngetCandidatesCount() returned: {count}")
    except Exception as e:
        print(f"\nError calling getCandidatesCount(): {e}")
else:
    print("ERROR: Cannot connect to blockchain!")
