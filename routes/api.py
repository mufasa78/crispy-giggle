import uuid
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app import db
from models import Job, Deal, Product, BillingRecord, User
from services.job_service import process_job, get_job_result, cancel_job
from utils.auth import api_key_required

# Create blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Logger
logger = logging.getLogger(__name__)

@api_bp.route('/', methods=['GET'])
def index():
    """API index route"""
    return jsonify({
        'name': 'Shopee Product Data API',
        'version': 'v1',
        'status': 'active'
    }), 200

@api_bp.route('/job/create', methods=['POST'])
@api_key_required
def create_job():
    """
    Create a new job with multiple product IDs
    
    Request body example:
    {
        "job_id": "34c4e7623450",  # Optional
        "deals": [
            {
                "deal_id": "1988776.7648272833",
                "step_id": "123546",
                "priority": 2
            },
            {
                "deal_id": "1877554.6761418533",
                "step_id": "123893",
                "priority": 1
            }
        ]
    }
    """
    try:
        # Get current user from API key
        current_user = request.current_user
        
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'code': 'invalid_request',
                'message': 'Invalid request body'
            }), 400
        
        # Validate required fields
        if 'deals' not in data or not isinstance(data['deals'], list) or len(data['deals']) == 0:
            return jsonify({
                'success': False,
                'code': 'invalid_deals',
                'message': 'Deals are required and must be a non-empty list'
            }), 400
        
        # Validate each deal
        for deal in data['deals']:
            if not all(key in deal for key in ['deal_id', 'step_id', 'priority']):
                return jsonify({
                    'success': False,
                    'code': 'invalid_deal_data',
                    'message': 'Each deal must contain deal_id, step_id, and priority'
                }), 400
        
        # Generate vendor_job_id if not provided
        vendor_job_id = data.get('job_id', str(uuid.uuid4().hex))
        
        # Check if job with this vendor_job_id already exists
        existing_job = Job.query.filter_by(vendor_job_id=vendor_job_id).first()
        if existing_job:
            return jsonify({
                'success': False,
                'code': 'job_already_exists',
                'message': f'Job with ID {vendor_job_id} already exists'
            }), 409
        
        # Create new job
        new_job = Job(
            vendor_job_id=vendor_job_id,
            user_id=current_user.id,
            status='processing'
        )
        db.session.add(new_job)
        db.session.flush()  # Flush to get the job ID
        
        # Create deals for the job
        for deal_data in data['deals']:
            new_deal = Deal(
                job_id=new_job.id,
                deal_id=deal_data['deal_id'],
                step_id=deal_data['step_id'],
                priority=deal_data['priority']
            )
            db.session.add(new_deal)
        
        # Create billing record
        billing_record = BillingRecord(
            user_id=current_user.id,
            job_id=new_job.id,
            product_count=len(data['deals'])
        )
        db.session.add(billing_record)
        
        db.session.commit()
        
        # Process job asynchronously
        process_job(new_job.id)
        
        # Return success response
        return jsonify({
            'success': True,
            'code': None,
            'message': None,
            'data': {
                'vendor_job_id': vendor_job_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating job: {str(e)}")
        return jsonify({
            'success': False,
            'code': 'server_error',
            'message': 'An error occurred while creating the job'
        }), 500

@api_bp.route('/job/cancel/<vendor_job_id>', methods=['POST'])
@api_key_required
def cancel_job_api(vendor_job_id):
    """
    Cancel a job that is in progress
    """
    logger.info(f"Received cancel request for job {vendor_job_id}")
    logger.info(f"Request headers: {request.headers}")
    
    try:
        # Get current user from API key
        current_user = request.current_user
        logger.info(f"User authenticated: {current_user.username}")
        
        # Get job by vendor_job_id
        job = Job.query.filter_by(vendor_job_id=vendor_job_id).first()
        logger.info(f"Job found: {job is not None}")
        
        if not job:
            return jsonify({
                'success': False,
                'code': 'job_not_found',
                'message': f'Job with ID {vendor_job_id} not found'
            }), 404
        
        # Check if user owns the job
        if job.user_id != current_user.id:
            return jsonify({
                'success': False,
                'code': 'unauthorized',
                'message': 'You do not have permission to cancel this job'
            }), 403
        
        # Check if job is already completed
        if job.status in ('success', 'failure', 'cancelled'):
            return jsonify({
                'success': False,
                'code': 'job_already_completed',
                'message': f'Job is already in state: {job.status} and cannot be cancelled'
            }), 400
        
        # Cancel the job
        logger.info(f"Attempting to cancel job {job.id}")
        result = cancel_job(job.id)
        logger.info(f"Cancel job result: {result}")
        
        if result:
            return jsonify({
                'success': True,
                'code': None,
                'message': None,
                'data': {
                    'vendor_job_id': vendor_job_id,
                    'status': 'cancelled'
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'code': 'cancel_error',
                'message': 'Failed to cancel the job'
            }), 500
        
    except Exception as e:
        logger.error(f"Error cancelling job: {str(e)}")
        return jsonify({
            'success': False,
            'code': 'server_error',
            'message': 'An error occurred while cancelling the job'
        }), 500

@api_bp.route('/job/result/<vendor_job_id>', methods=['GET'])
@api_key_required
def get_job_results(vendor_job_id):
    """
    Retrieve the product results by job ID
    """
    try:
        # Get current user from API key
        current_user = request.current_user
        
        # Get job by vendor_job_id
        job = Job.query.filter_by(vendor_job_id=vendor_job_id).first()
        
        if not job:
            return jsonify({
                'success': False,
                'code': 'job_not_found',
                'message': f'Job with ID {vendor_job_id} not found'
            }), 404
        
        # Check if user owns the job
        if job.user_id != current_user.id:
            return jsonify({
                'success': False,
                'code': 'unauthorized',
                'message': 'You do not have permission to access this job'
            }), 403
        
        # Get job results
        result = get_job_result(job.id)
        
        # Return success response
        return jsonify({
            'success': True,
            'code': None,
            'message': None,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting job results: {str(e)}")
        return jsonify({
            'success': False,
            'code': 'server_error',
            'message': 'An error occurred while retrieving job results'
        }), 500

@api_bp.errorhandler(404)
def handle_not_found(e):
    return jsonify({
        'success': False,
        'code': 'not_found',
        'message': 'The requested resource was not found'
    }), 404

@api_bp.errorhandler(405)
def handle_method_not_allowed(e):
    return jsonify({
        'success': False,
        'code': 'method_not_allowed',
        'message': 'The method is not allowed for the requested URL'
    }), 405

@api_bp.errorhandler(500)
def handle_server_error(e):
    return jsonify({
        'success': False,
        'code': 'server_error',
        'message': 'An internal server error occurred'
    }), 500
