#!/usr/bin/env python3
"""Check if votes are actually being recorded in the database"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import get_db_connection

print("=== DATABASE VOTE CHECK ===\n")

try:
    db = get_db_connection()
    cursor = db.cursor()
    
    # Check voters table
    print("Voters in database:")
    cursor.execute("SELECT voter_id, has_voted, wallet_address FROM voters LIMIT 10")
    voters = cursor.fetchall()
    for voter in voters:
        print(f"  - {voter[0]}: has_voted={voter[1]}, wallet={voter[2]}")
    
    print(f"\nTotal voters: ", end="")
    cursor.execute("SELECT COUNT(*) FROM voters")
    count = cursor.fetchone()[0]
    print(count)
    
    # Check if votes are being persisted
    print("\nVoters who have voted:")
    cursor.execute("SELECT voter_id, has_voted FROM voters WHERE has_voted=1")
    voted = cursor.fetchall()
    if voted:
        for v in voted:
            print(f"  - {v[0]}")
    else:
        print("  (none)")
    
    cursor.close()
    db.close()
    
except Exception as e:
    print(f"Database error: {e}")
    import traceback
    traceback.print_exc()
