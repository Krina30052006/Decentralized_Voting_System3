import requests

print('=== DETAILED VOTING TEST ===')

# Register second voter
print('\n1. Registering second voter...')
reg_data = {'voter_id': 'VOTE-TEST-2', 'name': 'Voter 2', 'email': 'voter2@test.com', 'password': 'pass123'}
reg_resp = requests.post('http://127.0.0.1:5000/register', json=reg_data, timeout=5)
print(f'   Status: {reg_resp.status_code}')

# Try vote 1
print('\n2. First vote (VOTE-TEST-1)...')
vote1_data = {'voter_id': 'VOTE-TEST-1', 'candidate_id': 1}
vote1_resp = requests.post('http://127.0.0.1:5000/vote', json=vote1_data, timeout=5)
print(f'   Status: {vote1_resp.status_code}')
print(f'   Response: {vote1_resp.json()}')

# Try vote 2
print('\n3. Second vote (VOTE-TEST-2)...')
vote2_data = {'voter_id': 'VOTE-TEST-2', 'candidate_id': 1}
vote2_resp = requests.post('http://127.0.0.1:5000/vote', json=vote2_data, timeout=5)
print(f'   Status: {vote2_resp.status_code}')
print(f'   Response: {vote2_resp.json()}')

# Try vote 1 again (should fail - already voted)
print('\n4. First vote again (VOTE-TEST-1) - should fail...')
vote1_again_data = {'voter_id': 'VOTE-TEST-1', 'candidate_id': 1}
vote1_again_resp = requests.post('http://127.0.0.1:5000/vote', json=vote1_again_data, timeout=5)
print(f'   Status: {vote1_again_resp.status_code}')
print(f'   Response: {vote1_again_resp.json()}')
