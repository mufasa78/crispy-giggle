import logging
import threading
import time
import concurrent.futures
from datetime import datetime

from app import db
from models import Job, Deal, Product
from services.shopee_service import ShopeeService
from config import JOB_BATCH_SIZE, MAX_CONCURRENT_REQUESTS

# Configure logging
logger = logging.getLogger(__name__)

def process_job(job_id):
    """
    Process a job asynchronously
    """
    # Start job processing in a separate thread to not block the request
    thread = threading.Thread(target=_process_job_async, args=(job_id,))
    thread.daemon = True
    thread.start()
    
    return True

def _process_job_async(job_id):
    """
    Internal function to process a job asynchronously
    """
    try:
        # Get job
        from flask import current_app
        with current_app.app_context():
            job = Job.query.get(job_id)
            
            if not job:
                logger.error(f"Job with ID {job_id} not found")
                return False
            
            # Update job status to processing if not already
            if job.status != 'processing':
                job.status = 'processing'
                db.session.commit()
            
            # Get all deals for the job
            deals = Deal.query.filter_by(job_id=job.id).order_by(Deal.priority).all()
            
            if not deals:
                logger.warning(f"No deals found for job {job_id}")
                job.status = 'failure'
                job.completed_at = datetime.utcnow()
                db.session.commit()
                return False
            
            # Process deals in batches to avoid memory issues
            total_deals = len(deals)
            processed_deals = 0
            success_count = 0
            failure_count = 0
            
            logger.info(f"Starting to process {total_deals} deals for job {job_id}")
            
            # Process in batches
            for i in range(0, total_deals, JOB_BATCH_SIZE):
                batch = deals[i:i+JOB_BATCH_SIZE]
                
                # Process batch with concurrent workers
                with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
                    # Submit all deals to the executor
                    future_to_deal = {executor.submit(_process_deal, deal.id): deal for deal in batch}
                    
                    # Process results as they complete
                    for future in concurrent.futures.as_completed(future_to_deal):
                        deal = future_to_deal[future]
                        try:
                            result = future.result()
                            processed_deals += 1
                            
                            if result:
                                success_count += 1
                            else:
                                failure_count += 1
                                
                            # Log progress
                            if processed_deals % 100 == 0 or processed_deals == total_deals:
                                logger.info(f"Processed {processed_deals}/{total_deals} deals for job {job_id}")
                                
                        except Exception as exc:
                            logger.error(f"Deal {deal.id} generated an exception: {exc}")
                            failure_count += 1
                
                # Commit changes after each batch
                db.session.commit()
            
            # Update job status based on results
            if failure_count == 0 and success_count > 0:
                job.status = 'success'
            elif success_count == 0:
                job.status = 'failure'
            else:
                job.status = 'partial_success'
                
            job.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Job {job_id} completed: {success_count} successes, {failure_count} failures")
            
            return True
            
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        
        # Update job status to failure
        from flask import current_app
        with current_app.app_context():
            job = Job.query.get(job_id)
            if job:
                job.status = 'failure'
                job.completed_at = datetime.utcnow()
                db.session.commit()
                
        return False

def _process_deal(deal_id):
    """
    Process a single deal
    """
    try:
        # Get deal
        deal = Deal.query.get(deal_id)
        
        if not deal:
            logger.error(f"Deal with ID {deal_id} not found")
            return False
        
        # Update deal status to processing
        deal.status = 1  # processing
        db.session.commit()
        
        # Extract shop_id and item_id from deal_id
        try:
            shop_id, item_id = ShopeeService.extract_item_id_and_shop_id(deal.deal_id)
        except ValueError as e:
            deal.status = 3  # failure
            deal.error_message = str(e)
            deal.processed_at = datetime.utcnow()
            db.session.commit()
            return False
        
        # Fetch product data from Shopee
        try:
            product_data = ShopeeService.fetch_product_data(shop_id, item_id)
            
            # Create product record
            product = Product(
                deal_id=deal.id,
                shopee_item_id=item_id,
                raw_data=product_data
            )
            db.session.add(product)
            
            # Update deal status to success
            deal.status = 2  # success
            deal.processed_at = datetime.utcnow()
            db.session.commit()
            
            return True
            
        except Exception as e:
            # Update deal status to failure
            deal.status = 3  # failure
            deal.error_message = str(e)
            deal.processed_at = datetime.utcnow()
            db.session.commit()
            
            return False
            
    except Exception as e:
        logger.error(f"Error processing deal {deal_id}: {str(e)}")
        
        try:
            # Update deal status to failure
            deal = Deal.query.get(deal_id)
            if deal:
                deal.status = 3  # failure
                deal.error_message = str(e)
                deal.processed_at = datetime.utcnow()
                db.session.commit()
        except:
            pass
            
        return False

def get_job_result(job_id):
    """
    Get the result of a job
    """
    try:
        # Get job
        job = Job.query.get(job_id)
        
        if not job:
            logger.error(f"Job with ID {job_id} not found")
            return None
        
        # Get all deals for the job
        deals = Deal.query.filter_by(job_id=job.id).all()
        
        if not deals:
            logger.warning(f"No deals found for job {job_id}")
            return {
                'vendor_job_id': job.vendor_job_id,
                'status': job.status,
                'deals': []
            }
        
        # Build deals results
        deal_results = []
        for deal in deals:
            # Get product data if available
            product = Product.query.filter_by(deal_id=deal.id).first()
            product_data = product.raw_data if product else None
            
            deal_result = {
                'deal_id': deal.deal_id,
                'step_id': deal.step_id,
                'priority': deal.priority,
                'status': deal.status,
                'data': product_data
            }
            
            deal_results.append(deal_result)
        
        # Build job result
        result = {
            'vendor_job_id': job.vendor_job_id,
            'status': job.status,
            'deals': deal_results
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting job result {job_id}: {str(e)}")
        return None
