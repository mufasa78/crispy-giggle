import logging
from functools import wraps
from flask import request, jsonify, g, make_response
from flask_cors import cross_origin

from models import User

# Configure logging
logger = logging.getLogger(__name__)

def handle_options_request(f):
    """
    Decorator to handle OPTIONS requests for CORS preflight
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, X-API-Key, Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            return response
        return f(*args, **kwargs)
    return decorated_function

def api_key_required(f):
    """
    Decorator to require API key authentication
    """
    @wraps(f)
    @handle_options_request
    @cross_origin()
    def decorated_function(*args, **kwargs):
        # Handle CORS preflight requests
        if request.method == 'OPTIONS':
            return make_response()
            
        # Check first for X-API-Key header (used by frontend)
        api_key = request.headers.get('X-API-Key')
        
        # If X-API-Key is not present, check for Authorization header
        if not api_key:
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return jsonify({
                    'success': False,
                    'code': 'unauthorized',
                    'message': 'API key is missing. Please provide either X-API-Key header or Authorization header.'
                }), 401
            
            # Check if Authorization header is in the correct format
            parts = auth_header.split()
            
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return jsonify({
                    'success': False,
                    'code': 'unauthorized',
                    'message': 'Authorization header must be in the format: Bearer {API_KEY}'
                }), 401
            
            api_key = parts[1]
        
        try:
            # Get user by API key
            user = User.query.filter_by(api_key=api_key).first()
            
            if not user:
                return jsonify({
                    'success': False,
                    'code': 'unauthorized',
                    'message': 'Invalid API key'
                }), 401
            
            # Store user in request context
            request.current_user = user
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error authenticating API key: {str(e)}")
            return jsonify({
                'success': False,
                'code': 'server_error',
                'message': 'An error occurred while authenticating'
            }), 500
    
    return decorated_function
