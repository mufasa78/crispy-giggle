import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_jwt_extended import JWTManager

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the base class
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://shopeescraper_owner:npg_zAhujem75qoK@ep-lucky-math-a4xqp14y-pooler.us-east-1.aws.neon.tech/shopeescraper?sslmode=require"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Configure JWT
app.config["JWT_SECRET_KEY"] = os.environ.get("SESSION_SECRET", "default-secret-key")
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
