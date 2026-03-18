from flask import Flask, request, jsonify, send_from_directory, session
from database import db, cursor
from blockchain import web3, contract, account
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
from config import ADMIN_CREDENTIALS, CONTRACT_ADDRESS
import uuid

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key-change-in-prod')  # Use env var for security

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')

@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route("/<path:path>")
def serve_static(path):
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, 'index.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/debug", methods=["GET"])
def debug_info():
    """Debug endpoint to check contract address and candidate count"""
    try:
        count = contract.functions.getCandidatesCount().call()
        return jsonify({
            "contract_address": CONTRACT_ADDRESS,
            "candidate_count": count,
            "web3_connected": web3.is_connected()
        })
    except Exception as e:
        return jsonify({
            "contract_address": CONTRACT_ADDRESS,
            "error": str(e)
        }), 500

def require_admin():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        return jsonify({"message": "Admin authentication required"}), 403
    return None

@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username == ADMIN_CREDENTIALS["username"] and password == ADMIN_CREDENTIALS["password"]:
        session['admin_logged_in'] = True  # Set session for auth
        return jsonify({
            "message": "Admin login successful",
            "is_admin": True
        })
    else:
        return jsonify({"message": "Invalid admin credentials"}), 401

@app.route("/admin/start-election", methods=["POST"])
def start_election():
    auth_check = require_admin()
    if auth_check: return auth_check
    
    try:
        count = contract.functions.getCandidatesCount().call()
        if count == 0:
            return jsonify({"message": "Cannot start election with 0 candidates."}), 400
            
        tx_hash = contract.functions.startElection().transact({"from": account})
        web3.eth.wait_for_transaction_receipt(tx_hash)
        return jsonify({"message": "Election started successfully", "tx_hash": tx_hash.hex()})
    except Exception as e:
        return jsonify({"message": f"Failed to start election: {str(e)}"}), 500

@app.route("/admin/end-election", methods=["POST"])
def end_election():
    auth_check = require_admin()
    if auth_check: return auth_check
    
    try:
        tx_hash = contract.functions.endElection().transact({"from": account})
        web3.eth.wait_for_transaction_receipt(tx_hash)
        return jsonify({"message": "Election ended successfully", "tx_hash": tx_hash.hex()})
    except Exception as e:
        return jsonify({"message": f"Failed to end election: {str(e)}"}), 500

@app.route("/admin/reset", methods=["POST"])
def reset_system():
    auth_check = require_admin()
    if auth_check: return auth_check
    
    try:
        tx_hash = contract.functions.resetSystem().transact({"from": account})
        web3.eth.wait_for_transaction_receipt(tx_hash)
        
        cursor.execute("UPDATE voters SET has_voted = 0")
        db.commit()
        
        return jsonify({"message": "Election records archived. System ready for new round."})
    except Exception as e:
        db.rollback()  # Rollback DB on failure for consistency
        return jsonify({"message": f"Reset failed: {str(e)}"}), 500

@app.route("/election/status", methods=["GET"])
def get_election_status():
    try:
        status_code = contract.functions.electionState().call()
        states = ["NotStarted", "Started", "Ended"]
        return jsonify({"status": states[status_code], "status_code": status_code})
    except Exception as e:
        return jsonify({"message": f"Failed to get status: {str(e)}"}), 500

@app.route("/admin/add-candidate", methods=["POST"])
def add_candidate():
    auth_check = require_admin()
    if auth_check: return auth_check
    
    data = request.json
    name = data.get("name", "").strip()
    party_name = data.get("party_name", "").strip()
    party_logo = data.get("party_logo", "").strip()
    slogan = data.get("slogan", "").strip()
    biography = data.get("biography", "").strip()

    if not name or not party_name or not party_logo:
        return jsonify({"message": "Name, Party, and Logo are required"}), 400

    try:
        tx_hash = contract.functions.addCandidate(name, party_name, party_logo, slogan, biography).transact({"from": account})
        web3.eth.wait_for_transaction_receipt(tx_hash)
        return jsonify({"message": "Candidate added successfully", "tx_hash": tx_hash.hex()})
    except Exception as e:
        return jsonify({"message": f"Failed to add candidate: {str(e)}"}), 500

@app.route("/admin/upload-logo", methods=["POST"])
def upload_logo():
    auth_check = require_admin()
    if auth_check: return auth_check
    
    if 'logo' not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files['logo']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        import time
        filename = f"{int(time.time())}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Dynamic URL based on request
        logo_url = f"{request.host_url}uploads/{filename}"
        return jsonify({"logo_url": logo_url})
    return jsonify({"message": "Invalid file type"}), 400

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/admin/delete-candidate/<int:candidate_id>", methods=["POST"])
def delete_candidate(candidate_id):
    auth_check = require_admin()
    if auth_check: return auth_check
    
    try:
        tx_hash = contract.functions.deleteCandidate(candidate_id).transact({"from": account})
        web3.eth.wait_for_transaction_receipt(tx_hash)
        return jsonify({"message": "Candidate deleted successfully", "tx_hash": tx_hash.hex()})
    except Exception as e:
        return jsonify({"message": f"Failed to delete candidate: {str(e)}"}), 500

