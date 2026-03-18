#!/usr/bin/env python3
"""Test voting with unique user"""
import sys
import os
import uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import app

print("=== FRESH VOTE TEST ===\n")

# Create test client
client = app.test_client()

# Use a unique user ID
unique_id = f"VOTER-{uuid.uuid4().hex[:8].upper()}"
print(f"Testing with voter ID: {unique_id}")

# Register
print("\nStep 1: Register")
register = client.post('/register', json={
    'voter_id': unique_id,
    'name': 'New Test Voter',
    'email': f'{unique_id}@test.com',
    'password': 'password123'
})
print(f"Status: {register.status_code} - {register.json.get('message', register.json)}")

if register.status_code != 200:
    print("Registration failed!")
    sys.exit(1)

# Login
print("\nStep 2: Login")
login = client.post('/login', json={
    'voter_id': unique_id,
    'password': 'password123'
})
print(f"Status: {login.status_code} - {login.json.get('message', login.json)}")

if login.status_code != 200:
    print("Login failed!")
    sys.exit(1)

# Get candidates
print("\nStep 3: Get candidates")
response = client.get('/candidates')
candidates = response.json
print(f"Candidates: {len(candidates)}")
for c in candidates:
    print(f"  - ID {c['id']}: {c['name']} ({c['votes']} votes)")

if not candidates:
    print("No candidates!")
    sys.exit(1)

# Vote
print(f"\nStep 4: Vote for candidate {candidates[0]['id']}")
vote = client.post('/vote', json={
    'voter_id': unique_id,
    'candidate_id': candidates[0]['id']
})
print(f"Status: {vote.status_code} - {vote.json}")

if vote.status_code == 200:
    print("\n✅ SUCCESS: Vote recorded!")
    
    # Try voting again
    print("\nStep 5: Try voting again (should fail)")
    vote2 = client.post('/vote', json={
        'voter_id': unique_id,
        'candidate_id': candidates[1]['id'] if len(candidates) > 1 else candidates[0]['id']
    })
    print(f"Status: {vote2.status_code} - {vote2.json}")
    
    if vote2.status_code == 400 and "already voted" in vote2.json.get("message", "").lower():
        print("\n✅ SUCCESS: Duplicate vote correctly prevented!")
    else:
        print("\n⚠️ Warning: Duplicate vote check may not be working")
else:
    print(f"\n❌ FAILED: {vote.json}")
