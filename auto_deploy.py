import subprocess
import re
import os
import sys

# Paths
root = r"d:\decentralized-voting-system"
blockchain_dir = os.path.join(root, "blockchain")
config_file = os.path.join(root, "backend", "config.py")

def run():
    print("🚀 Starting End-to-End Deployment & Sync...")
    
    # 1. Deploy Contract
    print("📦 Deploying Voting.sol...")
    try:
        result = subprocess.run(
            ["npx", "hardhat", "run", "scripts/deploy.js", "--network", "ganache"],
            cwd=blockchain_dir,
            capture_output=True,
            text=False, # Use bytes
            shell=True
        )
        
        # Decode output
        output = result.stdout
        try:
            text = output.decode("utf-16") if b"\xff\xfe" in output[:2] else output.decode("utf-8")
        except:
            text = output.decode("latin-1")
            
        print("Raw Output Sample:", text[:100])
        
        # Extract Address
        match = re.search(r"0x[a-fA-F0-9]{40}", text)
        if not match:
            print("❌ Error: Could not find contract address in output.")
            print("Full Output:", text)
            return
            
        new_address = match.group(0)
        print(f"✅ Found Full Address: {new_address}")
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return

    # 2. Update config.py
    print("📝 Updating config.py...")
    try:
        with open(config_file, "r") as f:
            lines = f.readlines()
        
        new_lines = []
        updated = False
        for line in lines:
            if "CONTRACT_ADDRESS =" in line:
                new_lines.append(f'CONTRACT_ADDRESS = "{new_address}"\n')
                updated = True
            else:
                new_lines.append(line)
        
        if not updated:
            print("❌ Error: CONTRACT_ADDRESS line not found in config.py")
            return
            
        with open(config_file, "w") as f:
            f.writelines(new_lines)
        print("✅ Config updated.")
        
    except Exception as e:
        print(f"❌ Config update failed: {e}")
        return

    # 3. Final Verification
    print("🧪 Verifying Connection...")
    # Add root to sys.path
    if root not in sys.path: sys.path.append(root)
    # Add backend to sys.path
    backend_path = os.path.join(root, "backend")
    if backend_path not in sys.path: sys.path.append(backend_path)
    
    try:
        from web3 import Web3
        import json
        from config import GANACHE_URL, ABI_PATH
        
        w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
        if w3.is_connected():
            print("✅ Web3 Connected.")
            with open(ABI_PATH) as f:
                abi = json.load(f)["abi"]
            contract = w3.eth.contract(address=new_address, abi=abi)
            state = contract.functions.electionState().call()
            print(f"✅ Contract Verified. State: {state}")
            print("\n🎊 SYSTEM READY!")
        else:
            print("❌ Web3 Connection Failed.")
    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == "__main__":
    run()
