import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

# API Configuration
API_VERSION = 'v1'
BASE_URL = f'/api/{API_VERSION}'

# Shopee API Configuration
SHOPEE_BASE_URL = 'https://shopee.tw/api/v4/pdp/get_pc'

# Authentication Configuration
JWT_SECRET_KEY = os.environ.get('SESSION_SECRET', 'default-secret-key')
JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours

# Job Processing Configuration
JOB_BATCH_SIZE = 500  # Number of product IDs to process in a single batch
MAX_CONCURRENT_REQUESTS = 50  # Maximum number of concurrent requests to Shopee API
REQUEST_TIMEOUT = 20  # Timeout for requests to Shopee API in seconds
RETRY_ATTEMPTS = 3  # Number of retry attempts for failed requests
RETRY_DELAY = 0.5  # Delay between retry attempts in seconds
MAX_JOBS_IN_QUEUE = 10  # Maximum number of jobs that can be in the processing queue
WORKER_THREADS = 5  # Number of worker threads for processing jobs
