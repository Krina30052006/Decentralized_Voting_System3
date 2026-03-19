import os

GANACHE_URL = os.getenv('GANACHE_URL', 'http://127.0.0.1:8545')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS', '0x5FbDB2315678afecb367f032d93F642f64180aa3')
ABI_PATH = os.path.join(os.path.dirname(__file__), '..', 'blockchain', 'artifacts', 'contracts', 'Voting.sol', 'Voting.json')

ADMIN_CREDENTIALS = {
    "username": os.getenv('ADMIN_USERNAME', 'admin'),
    "password": os.getenv('ADMIN_PASSWORD', 'admin123')  # Use env var, not default weak password
}
DB_CONFIG = {
    "host": os.getenv('DB_HOST', 'localhost'),
    "user": os.getenv('DB_USER', 'root'),
    "password": os.getenv('DB_PASSWORD', ''),  # Use env var
    "database": os.getenv('DB_NAME', 'voting_system')
}