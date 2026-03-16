import mysql.connector
from web3 import Web3
import requests
import json
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from config import DB_CONFIG, GANACHE_URL, CONTRACT_ADDRESS, ABI_PATH

def test_connections():
    print("--- 🔍 SYSTEM CONNECTIVITY DIAGNOSTIC ---")
    
    # 1. Database Check
    try:
        db = mysql.connector.connect(**DB_CONFIG)
        print("✅ MySQL: Connected successfully.")
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM voters")
        print(f"   - Voters registered: {cur.fetchone()[0]}")
        db.close()
    except Exception as e:
        print(f"❌ MySQL: Connection failed! {e}")

    # 2. Blockchain Check
    try:
        w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
        if w3.is_connected():
            print(f"✅ Blockchain: Connected to {GANACHE_URL}")
            with open(ABI_PATH) as f:
                abi = json.load(f)["abi"]
            contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
            state = contract.functions.electionState().call()
            states = ["NotStarted", "Started", "Ended"]
            print(f"   - Contract: {CONTRACT_ADDRESS}")
            print(f"   - Election State: {states[state]}")
        else:
            print("❌ Blockchain: Connection failed!")
    except Exception as e:
        print(f"❌ Blockchain: Error! {e}")

    # 3. Flask Backend Check
    try:
        res = requests.get("http://127.0.0.1:5000/")
        if res.status_code == 200:
            print("✅ Flask: Backend is live at http://127.0.0.1:5000")
        else:
            print(f"⚠️ Flask: Backend responded with status {res.status_code}")
    except:
        print("❌ Flask: Backend is not reachable (Check if server is running).")

if __name__ == "__main__":
    test_connections()
