# Routes package initialization

from flask import Blueprint
from importlib import import_module

# Import all route modules to register them with the application
try:
    # API routes
    from .api import api_bp
    
    # Import additional route modules as needed
    # from .user_routes import user_bp
    # from .admin_routes import admin_bp
    
    # List of all blueprints for easy import
    all_blueprints = [api_bp]
    
    __all__ = ['api_bp', 'all_blueprints']
except ImportError as e:
    print(f"Warning: Some route modules could not be imported: {e}")
    __all__ = []
