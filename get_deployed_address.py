#!/usr/bin/env python3
"""Check deployed contract address from runtime state file"""
import json
import os
from pathlib import Path

state_file = Path(".runtime/state.json")
if state_file.exists():
    with open(state_file) as f:
        state = json.load(f)
    contract_address = state.get("contract_address")
    print(f"Currently deployed at: {contract_address}")
else:
    print(f"State file not found: {state_file}")
    print("Run start.bat first to deploy the contract")
