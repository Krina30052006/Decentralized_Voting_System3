import requests

print('=== TESTING VOTE WITH NEW VOTER ===')

# Register brand new voter
print('\n1. Registering new voter...')
reg_data = {'voter_id': 'NEW-VOTER-1', 'name': 'Brand New Voter', 'email': 'new@test.com', 'password': 'pass123'}
reg_resp = requests.post('http://127.0.0.1:5000/register', json=reg_data, timeout=5)
print(f'   Status: {reg_resp.status_code}')

# Try to vote
print('\n2. Voting...')
vote_data = {'voter_id': 'NEW-VOTER-1', 'candidate_id': 1}
vote_resp = requests.post('http://127.0.0.1:5000/vote', json=vote_data, timeout=5)
print(f'   Status: {vote_resp.status_code}')
result = vote_resp.json()
print(f'   Response: {result}')

if vote_resp.status_code == 200:
    print(f'\n✅ SUCCESS: Vote recorded!')
elif vote_resp.status_code == 500:
    print(f'\n❌ ERROR 500: {result.get("message")}')
else:
    print(f'\n⚠️ Status {vote_resp.status_code}: {result.get("message")}')

