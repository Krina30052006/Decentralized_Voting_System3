#!/usr/bin/env python3
"""
Debug script to test voting without recording
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_vote():
    # Step 1: Register a new voter
    print("\n=== STEP 1: Register New Voter ===")
    voter_id = "DEBUG-VOTER-999"
    payload = {
        "voter_id": voter_id,
        "password": "test123"
    }
    response = requests.post(f"{BASE_URL}/register", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Step 2: Login to get session
    print("\n=== STEP 2: Login ===")
    payload = {
        "voter_id": voter_id,
        "password": "test123"
    }
    response = requests.post(f"{BASE_URL}/login", json=payload, allow_redirects=False)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    cookies = response.cookies
    print(f"Cookies set: {cookies}")
    
    # Step 3: Check election status
    print("\n=== STEP 3: Check Election Status ===")
    response = requests.get(f"{BASE_URL}/election/status")
    print(f"Status: {response.status_code}")
    election_data = response.json()
    print(f"Response: {election_data}")
    
    # Step 4: Get candidates
    print("\n=== STEP 4: Get Candidates ===")
    response = requests.get(f"{BASE_URL}/candidates")
    print(f"Status: {response.status_code}")
    candidates = response.json()
    print(f"Candidates: {candidates}")
    
    if not candidates:
        print("ERROR: No candidates available!")
        return
    
    # Step 5: Try to vote
    print("\n=== STEP 5: Submit Vote ===")
    candidate_id = candidates[0]['id']
    print(f"Voting for candidate ID: {candidate_id}")
    
    payload = {
        "voter_id": voter_id,
        "candidate_id": candidate_id
    }
    response = requests.post(f"{BASE_URL}/vote", json=payload, cookies=cookies)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Step 6: Check if vote was recorded in DB
    print("\n=== STEP 6: Verify Vote Recorded ===")
    # Try voting again - should be blocked
    payload = {
        "voter_id": voter_id,
        "candidate_id": candidate_id
    }
    response = requests.post(f"{BASE_URL}/vote", json=payload, cookies=cookies)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 400 and "already voted" in response.json().get("message", "").lower():
        print("\n✓ SUCCESS: Vote was properly recorded (duplicate prevention working)")
    else:
        print("\n✗ FAIL: Vote was NOT recorded properly")

if __name__ == "__main__":
    test_vote()
