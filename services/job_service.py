import logging
import threading
import time
import concurrent.futures
import queue
from datetime import datetime

from app import db, app
from models import Job, Deal, Product
from services.shopee_service import ShopeeService
from config import JOB_BATCH_SIZE, MAX_CONCURRENT_REQUESTS, WORKER_THREADS, MAX_JOBS_IN_QUEUE

# Create a job queue to manage concurrent jobs
job_queue = queue.Queue(maxsize=MAX_JOBS_IN_QUEUE)

# Set to track currently active jobs for cancellation
active_jobs = set()

# Flag to track if worker threads have been started
workers_started = False

# Initialize worker threads
worker_threads = []

# Configure logging
logger = logging.getLogger(__name__)

def start_worker_threads():
    """
    Start worker threads to process jobs from the queue
    """
    global workers_started, worker_threads
    
    if not workers_started:
        logger.info(f"Starting {WORKER_THREADS} worker threads")
        for i in range(WORKER_THREADS):
            thread = threading.Thread(target=_job_worker, name=f"worker-{i}")
            thread.daemon = True
            thread.start()
            worker_threads.append(thread)
        workers_started = True

def _job_worker():
    """
    Worker thread that processes jobs from the queue
    """
    thread_name = threading.current_thread().name
    logger.info(f"Worker thread {thread_name} started")
    
    while True:
        try:
            # Get a job from the queue
            job_id = job_queue.get()
            logger.info(f"Worker {thread_name} processing job {job_id}")
            
            # Process the job
            with app.app_context():
                _process_job_async(job_id)
                
            # Mark the job as done
            job_queue.task_done()
            
        except Exception as e:
            logger.error(f"Error in worker {thread_name}: {str(e)}")
            # Sleep a bit to avoid a tight loop in case of persistent errors
            time.sleep(1)

def process_job(job_id):
    """
    Add a job to the processing queue
    """
    # Make sure worker threads are started
    start_worker_threads()
    
    try:
        # Add the job to the queue
        job_queue.put(job_id, block=False)
        logger.info(f"Added job {job_id} to queue. Queue size: {job_queue.qsize()}/{job_queue.maxsize}")
        return True
    except queue.Full:
        logger.error(f"Job queue is full, cannot add job {job_id}")
        with app.app_context():
            job = Job.query.get(job_id)
            if job:
                job.status = 'queued'
                db.session.commit()
        # Try again in the background after a short delay
        threading.Timer(5, _retry_add_job, args=(job_id,)).start()
        return False
        
def _retry_add_job(job_id):
    """
    Retry adding a job to the queue after a delay
    """
    try:
        logger.info(f"Retrying to add job {job_id} to queue")
        # Try to add to the queue with blocking and timeout
        job_queue.put(job_id, block=True, timeout=10)
        logger.info(f"Successfully added job {job_id} to queue after retry")
    except (queue.Full, Exception) as e:
        logger.error(f"Failed to add job {job_id} to queue after retry: {str(e)}")
        with app.app_context():
            job = Job.query.get(job_id)
            if job:
                job.status = 'error'
                job.completed_at = datetime.utcnow()
                db.session.commit()

def cancel_job(job_id):
    """
    Cancel a job that is in progress or queued
    """
    try:
        with app.app_context():
            # Get the job
            job = Job.query.get(job_id)
            
            if not job:
                logger.error(f"Job with ID {job_id} not found")
                return False
                
            # Check if job is already completed
            if job.status in ('success', 'failure', 'cancelled'):
                logger.warning(f"Cannot cancel job {job_id} because it is already in state: {job.status}")
                return False
                
            # Mark job as cancelled
            job.cancelled = True
            job.status = 'cancelled'
            job.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Job {job_id} has been marked as cancelled")
            
            # Update any unprocessed deals to cancelled state
            unprocessed_deals = Deal.query.filter(Deal.job_id == job_id, Deal.status == 1).all()
            for deal in unprocessed_deals:
                deal.status = 3  # failure
                deal.error_message = "Job cancelled by user"
                deal.processed_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Updated {len(unprocessed_deals)} unprocessed deals for cancelled job {job_id}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {str(e)}")
        return False

