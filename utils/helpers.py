import uuid
import hashlib
import logging
import json
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def generate_api_key():
    """
    Generate a unique API key
    """
    return uuid.uuid4().hex

def generate_vendor_job_id():
    """
    Generate a unique vendor job ID
    """
    return uuid.uuid4().hex

def hash_password(password):
    """
    Hash a password using SHA-256
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password):
    """
    Verify a password against a hash
    """
    return stored_hash == hashlib.sha256(password.encode()).hexdigest()

def format_datetime(dt):
    """
    Format a datetime object as ISO 8601 string
    """
    if dt is None:
        return None
    return dt.isoformat()

class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for handling datetime objects
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(JSONEncoder, self).default(obj)