@app.route("/admin/voters", methods=["GET"])
def get_all_voters():
    auth_check = require_admin()
    if auth_check: return auth_check
    
    try:
        cursor.execute("SELECT voter_id, name, email, has_voted FROM voters")
        voters = cursor.fetchall()
        result = []
        for v in voters:
            result.append({
                "voter_id": v[0],
                "name": v[1],
                "email": v[2],
                "has_voted": bool(v[3])
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"message": f"Failed to fetch voters: {str(e)}"}), 500

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    voter_id = data.get("voter_id", "").strip()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    
    if not voter_id or not name or not email or not password:
        return jsonify({"message": "All fields are required"}), 400
    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters"}), 400

    hashed_password = generate_password_hash(password)

    # Check for duplicate voter_id
    cursor.execute("SELECT COUNT(*) FROM voters WHERE voter_id = %s", (voter_id,))
    if cursor.fetchone()[0] > 0:
        return jsonify({"message": "Voter ID already exists"}), 400

    accounts = web3.eth.accounts
    if not accounts:
        return jsonify({"message": "Blockchain node has no available accounts. Registration suspended."}), 503
        
    # Use UUID for persistent wallet assignment
    wallet_uuid = str(uuid.uuid4())
    assigned_wallet = accounts[hash(wallet_uuid) % len(accounts)]

    sql = "INSERT INTO voters (voter_id, name, email, password, wallet_address) VALUES (%s,%s,%s,%s,%s)"
    values = (voter_id, name, email, hashed_password, assigned_wallet)

    try:
        cursor.execute(sql, values)
        db.commit()
    except Exception as e:
        return jsonify({"message": f"Registration failed: {str(e)}"}), 500

    return jsonify({"message": "Registration successful"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    voter_id = data.get("voter_id", "").strip()
    password = data.get("password", "").strip()

    if not voter_id or not password:
        return jsonify({"message": "Voter ID and password required"}), 400

    sql = "SELECT password, voter_id FROM voters WHERE voter_id=%s"
    cursor.execute(sql, (voter_id,))
    result = cursor.fetchone()

    if result and check_password_hash(result[0], password):
        return jsonify({"message": "Login successful", "voter_id": result[1]})
    else:
        return jsonify({"message": "Invalid voter ID or password"}), 401

@app.route("/vote", methods=["POST"])
def vote():
    data = request.json
    voter_id = data.get("voter_id", "").strip()
    candidate_id = data.get("candidate_id")
    
    if not voter_id:
        return jsonify({"message": "Voter ID not provided. Are you logged in?"}), 400
    if candidate_id is None or not isinstance(candidate_id, int) or candidate_id <= 0:
        return jsonify({"message": "Valid candidate ID required"}), 400

    sql = "SELECT wallet_address, has_voted FROM voters WHERE voter_id=%s"
    cursor.execute(sql, (voter_id,))
    res = cursor.fetchone()
    
    if not res or not res[0]:
        return jsonify({"message": "User wallet not found."}), 404
    if res[1]:
        return jsonify({"message": "You have already voted."}), 400
        
    voter_wallet = res[0]

    try:
        tx_hash = contract.functions.vote(candidate_id).transact({"from": voter_wallet})
        web3.eth.wait_for_transaction_receipt(tx_hash)

        cursor.execute("UPDATE voters SET has_voted=1 WHERE voter_id=%s", (voter_id,))
        db.commit()

        return jsonify({"message": "Vote recorded successfully"})
    except Exception as e:
        db.rollback()  # Rollback DB on TX failure
        error_msg = str(e)
        if "already voted" in error_msg.lower():
            return jsonify({"message": "Error: You have already voted."}), 400
        elif "Action not allowed" in error_msg:
            return jsonify({"message": "Voting is not currently allowed."}), 400
        return jsonify({"message": "Unable to record vote right now. Please try again."}), 500

@app.route("/candidates", methods=["GET"])
def get_candidates():
    candidates = []
    try:
        count = contract.functions.getCandidatesCount().call()
        for i in range(1, count + 1):
            candidate = contract.functions.getCandidate(i).call()
            if not candidate[7]:  # isDeleted
                candidates.append({
                    "id": candidate[0],
                    "name": candidate[1],
                    "party_name": candidate[2],
                    "party_logo": candidate[3],
                    "slogan": candidate[4],
                    "biography": candidate[5],
                    "votes": candidate[6]
                })
    except Exception as e:
        print(f"Error getting candidates: {e}")
    return jsonify(candidates)

@app.route("/results", methods=["GET"])
def get_results():
    results = []
    try:
        count = contract.functions.getCandidatesCount().call()
        for i in range(1, count + 1):
            candidate = contract.functions.getCandidate(i).call()
            if not candidate[7]:  # isDeleted
                results.append({
                    "candidate": candidate[1],
                    "party": candidate[2],
                    "votes": candidate[6]
                })
    except Exception as e:
        print(f"Error getting results: {e}")
    return jsonify(results)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)  # Removed debug, added host for deployment