def _process_job_async(job_id):
    """
    Internal function to process a job asynchronously
    """
    # Note: Application context is already provided by the worker thread
    try:
        # Add to active jobs
        active_jobs.add(job_id)
        
        # Get job
        job = Job.query.get(job_id)
        
        if not job:
            logger.error(f"Job with ID {job_id} not found")
            active_jobs.discard(job_id)
            return False
        
        # Check if job was cancelled
        if job.cancelled:
            logger.info(f"Job {job_id} was cancelled, skipping processing")
            active_jobs.discard(job_id)
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
            active_jobs.discard(job_id)
            return False
        
        # Process deals in batches to avoid memory issues
        total_deals = len(deals)
        processed_deals = 0
        success_count = 0
        failure_count = 0
        
        logger.info(f"Starting to process {total_deals} deals for job {job_id}")
        
        # Process in batches for better memory management and database performance
        for i in range(0, total_deals, JOB_BATCH_SIZE):
            # Check if job was cancelled mid-processing
            job = Job.query.get(job_id)
            if job.cancelled:
                logger.info(f"Job {job_id} was cancelled during processing, stopping at {processed_deals}/{total_deals} deals")
                active_jobs.discard(job_id)
                return False
                
            batch = deals[i:i+JOB_BATCH_SIZE]
            batch_size = len(batch)
            
            logger.info(f"Processing batch {i//JOB_BATCH_SIZE + 1} with {batch_size} deals for job {job_id}")
            
            # Create a thread pool for concurrent processing within this batch
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
                            
                        # Log progress more frequently for large batches
                        if processed_deals % 50 == 0 or processed_deals == total_deals:
                            logger.info(f"Processed {processed_deals}/{total_deals} deals for job {job_id} (S:{success_count}/F:{failure_count})")
                            
                    except Exception as exc:
                        logger.error(f"Deal {deal.id} generated an exception: {exc}")
                        failure_count += 1
                        
                    # Periodically check if job was cancelled
                    if processed_deals % 100 == 0:
                        # Refresh job to check cancelled flag
                        job = Job.query.get(job_id)
                        if job.cancelled:
                            logger.info(f"Job {job_id} was cancelled during batch processing, stopping at {processed_deals}/{total_deals} deals")
                            executor.shutdown(wait=False)  # Attempt to shut down the executor without waiting
                            active_jobs.discard(job_id)
                            return False
            
            # Commit changes after each batch and update job progress
            job.status = 'processing'
            db.session.commit()
            
            # Give the database a small breather between large batches
            if batch_size >= 100:
                time.sleep(0.5)
        
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
        active_jobs.discard(job_id)
        return True
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        
        try:
            # Update job status to failure
            job = Job.query.get(job_id)
            if job:
                job.status = 'failure'
                job.completed_at = datetime.utcnow()
                db.session.commit()
        except Exception as inner_e:
            logger.error(f"Failed to update job status: {str(inner_e)}")
        
        # Always remove from active jobs set when done
        active_jobs.discard(job_id)
        return False

def _process_deal(deal_id):
    """
    Process a single deal
    """
    # Ensure we have an application context for database operations
    with app.app_context():
        try:
            # Get deal
            deal = Deal.query.get(deal_id)
            
            if not deal:
                logger.error(f"Deal with ID {deal_id} not found")
                return False
            
            # Check if the job was cancelled
            job = Job.query.get(deal.job_id)
            if job and job.cancelled:
                logger.info(f"Skipping deal {deal_id} as job {deal.job_id} was cancelled")
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
            except Exception as inner_e:
                logger.error(f"Failed to update deal status: {str(inner_e)}")
                
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
