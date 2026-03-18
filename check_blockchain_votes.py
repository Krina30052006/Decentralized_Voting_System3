#!/usr/bin/env python3
"""Check if votes are recorded in blockchain"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.blockchain import contract

print("=== BLOCKCHAIN VOTE CHECK ===\n")

try:
    # Get candidate count
    count = contract.functions.getCandidatesCount().call()
    print(f"Candidates in contract: {count}\n")
    
    # Check vote counts for each candidate
    for i in range(1, count + 1):
        candidate = contract.functions.getCandidate(i).call()
        name = candidate[1]
        votes = candidate[6]
        print(f"Candidate {i}: {name} - {votes} votes (in blockchain)")
    
    print("\nIf the vote counts are 0 or low, votes may not be recorded in blockchain.")
    print("They are likely only being stored in database.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
