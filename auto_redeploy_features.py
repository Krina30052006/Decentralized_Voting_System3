import subprocess
import re
import os

blockchain_dir = r"d:\decentralized-voting-system\blockchain"
config_file = r"d:\decentralized-voting-system\backend\config.py"

def deploy():
    print("🚀 Deploying Smart Contract with Delete Feature...")
    result = subprocess.run(
        ["npx", "hardhat", "run", "scripts/deploy.js", "--network", "ganache"],
        cwd=blockchain_dir,
        capture_output=True,
        text=False,
        shell=True
    )
    output = result.stdout
    try:
        text = output.decode("utf-16") if b"\xff\xfe" in output[:2] else output.decode("utf-8")
    except:
        text = output.decode("latin-1")
    
    match = re.search(r"0x[a-fA-F0-9]{40}", text)
    if not match:
        print("❌ Could not find address!")
        print(text)
        return
    
    new_address = match.group(0)
    print(f"✅ New Address: {new_address}")
    
    with open(config_file, "r") as f:
        content = f.read()
    
    # Updated regex to be more robust
    updated = re.sub(r'CONTRACT_ADDRESS = "0x[a-fA-F0-9]{40}"', f'CONTRACT_ADDRESS = "{new_address}"', content)
    
    with open(config_file, "w") as f:
        f.write(updated)
    print("✅ Config Updated.")

if __name__ == "__main__":
    deploy()
