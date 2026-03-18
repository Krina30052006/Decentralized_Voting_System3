import requests

print('=== TESTING DUPLICATE VOTE PREVENTION ===')

# Voter already voted
print('\n1. Attempting second vote from same voter...')
vote_data = {'voter_id': 'NEW-VOTER-1', 'candidate_id': 1}
vote_resp = requests.post('http://127.0.0.1:5000/vote', json=vote_data, timeout=5)
print(f'   Status: {vote_resp.status_code}')
result = vote_resp.json()
print(f'   Response: {result}')

if vote_resp.status_code == 400 and 'already voted' in result.get('message','').lower():
    print(f'\n✅ Correctly prevented duplicate vote!')
else:
    print(f'\n❌ Duplicate vote not prevented!')
