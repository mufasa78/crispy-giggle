import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Helper functions for configuration
def get_database_url():
    return os.environ.get("DATABASE_URL")

def get_session_secret():
    return os.environ.get("SESSION_SECRET")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the base class
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = get_session_secret()
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
database_url = get_database_url()
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
}

# Configure JWT
app.config["JWT_SECRET_KEY"] = get_session_secret()  # Use the same secret for simplicity
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 86400  # 24 hours

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# Import routes
with app.app_context():
    # Register API routes
    from routes.api import api_bp
    app.register_blueprint(api_bp)

    # Import models and create tables
    import models
    db.create_all()

    logging.info("Application initialized successfully")

# Ensure the app runs on 0.0.0.0 to make it externally accessible
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
