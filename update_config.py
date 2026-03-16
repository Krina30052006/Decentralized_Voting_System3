import os
import re

# Paths
root = r"d:\decentralized-voting-system"
deploy_file = os.path.join(root, "blockchain", "deploy_addr.txt")
config_file = os.path.join(root, "backend", "config.py")

# Try UTF-16LE first (common for PowerShell redirects on Windows)
try:
    with open(deploy_file, "r", encoding="utf-16") as f:
        content = f.read()
except:
    with open(deploy_file, "r") as f:
        content = f.read()

# Match standard Ethereum address
match = re.search(r"0x[a-fA-F0-9]{40}", content)
if match:
    new_address = match.group(0)
    print(f"Found address: {new_address}")
    
    with open(config_file, "r") as f:
        config_content = f.read()
    
    # Replace the existing CONTRACT_ADDRESS line
    new_config = re.sub(r'CONTRACT_ADDRESS = "0x[a-fA-F0-9]{40}"', f'CONTRACT_ADDRESS = "{new_address}"', config_content)
    
    with open(config_file, "w") as f:
        f.write(new_config)
    print("Updated config.py successfully")
else:
    print("Could not find address in deploy_addr.txt")
    print(f"Content length: {len(content)}")
    print(f"Content peek (hex): {content.encode('utf-16').hex()[:50]}")
