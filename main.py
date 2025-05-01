import os
import logging
from functools import wraps
from app import app, db
from flask import render_template, redirect, url_for, request, session, flash
from models import User, Job, Deal, Product, BillingRecord
from utils.helpers import hash_password, verify_password, generate_api_key

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set up login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/docs')
def docs():
    return render_template('docs.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if user and verify_password(user.password_hash, password):
            # Store user ID in session
            session['user_id'] = user.id
            session['username'] = user.username
            
            # Redirect to dashboard
            return redirect(url_for('dashboard'))
        else:
            # Return to login page with error
            return render_template('login.html', error='Invalid username or password')
    
    # GET request
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear session
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get current user
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    # Get user's jobs
    jobs = Job.query.filter_by(user_id=user.id).order_by(Job.created_at.desc()).limit(10).all()
    
    # Calculate statistics
    total_jobs = Job.query.filter_by(user_id=user.id).count()
    total_products = Product.query.join(Deal).join(Job).filter(Job.user_id == user.id).count()
    
    # Calculate success rate
    success_count = Job.query.filter_by(user_id=user.id, status='success').count()
    success_rate = int((success_count / total_jobs) * 100) if total_jobs > 0 else 0
    
    # Calculate product count for each job
    for job in jobs:
        job.product_count = Deal.query.filter_by(job_id=job.id).count()
    
    return render_template(
        'dashboard.html',
        jobs=jobs,
        total_jobs=total_jobs,
        total_products=total_products,
        success_rate=success_rate,
        api_key=user.api_key
    )

@app.route('/setup-admin', methods=['GET', 'POST'])
def setup_admin():
    # Check if any users exist
    if User.query.count() > 0:
        flash('Admin user already exists.')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password:
            return render_template('setup_admin.html', error='Username and password are required')
            
        if password != confirm_password:
            return render_template('setup_admin.html', error='Passwords do not match')
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('setup_admin.html', error='Username already exists')
        
        # Create admin user
        hashed_password = hash_password(password)
        api_key = generate_api_key()
        
        new_admin = User(
            username=username,
            password_hash=hashed_password,
            api_key=api_key
        )
        
        db.session.add(new_admin)
        db.session.commit()
        
        flash('Admin user created successfully. Please login.')
        return redirect(url_for('login'))
    
    return render_template('setup_admin.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
