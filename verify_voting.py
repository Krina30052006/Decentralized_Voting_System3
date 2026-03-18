#!/usr/bin/env python3
"""Verify voting is working end-to-end"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import app
from config import CONTRACT_ADDRESS
import json

print("=== SYSTEM STATUS CHECK ===\n")

# Check config address
print(f"Contract address in config.py: {CONTRACT_ADDRESS}")

# Create test client
client = app.test_client()

# Check candidates
print("\nFetching candidates...")
response = client.get('/candidates')
candidates = response.json
print(f"Status: {response.status_code}")
print(f"Candidates found: {len(candidates)}")

if candidates:
    print("\nCandidates:")
    for c in candidates:
        print(f"  - ID {c['id']}: {c['name']} ({c['party_name']}) - {c['votes']} votes")
    
    # Check election status
    print("\nElection status...")
    response = client.get('/election/status')
    status = response.json
    print(f"Status: {status}")
    
    # Try voting with a test user
    print("\n=== QUICK VOTE TEST ===")
    
    # Register
    print("Registering QUICK-TEST-1...")
    register = client.post('/register', json={
        'voter_id': 'QUICK-TEST-1',
        'name': 'Test User',
        'email': 'test@test.com',
        'password': 'password123'
    })
    print(f"Register: {register.status_code} - {register.json}")
    
    # Login
    print("Logging in...")
    login = client.post('/login', json={
        'voter_id': 'QUICK-TEST-1',
        'password': 'password123'
    })
    print(f"Login: {login.status_code} - {login.json}")
    
    # Vote
    print(f"Voting for candidate {candidates[0]['id']}...")
    vote = client.post('/vote', json={
        'voter_id': 'QUICK-TEST-1',
        'candidate_id': candidates[0]['id']
    })
    print(f"Vote: {vote.status_code} - {vote.json}")
    
    if vote.status_code == 200:
        print("\n✅ SUCCESS: Voting is working!")
    else:
        print(f"\n❌ FAILED: {vote.json}")
else:
    print("❌ No candidates found - the election may not be started")
