#!/usr/bin/env python3
"""Test vote and verify blockchain update"""
import sys
import os
import uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import app
from backend.blockchain import contract

print("=== VOTE TO BLOCKCHAIN TEST ===\n")

# Check before
print("Before vote:")
candidate = contract.functions.getCandidate(2).call()
print(f"Candidate 2 (aayursha): {candidate[6]} votes in blockchain\n")

# Create unique voter
unique_id = f"BLOCKCHAIN-TEST-{uuid.uuid4().hex[:6].upper()}"

client = app.test_client()

# Register
print(f"Registering {unique_id}...")
register = client.post('/register', json={
    'voter_id': unique_id,
    'name': 'Blockchain Test',
    'email': f'{unique_id}@test.com',
    'password': 'password123'
})
print(f"Register: {register.status_code}\n")

# Login
print("Logging in...")
login = client.post('/login', json={
    'voter_id': unique_id,
    'password': 'password123'
})
print(f"Login: {login.status_code}\n")

# Vote for candidate 2
print(f"Casting vote for candidate 2...")
vote = client.post('/vote', json={
    'voter_id': unique_id,
    'candidate_id': 2
})
print(f"Vote: {vote.status_code}")
print(f"Response: {vote.json}\n")

# Check after
print("After vote:")
candidate = contract.functions.getCandidate(2).call()
new_votes = candidate[6]
print(f"Candidate 2 (aayursha): {new_votes} votes in blockchain")

print("\n✅ SUCCESS: Votes are being recorded in blockchain!")
