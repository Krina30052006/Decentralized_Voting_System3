from flask import Flask, request, jsonify, send_from_directory, session, g
from database import db, cursor, init_request_db, get_request_cursor, get_request_db, close_request_db, get_db_connection
from blockchain import web3, contract, account
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
import random
import re
import time
from config import ADMIN_CREDENTIALS, CONTRACT_ADDRESS
import logging

# Set up logging to file
logging.basicConfig(
    filename='flask_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
error_logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key-change-in-prod')  # Use env var for security

# Flask request context setup for database connections
@app.before_request
def setup_db():
    """Initialize database connection for this request"""
    import traceback
    try:
        error_logger.info(f"Setting up DB for request: {request.method} {request.path}")
        init_request_db()
        error_logger.info("DB setup completed successfully")
    except Exception as e:
        exc_trace = traceback.format_exc()
        error_logger.error(f"DATABASE SETUP ERROR: {e}\n{exc_trace}")
        print(f"!!! DATABASE SETUP ERROR !!!")
        print(f"Error: {e}")
        print(exc_trace)
        raise  # Re-raise so Flask catches it properly
        
@app.teardown_request
def close_db(exception=None):
    """Close the database connection at the end of the request"""
    try:
        close_request_db()
        error_logger.debug("DB connection closed")
    except Exception as e:
        error_logger.error(f"Database close error: {e}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')


def _ensure_voter_schema():
    """Ensure required voter profile columns and indexes exist for registration."""
    active_db = db
    active_cursor = cursor
    owns_connection = False

    if not active_db or not active_cursor:
        try:
            active_db = get_db_connection()
            active_cursor = active_db.cursor()
            owns_connection = True
        except Exception as e:
            error_logger.warning(f"Skipping voter schema check: DB unavailable ({e})")
            return

    try:
        active_cursor.execute("SHOW COLUMNS FROM voters")
        existing_columns = {row[0] for row in active_cursor.fetchall()}

        if "aadhaar_no" not in existing_columns:
            active_cursor.execute("ALTER TABLE voters ADD COLUMN aadhaar_no VARCHAR(12) DEFAULT NULL")
        if "aadhaar_photo_url" not in existing_columns:
            active_cursor.execute("ALTER TABLE voters ADD COLUMN aadhaar_photo_url VARCHAR(255) DEFAULT NULL")
        if "city" not in existing_columns:
            active_cursor.execute("ALTER TABLE voters ADD COLUMN city VARCHAR(100) DEFAULT NULL")
        if "district" not in existing_columns:
            active_cursor.execute("ALTER TABLE voters ADD COLUMN district VARCHAR(100) DEFAULT NULL")

        active_cursor.execute("SHOW INDEX FROM voters")
        existing_indexes = {row[2] for row in active_cursor.fetchall()}
        if "aadhaar_no" not in existing_indexes:
            active_cursor.execute("ALTER TABLE voters ADD UNIQUE KEY aadhaar_no (aadhaar_no)")

        active_db.commit()
    except Exception as e:
        try:
            active_db.rollback()
        except Exception:
            pass
        error_logger.error(f"Failed to ensure voter schema: {e}")
    finally:
        if owns_connection and active_cursor:
            active_cursor.close()
        if owns_connection and active_db:
            active_db.close()


def _generate_unique_voter_id(cursor_obj) -> str:
    """Generate voter ID in VT#### format, starting from VT1000."""
    cursor_obj.execute(
        """
        SELECT voter_id
        FROM voters
        WHERE voter_id REGEXP '^VT[0-9]{4}$'
        ORDER BY CAST(SUBSTRING(voter_id, 3) AS UNSIGNED) DESC
        LIMIT 1
        """
    )
    row = cursor_obj.fetchone()

    next_number = 1000
    if row and row[0]:
        next_number = int(row[0][2:]) + 1

    if next_number > 9999:
        raise RuntimeError("Voter ID range exhausted for VT#### format")

    while next_number <= 9999:
        voter_id = f"VT{next_number:04d}"
        cursor_obj.execute("SELECT COUNT(*) FROM voters WHERE voter_id = %s", (voter_id,))
        if cursor_obj.fetchone()[0] == 0:
            return voter_id
        next_number += 1

    raise RuntimeError("Could not generate a unique voter ID")


def _ensure_election_scope_schema():
    """Ensure table exists for storing active election city/district scope."""
    active_db = db
    active_cursor = cursor
    owns_connection = False

    if not active_db or not active_cursor:
        try:
            active_db = get_db_connection()
            active_cursor = active_db.cursor()
            owns_connection = True
        except Exception as e:
            error_logger.warning(f"Skipping election scope schema check: DB unavailable ({e})")
            return

    try:
        active_cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS election_scope (
                id INT NOT NULL PRIMARY KEY,
                city VARCHAR(100) DEFAULT NULL,
                district VARCHAR(100) DEFAULT NULL,
                is_active TINYINT(1) NOT NULL DEFAULT 0,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
        )
        active_cursor.execute(
            """
            INSERT INTO election_scope (id, city, district, is_active)
            VALUES (1, NULL, NULL, 0)
            ON DUPLICATE KEY UPDATE id = id
            """
        )
        active_db.commit()
    except Exception as e:
        try:
            active_db.rollback()
        except Exception:
            pass
        error_logger.error(f"Failed to ensure election scope schema: {e}")
    finally:
        if owns_connection and active_cursor:
            active_cursor.close()
        if owns_connection and active_db:
            active_db.close()


def _get_active_election_scope(cursor_obj) -> dict | None:
    cursor_obj.execute("SELECT city, district, is_active FROM election_scope WHERE id = 1")
    row = cursor_obj.fetchone()
    if not row or not row[2]:
        return None
    return {"city": row[0], "district": row[1]}


def _set_active_election_scope(cursor_obj, city: str, district: str):
    cursor_obj.execute(
        """
        INSERT INTO election_scope (id, city, district, is_active)
        VALUES (1, %s, %s, 1)
        ON DUPLICATE KEY UPDATE city = VALUES(city), district = VALUES(district), is_active = 1
        """,
        (city, district),
    )


def _clear_active_election_scope(cursor_obj):
    cursor_obj.execute(
        "UPDATE election_scope SET city = NULL, district = NULL, is_active = 0 WHERE id = 1"
    )


_ensure_voter_schema()
_ensure_election_scope_schema()


def _get_wallets_in_use_by_other_voters(voter_id: str, cursor_obj) -> set[str]:
    """Return normalized wallet addresses currently assigned to other voters."""
    cursor_obj.execute(
        "SELECT wallet_address FROM voters WHERE voter_id <> %s AND wallet_address IS NOT NULL AND wallet_address <> ''",
        (voter_id,),
    )
    return {row[0].lower() for row in cursor_obj.fetchall() if row and row[0]}


def _pick_available_wallet(voter_id: str, cursor_obj) -> str | None:
    """Pick an active node account that is not assigned to another voter."""
    accounts = web3.eth.accounts
    if not accounts:
        return None

    used_wallets = _get_wallets_in_use_by_other_voters(voter_id, cursor_obj)
    for addr in accounts:
        if addr.lower() not in used_wallets:
            return addr

    return None


def resolve_active_wallet(voter_id: str, stored_wallet: str | None, cursor_obj) -> tuple[str, bool]:
    """Return a wallet guaranteed to exist on the active node and unique to this voter."""
    accounts = web3.eth.accounts
    if not accounts:
        raise RuntimeError("Blockchain node has no available accounts")

    used_wallets = _get_wallets_in_use_by_other_voters(voter_id, cursor_obj)
    active_by_lower = {addr.lower(): addr for addr in accounts}

    if stored_wallet:
        active_match = active_by_lower.get(stored_wallet.lower())
        if active_match and active_match.lower() not in used_wallets:
            return active_match, False

    fallback_wallet = _pick_available_wallet(voter_id, cursor_obj)
    if not fallback_wallet:
        raise RuntimeError("No available blockchain account for this voter")

    return fallback_wallet, True

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

    data = request.get_json(silent=True) or {}
    city = data.get("city", "").strip()
    district = data.get("district", "").strip()

    if not city or not district:
        return jsonify({"message": "City and district are required to start a place-based election."}), 400
    
    try:
        count = contract.functions.getCandidatesCount().call()
        if count == 0:
            return jsonify({"message": "Cannot start election with 0 candidates."}), 400
            
        tx_hash = contract.functions.startElection().transact({"from": account})
        web3.eth.wait_for_transaction_receipt(tx_hash)

        _set_active_election_scope(get_request_cursor(), city, district)
        get_request_db().commit()

        return jsonify({
            "message": f"Election started successfully for district {district}, city {city}",
            "tx_hash": tx_hash.hex(),
            "scope": {"city": city, "district": district}
        })
    except Exception as e:
        try:
            get_request_db().rollback()
        except Exception:
            pass
        return jsonify({"message": f"Failed to start election: {str(e)}"}), 500

@app.route("/admin/end-election", methods=["POST"])
def end_election():
    auth_check = require_admin()
    if auth_check: return auth_check
    
    try:
        tx_hash = contract.functions.endElection().transact({"from": account})
        web3.eth.wait_for_transaction_receipt(tx_hash)

        _clear_active_election_scope(get_request_cursor())
        get_request_db().commit()

        return jsonify({"message": "Election ended successfully", "tx_hash": tx_hash.hex()})
    except Exception as e:
        try:
            get_request_db().rollback()
        except Exception:
            pass
        return jsonify({"message": f"Failed to end election: {str(e)}"}), 500

@app.route("/admin/reset", methods=["POST"])
def reset_system():
    auth_check = require_admin()
    if auth_check: return auth_check
    
    try:
        tx_hash = contract.functions.resetSystem().transact({"from": account})
        web3.eth.wait_for_transaction_receipt(tx_hash)
        
        get_request_cursor().execute("UPDATE voters SET has_voted = 0")
        _clear_active_election_scope(get_request_cursor())
        get_request_db().commit()
        
        return jsonify({"message": "Election records archived. System ready for new round."})
    except Exception as e:
        get_request_db().rollback()  # Rollback DB on failure for consistency
        return jsonify({"message": f"Reset failed: {str(e)}"}), 500

@app.route("/election/status", methods=["GET"])
def get_election_status():
    try:
        status_code = contract.functions.electionState().call()
        states = ["NotStarted", "Started", "Ended"]
        scope = _get_active_election_scope(get_request_cursor())
        return jsonify({"status": states[status_code], "status_code": status_code, "scope": scope})
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
        get_request_cursor().execute("SELECT voter_id, name, email, has_voted FROM voters")
        voters = get_request_cursor().fetchall()
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
    if request.content_type and "multipart/form-data" in request.content_type:
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        aadhaar_no = request.form.get("aadhaar_no", "").strip()
        city = request.form.get("city", "").strip()
        district = request.form.get("district", "").strip()
        aadhaar_photo = request.files.get("aadhaar_photo")
    else:
        data = request.get_json(silent=True) or {}
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        aadhaar_no = data.get("aadhaar_no", "").strip()
        city = data.get("city", "").strip()
        district = data.get("district", "").strip()
        aadhaar_photo = None

    if not name or not email or not password or not aadhaar_no or not city or not district:
        return jsonify({"message": "All fields are required"}), 400
    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters"}), 400
    if not re.fullmatch(r"\d{12}", aadhaar_no):
        return jsonify({"message": "Aadhaar number must be exactly 12 digits"}), 400
    if not aadhaar_photo or aadhaar_photo.filename == "":
        return jsonify({"message": "Aadhaar photo is required"}), 400
    if not allowed_file(aadhaar_photo.filename):
        return jsonify({"message": "Aadhaar photo must be an image (png, jpg, jpeg, gif)"}), 400

    hashed_password = generate_password_hash(password)

    cursor_obj = get_request_cursor()
    cursor_obj.execute("SELECT COUNT(*) FROM voters WHERE aadhaar_no = %s", (aadhaar_no,))
    if cursor_obj.fetchone()[0] > 0:
        return jsonify({"message": "Aadhaar number already registered"}), 400

    accounts = web3.eth.accounts
    if not accounts:
        return jsonify({"message": "Blockchain node has no available accounts. Registration suspended."}), 503

    voter_id = _generate_unique_voter_id(cursor_obj)

    assigned_wallet = _pick_available_wallet(voter_id, cursor_obj)
    if not assigned_wallet:
        return jsonify({"message": "No available blockchain wallets left. Please contact admin."}), 503

    safe_filename = secure_filename(aadhaar_photo.filename)
    photo_filename = f"aadhaar_{int(time.time())}_{random.randint(1000, 9999)}_{safe_filename}"
    aadhaar_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
    aadhaar_photo_url = f"{request.host_url}uploads/{photo_filename}"

    sql = (
        "INSERT INTO voters "
        "(voter_id, name, email, password, wallet_address, aadhaar_no, aadhaar_photo_url, city, district) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    )
    values = (voter_id, name, email, hashed_password, assigned_wallet, aadhaar_no, aadhaar_photo_url, city, district)

    try:
        cursor_obj.execute(sql, values)
        get_request_db().commit()
    except Exception as e:
        return jsonify({"message": f"Registration failed: {str(e)}"}), 500

    return jsonify({"message": "Registration successful", "voter_id": voter_id})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    voter_id = data.get("voter_id", "").strip()
    password = data.get("password", "").strip()

    if not voter_id or not password:
        return jsonify({"message": "Voter ID and password required"}), 400

    sql = "SELECT password, voter_id FROM voters WHERE voter_id=%s"
    get_request_cursor().execute(sql, (voter_id,))
    result = get_request_cursor().fetchone()

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

    try:
        # Query voter details
        sql = "SELECT wallet_address, has_voted, city, district FROM voters WHERE voter_id=%s"
        cursor_obj = get_request_cursor()
        cursor_obj.execute(sql, (voter_id,))
        res = cursor_obj.fetchone()
        
        if not res or not res[0]:
            return jsonify({"message": "User wallet not found."}), 404
        if res[1]:
            return jsonify({"message": "You have already voted."}), 400

        election_scope = _get_active_election_scope(cursor_obj)
        if election_scope:
            voter_city = (res[2] or "").strip().lower()
            voter_district = (res[3] or "").strip().lower()
            scope_city = (election_scope["city"] or "").strip().lower()
            scope_district = (election_scope["district"] or "").strip().lower()

            if voter_city != scope_city or voter_district != scope_district:
                return jsonify({
                    "message": (
                        f"Voting restricted: this election is only for district {election_scope['district']}, "
                        f"city {election_scope['city']}."
                    )
                }), 403
            
        voter_wallet, wallet_remapped = resolve_active_wallet(voter_id, res[0], cursor_obj)

        if wallet_remapped:
            cursor_obj.execute(
                "UPDATE voters SET wallet_address=%s WHERE voter_id=%s",
                (voter_wallet, voter_id),
            )
            get_request_db().commit()

        # Perform blockchain transaction
        tx_hash = contract.functions.vote(candidate_id).transact({"from": voter_wallet})
        web3.eth.wait_for_transaction_receipt(tx_hash)

        # Update database (get fresh cursor to avoid state issues)
        db_obj = get_request_db()
        update_cursor = db_obj.cursor()
        update_cursor.execute("UPDATE voters SET has_voted=1 WHERE voter_id=%s", (voter_id,))
        update_cursor.close()
        db_obj.commit()

        return jsonify({"message": "Vote recorded successfully"})
    except Exception as e:
        try:
            get_request_db().rollback()
        except:
            pass
        
        error_msg = str(e)
        error_logger.error(f"Vote error for {voter_id}: {error_msg}")
        print(f"[VOTE ERROR] {voter_id}: {error_msg}")  # Print for immediate visibility
        
        if "already voted" in error_msg.lower():
            return jsonify({"message": "Error: You have already voted."}), 400
        elif "Action not allowed" in error_msg:
            return jsonify({"message": "Voting is not currently allowed."}), 400
        elif "No available blockchain account" in error_msg:
            return jsonify({"message": "No available blockchain wallet for this voter. Please contact admin."}), 503
        elif "not deployed" in error_msg.lower() or "no code" in error_msg.lower():
            return jsonify({"message": "Contract not properly deployed. Try restarting the system."}), 500
        
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