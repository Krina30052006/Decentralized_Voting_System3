#!/usr/bin/env python3
"""Redeploy contract and update config"""
import subprocess
import sys
import os
import re

BLOCKCHAIN_DIR = "blockchain"

def get_npx_command():
    if sys.platform.startswith("win"):
        return "npx.cmd"
    return "npx"

# Deploy contract
print("Redeploying Voting contract...")
cmd = [get_npx_command(), "hardhat", "run", "scripts/deploy.js", "--network", "localhost"]
result = subprocess.run(
    cmd,
    cwd=BLOCKCHAIN_DIR,
    capture_output=True,
    text=True,
    check=False,
)

output = (result.stdout or "") + "\n" + (result.stderr or "")
print(output)

match = re.search(r"Voting contract deployed to:\s*(0x[a-fA-F0-9]{40})", output)
if not match:
    print("ERROR: Could not parse deployed contract address from output")
    sys.exit(1)

contract_address = match.group(1)
print(f"\nContract deployed at: {contract_address}")

# Update config.py with new address
config_file = "backend/config.py"
with open(config_file, 'r') as f:
    config_content = f.read()

# Replace the hardcoded address
old_address_line = f"CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS', '0x8A791620dd6260079BF849Dc5567aDC3F2FdC318')"
new_address_line = f"CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS', '{contract_address}')"

if old_address_line in config_content:
    config_content = config_content.replace(old_address_line, new_address_line)
    with open(config_file, 'w') as f:
        f.write(config_content)
    print(f"Updated {config_file} with new contract address")
else:
    print(f"Could not find old address line in {config_file}")
    print(f"Please manually update the CONTRACT_ADDRESS in {config_file}")

print("\nDONE. Please restart your system with start.bat")
