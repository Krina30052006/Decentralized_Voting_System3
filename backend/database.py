import mysql.connector
from config import DB_CONFIG
import threading

# Module-level fallback connections (for non-Flask contexts)
try:
    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()
except Exception as e:
    print(f"Module-level database connection failed: {e}")
    db = None
    cursor = None

def get_db_connection():
    """Get a fresh database connection"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Failed to create database connection: {e}")
        raise

# Flask request-level database management
_thread_local = threading.local()

def init_request_db():
    """Initialize database connection for current request"""
    import traceback
    try:
        _thread_local.db = get_db_connection()
        _thread_local.cursor = _thread_local.db.cursor()
        print(f"[DB] Request DB initialized successfully")
    except Exception as e:
        print(f"[DB] Request DB init error: {e}")
        traceback.print_exc()
        _thread_local.db = None
        _thread_local.cursor = None
        raise

def get_request_cursor():
    """Get cursor for current request"""
    if not hasattr(_thread_local, 'cursor') or _thread_local.cursor is None:
        init_request_db()
    return _thread_local.cursor

def get_request_db():
    """Get connection for current request"""
    if not hasattr(_thread_local, 'db') or _thread_local.db is None:
        init_request_db()
    return _thread_local.db

def close_request_db():
    """Close database connection for current request"""
    if hasattr(_thread_local, 'cursor') and _thread_local.cursor:
        try:
            _thread_local.cursor.close()
        except:
            pass
    if hasattr(_thread_local, 'db') and _thread_local.db:
        try:
            _thread_local.db.close()
        except:
            pass
    # Clear thread-local references
    if hasattr(_thread_local, 'db'):
        _thread_local.db = None
    if hasattr(_thread_local, 'cursor'):
        _thread_local.cursor = None