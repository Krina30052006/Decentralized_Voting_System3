from flask import Flask, request, jsonify, send_from_directory
from database import db, cursor
from blockchain import web3, contract, account
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
from config import ADMIN_CREDENTIALS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------------------
# HOME
# -------------------------------
@app.route("/")
def home():
    return "Decentralized Voting Backend Running"

# -------------------------------
# ADMIN LOGIN
# -------------------------------
@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username == ADMIN_CREDENTIALS["username"] and password == ADMIN_CREDENTIALS["password"]:
        return jsonify({
            "message": "Admin login successful",
            "is_admin": True
        })
    else:
        return jsonify({"message": "Invalid admin credentials"}), 401

# -------------------------------
# ELECTION CONTROL
# -------------------------------
@app.route("/admin/start-election", methods=["POST"])
def start_election():
    try:
        # Check if contract has candidates for the current round
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
    try:
        tx_hash = contract.functions.endElection().transact({"from": account})
        web3.eth.wait_for_transaction_receipt(tx_hash)
        return jsonify({"message": "Election ended successfully", "tx_hash": tx_hash.hex()})
    except Exception as e:
        return jsonify({"message": f"Failed to end election: {str(e)}"}), 500

@app.route("/admin/reset", methods=["POST"])
def reset_system():
    try:
        # 1. Reset Blockchain (Increments electionRound and sets status to NotStarted)
        tx_hash = contract.functions.resetSystem().transact({"from": account})
        web3.eth.wait_for_transaction_receipt(tx_hash)
        
        # 2. Reset Database (Clear voter turnout flags but keep account data)
        # Result: Voters remain in system, has_voted reset to 0
        cursor.execute("UPDATE voters SET has_voted = 0")
        db.commit()
        
        return jsonify({"message": "Election records archived. System ready for new round."})
    except Exception as e:
        return jsonify({"message": f"Reset failed: {str(e)}"}), 500

@app.route("/election/status", methods=["GET"])
def get_election_status():
    try:
        status_code = contract.functions.electionState().call()
        states = ["NotStarted", "Started", "Ended"]
        return jsonify({"status": states[status_code], "status_code": status_code})
    except Exception as e:
        return jsonify({"message": f"Failed to get status: {str(e)}"}), 500

# -------------------------------
# CANDIDATE MANAGEMENT
# -------------------------------
@app.route("/admin/add-candidate", methods=["POST"])
def add_candidate():
    data = request.json
    name = data.get("name")
    party_name = data.get("party_name")
    party_logo = data.get("party_logo")
    slogan = data.get("slogan", "")
    biography = data.get("biography", "")

    try:
        tx_hash = contract.functions.addCandidate(name, party_name, party_logo, slogan, biography).transact({"from": account})
        web3.eth.wait_for_transaction_receipt(tx_hash)
        return jsonify({"message": "Candidate added successfully", "tx_hash": tx_hash.hex()})
    except Exception as e:
        return jsonify({"message": f"Failed to add candidate: {str(e)}"}), 500

@app.route("/admin/upload-logo", methods=["POST"])
def upload_logo():
    if 'logo' not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files['logo']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to filename to prevent collisions
        import time
        filename = f"{int(time.time())}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"logo_url": f"http://127.0.0.1:5000/uploads/{filename}"})
    return jsonify({"message": "Invalid file type"}), 400

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/admin/delete-candidate/<int:candidate_id>", methods=["POST"])
def delete_candidate(candidate_id):
    try:
        tx_hash = contract.functions.deleteCandidate(candidate_id).transact({"from": account})
        web3.eth.wait_for_transaction_receipt(tx_hash)
        return jsonify({"message": "Candidate deleted successfully", "tx_hash": tx_hash.hex()})
    except Exception as e:
        return jsonify({"message": f"Failed to delete candidate: {str(e)}"}), 500

@app.route("/admin/voters", methods=["GET"])
def get_all_voters():
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

# -------------------------------
# REGISTER / LOGIN / VOTE (VOTERS)
# -------------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    voter_id = data["voter_id"]
    name = data["name"]
    email = data["email"]
    password = data["password"]
    hashed_password = generate_password_hash(password)

    cursor.execute("SELECT COUNT(*) FROM voters")
    voter_count = cursor.fetchone()[0]
    
    accounts = web3.eth.accounts
    assigned_wallet = accounts[voter_count % len(accounts)]

    sql = "INSERT INTO voters (voter_id, name, email, password, wallet_address) VALUES (%s,%s,%s,%s,%s)"
    values = (voter_id, name, email, hashed_password, assigned_wallet)

    try:
        cursor.execute(sql, values)
        db.commit()
    except Exception as e:
        return jsonify({"message": f"Registration failed: {str(e)}"}), 500

    return jsonify({"message": "Registration successful", "wallet_address": assigned_wallet})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    voter_id = data["voter_id"]
    password = data["password"]

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
    voter_id = data.get("voter_id")
    candidate_id = int(data["candidate_id"])
    
    if not voter_id:
        return jsonify({"message": "Voter ID not provided. Are you logged in?"}), 400

    sql = "SELECT wallet_address FROM voters WHERE voter_id=%s"
    cursor.execute(sql, (voter_id,))
    res = cursor.fetchone()
    
    if not res or not res[0]:
        return jsonify({"message": "User wallet not found."}), 404
        
    voter_wallet = res[0]

    try:
        tx_hash = contract.functions.vote(candidate_id).transact({"from": voter_wallet})
        web3.eth.wait_for_transaction_receipt(tx_hash)

        cursor.execute("UPDATE voters SET has_voted=1 WHERE voter_id=%s", (voter_id,))
        db.commit()

        return jsonify({"message": "Vote recorded successfully", "transaction_hash": tx_hash.hex()})
    except Exception as e:
        error_msg = str(e)
        if "already voted" in error_msg.lower():
            return jsonify({"message": "Error: You have already voted."}), 400
        elif "Action not allowed" in error_msg:
            return jsonify({"message": "Voting is not currently allowed."}), 400
        return jsonify({"message": f"Blockchain error: {error_msg}"}), 500

# -------------------------------
# GET DATA
# -------------------------------
@app.route("/candidates", methods=["GET"])
def get_candidates():
    candidates = []
    try:
        count = contract.functions.getCandidatesCount().call()
        for i in range(1, count + 1):
            candidate = contract.functions.getCandidate(i).call()
            if not candidate[7]: # isDeleted is now 7th index
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
            if not candidate[7]: # isDeleted
                results.append({
                    "candidate": candidate[1],
                    "party": candidate[2],
                    "votes": candidate[6]
                })
    except Exception as e:
        print(f"Error getting results: {e}")
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)