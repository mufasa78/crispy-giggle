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

@app.route('/import', methods=['GET', 'POST'])
@login_required
def import_data():
    # Get current user
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Check if file was uploaded
        if 'csv_file' not in request.files:
            return render_template('import.html', error='No file uploaded')
        
        file = request.files['csv_file']
        
        # Check if file is empty
        if file.filename == '':
            return render_template('import.html', error='No file selected')
        
        # Check if file is CSV
        if not file.filename.endswith('.csv'):
            return render_template('import.html', error='File must be a CSV')
        
        try:
            # Read CSV file
            csv_data = file.read().decode('latin-1')
            lines = csv_data.splitlines()
            
            # Skip header
            if len(lines) > 0:
                lines = lines[1:]
            
            # Check if there are any product URLs
            if len(lines) == 0:
                return render_template('import.html', error='No product URLs found in the CSV')
            
            # Extract product URLs
            product_urls = []
            for line in lines:
                parts = line.split(',')
                if len(parts) >= 2:
                    product_urls.append(parts[1].strip())
            
            # Check if there are any valid URLs
            if len(product_urls) == 0:
                return render_template('import.html', error='No valid product URLs found in the CSV')
            
            # Process products and create job
            from services.shopee_service import ShopeeService
            from utils.helpers import generate_vendor_job_id
            
            # Generate job ID
            job_name = request.form.get('job_name', '')
            vendor_job_id = f"{job_name}-{generate_vendor_job_id()}" if job_name else generate_vendor_job_id()
            
            # Create new job
            new_job = Job(
                vendor_job_id=vendor_job_id,
                user_id=user.id,
                status='processing'
            )
            db.session.add(new_job)
            db.session.flush()  # Flush to get the job ID
            
            # Process each URL and create deals
            valid_urls = 0
            for priority, url in enumerate(product_urls):
                try:
                    # Extract shop_id and item_id from URL
                    shop_id, item_id = ShopeeService.extract_ids_from_url(url)
                    
                    # Create deal
                    deal_id = f"{shop_id}.{item_id}"
                    step_id = str(priority)  # Use priority as step_id
                    
                    new_deal = Deal(
                        job_id=new_job.id,
                        deal_id=deal_id,
                        step_id=step_id,
                        priority=priority
                    )
                    db.session.add(new_deal)
                    valid_urls += 1
                    
                except Exception as e:
                    logger.error(f"Error processing URL {url}: {str(e)}")
                    continue
            
            if valid_urls == 0:
                db.session.rollback()
                return render_template('import.html', error='No valid Shopee URLs found in the file')
            
            # Create billing record
            billing_record = BillingRecord(
                user_id=user.id,
                job_id=new_job.id,
                product_count=valid_urls
            )
            db.session.add(billing_record)
            
            db.session.commit()
            
            # Process job asynchronously
            from services.job_service import process_job
            process_job(new_job.id)
            
            return render_template(
                'import.html', 
                success=f'Job created with ID: {vendor_job_id}. Processing {valid_urls} products.'
            )
            
        except Exception as e:
            logger.error(f"Error importing CSV: {str(e)}")
            return render_template('import.html', error=f'Error processing file: {str(e)}')
    
    return render_template('import.html')

@app.route('/import/url', methods=['POST'])
@login_required
def import_single_url():
    # Get current user
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    # Get URL from form
    shopee_url = request.form.get('shopee_url')
    
    if not shopee_url:
        return render_template('import.html', error='No URL provided')
    
    if not 'shopee.tw/' in shopee_url or not '-i.' in shopee_url:
        return render_template('import.html', error='Invalid Shopee URL format')
    
    try:
        # Process URL and create job
        from services.shopee_service import ShopeeService
        from utils.helpers import generate_vendor_job_id
        
        # Generate job ID
        job_name = request.form.get('job_name', '')
        vendor_job_id = f"{job_name}-{generate_vendor_job_id()}" if job_name else generate_vendor_job_id()
        
        # Create new job
        new_job = Job(
            vendor_job_id=vendor_job_id,
            user_id=user.id,
            status='processing'
        )
        db.session.add(new_job)
        db.session.flush()  # Flush to get the job ID
        
        # Extract shop_id and item_id from URL
        shop_id, item_id = ShopeeService.extract_ids_from_url(shopee_url)
        
        # Create deal
        deal_id = f"{shop_id}.{item_id}"
        step_id = "1"  # Single URL always has step_id 1
        
        new_deal = Deal(
            job_id=new_job.id,
            deal_id=deal_id,
            step_id=step_id,
            priority=1
        )
        db.session.add(new_deal)
        
        # Create billing record
        billing_record = BillingRecord(
            user_id=user.id,
            job_id=new_job.id,
            product_count=1
        )
        db.session.add(billing_record)
        
        db.session.commit()
        
        # Process job asynchronously
        from services.job_service import process_job
        process_job(new_job.id)
        
        return render_template(
            'import.html', 
            success=f'Job created with ID: {vendor_job_id}. Processing URL: {shopee_url}'
        )
        
    except Exception as e:
        logger.error(f"Error processing URL {shopee_url}: {str(e)}")
        return render_template('import.html', error=f'Error processing URL: {str(e)}')

@app.route('/job/<int:job_id>')
@login_required
def job_detail(job_id):
    # Get current user
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    # Get job
    job = Job.query.get_or_404(job_id)
    
    # Check if user owns the job
    if job.user_id != user.id:
        flash('You do not have permission to view this job')
        return redirect(url_for('dashboard'))
    
    # Get all deals for the job
    deals = Deal.query.filter_by(job_id=job.id).order_by(Deal.priority).all()
    
    # Calculate statistics
    success_count = Deal.query.filter_by(job_id=job.id, status=2).count()  # status 2 = success
    failure_count = Deal.query.filter_by(job_id=job.id, status=3).count()  # status 3 = failure
    
    # Get job result in JSON format
    from services.job_service import get_job_result
    job_result = get_job_result(job.id)
    
    return render_template(
        'job_detail.html',
        job=job,
        deals=deals,
        success_count=success_count,
        failure_count=failure_count,
        job_result=job_result
    )

@app.route('/job/<int:job_id>/export')
@login_required
def job_export(job_id):
    # Get current user
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    # Get job
    job = Job.query.get_or_404(job_id)
    
    # Check if user owns the job
    if job.user_id != user.id:
        flash('You do not have permission to export this job')
        return redirect(url_for('dashboard'))
    
    # Get job result in JSON format
    from services.job_service import get_job_result
    job_result = get_job_result(job.id)
    
    # Return as downloadable JSON file
    from flask import Response
    import json
    from utils.helpers import JSONEncoder
    
    filename = f"shopee_data_{job.vendor_job_id}.json"
    json_data = json.dumps(job_result, cls=JSONEncoder, indent=2)
    
    response = Response(
        json_data,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
    
    return response

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
