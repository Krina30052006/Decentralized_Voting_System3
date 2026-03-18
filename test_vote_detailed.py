#!/usr/bin/env python3
"""Test the vote endpoint with detailed error capture"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import app
from database import init_request_db, get_request_db, get_request_cursor, close_request_db
from config import ADMIN_CREDENTIALS
import json

# Create test client
client = app.test_client()

print("=== TESTING VOTE ENDPOINT ===\n")

# Step 1: Login as admin
print("Step 1: Admin login...")
admin_login = client.post('/admin/login', json={
    'username': ADMIN_CREDENTIALS['username'],
    'password': ADMIN_CREDENTIALS['password']
})
print(f"Response: {admin_login.status_code} - {admin_login.json}")

# Step 2: Add a candidate
print("\nStep 2: Add candidate...")
add_candidate = client.post('/admin/add-candidate', json={
    'name': 'John Doe',
    'party_name': 'Party A',
    'party_logo': 'logo_a.png',
    'slogan': 'Vote for change',
    'biography': 'A great candidate'
})
print(f"Response: {add_candidate.status_code} - {add_candidate.json}")

# Step 3: Start election
print("\nStep 3: Start election...")
start_election = client.post('/admin/start-election')
print(f"Response: {start_election.status_code} - {start_election.json}")

# Step 4: Register voter
print("\nStep 4: Register voter...")
register = client.post('/register', json={
    'voter_id': 'TEST-VOTER-100',
    'name': 'Test Voter',
    'email': 'test@example.com',
    'password': 'password123'
})
print(f"Response: {register.status_code} - {register.json}")

# Step 5: Login as voter
print("\nStep 5: Voter login...")
login = client.post('/login', json={
    'voter_id': 'TEST-VOTER-100',
    'password': 'password123'
})
print(f"Response: {login.status_code} - {login.json}")

# Step 6: Get candidates
print("\nStep 6: Get candidates...")
candidates = client.get('/candidates')
print(f"Response: {candidates.status_code}")
candidate_list = candidates.json
print(f"Candidates: {candidate_list}")

if candidate_list:
    candidate_id = candidate_list[0]['id']
    
    # Step 7: Vote
    print(f"\nStep 7: Vote for candidate {candidate_id}...")
    vote = client.post('/vote', json={
        'voter_id': 'TEST-VOTER-100',
        'candidate_id': candidate_id
    })
    print(f"Response: {vote.status_code} - {vote.json}")
else:
    print("No candidates available!")
