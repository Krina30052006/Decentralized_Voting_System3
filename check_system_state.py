#!/usr/bin/env python3
"""Check system state"""
import requests

BASE_URL = "http://127.0.0.1:5000"

print("=== CHECKING SYSTEM STATE ===\n")

# Check if Flask is running
try:
    response = requests.get(f"{BASE_URL}/candidates", timeout=5)
    print(f"✓ Flask backend is running\n")
except:
    print(f"✗ Flask backend is NOT running")
    print(f"  Please start the system first using start.bat\n")
    exit(1)

# Check election status
response = requests.get(f"{BASE_URL}/election/status")
print(f"Election Status: {response.json()}")

# Check candidates
response = requests.get(f"{BASE_URL}/candidates")
candidates = response.json()
print(f"Candidates Count: {len(candidates)}")

if len(candidates) == 0:
    print("\n⚠️  No candidates found in blockchain")
    print("Please add candidates through the admin dashboard first")
else:
    print("Candidates:")
    for c in candidates:
        print(f"  - ID {c['id']}: {c['name']} ({c['party_name']})")

# Check database
print("\n=== DATABASE CHECK ===")
try:
    from backend.database import get_db_connection
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM voters")
    voter_count = cursor.fetchone()[0]
    print(f"Voters in database: {voter_count}")
    cursor.close()
    db.close()
except Exception as e:
    print(f"Database error: {e}")
