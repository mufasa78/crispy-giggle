import os
import logging
from datetime import timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global constants for service configuration
SHOPEE_BASE_URL = "https://shopee.tw"
SHOPEE_API_URL = "https://shopee.tw/api/v4/pdp/get_pc"

# Request configuration
REQUEST_TIMEOUT = 30
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5
USER_AGENT_ROTATION = True
REQUEST_DELAY_MIN = 0.5
REQUEST_DELAY_MAX = 2.0

# Performance and concurrency settings
MAX_CONCURRENT_REQUESTS = 10  # Maximum number of concurrent HTTP requests
WORKER_THREADS = 5            # Number of worker threads for processing jobs
MAX_JOBS_IN_QUEUE = 1000      # Maximum number of jobs to keep in the queue
JOB_BATCH_SIZE = 100          # Number of items to process in a batch
MAX_RETRIES = 3               # Maximum number of retries for failed operations

# Application configuration
class Config:
    """Base configuration"""
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-development-only')
    DEBUG = False
    TESTING = False
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # Check connections before using them
        "pool_recycle": 300,   # Recycle connections after 5 minutes
        "pool_size": 20,       # Maximum number of connections to keep persistently
        "max_overflow": 30,     # Maximum number of connections to create when pool is full
        "pool_timeout": 30,     # Seconds to wait before giving up on getting a connection
    }
    
    # JWT configuration for API authentication
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # API rate limiting
    RATELIMIT_DEFAULT = "2000 per hour"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Job processing configuration
    MAX_WORKER_THREADS = 10     # Number of concurrent worker threads
    BATCH_SIZE = 100            # Number of items to process in a single batch
    JOB_TIMEOUT = 3600          # Maximum job runtime in seconds (1 hour)
    REQUEST_TIMEOUT = 30        # HTTP request timeout in seconds
    RETRY_COUNT = 3             # Number of retries for failed requests
    RETRY_DELAY = 5             # Delay between retries in seconds
    
    # Cache configuration
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300  # Cache timeout in seconds (5 minutes)
    MAX_CACHE_ENTRIES = 10000   # Maximum number of cache entries
    
    # Shopee scraper configuration
    USER_AGENT_ROTATION = True   # Whether to rotate user agents
    REQUEST_DELAY_MIN = 0.5      # Minimum delay between requests (seconds)
    REQUEST_DELAY_MAX = 2.0      # Maximum delay between requests (seconds)
    COOKIE_RENEWAL_INTERVAL = 50 # Renew cookies every N requests
    
    # Enable robust anti-bot measures
    ENABLE_ANTIBOT = True        # Whether to use anti-bot measures
    
    # High-volume data configuration
    ENABLE_HIGH_VOLUME = True    # Enable high-volume processing optimizations
    HIGH_VOLUME_THRESHOLD = 10000  # Threshold for high-volume mode
    
    # Default list of user agents for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.203',
    ]

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    MAX_WORKER_THREADS = 2  # Fewer threads for development
    CACHE_DEFAULT_TIMEOUT = 60  # Shorter cache timeout for development
    REQUEST_DELAY_MIN = 0.1  # Shorter delays for development
    REQUEST_DELAY_MAX = 0.5

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost/test_db'
    MAX_WORKER_THREADS = 1  # Single thread for testing
    
    # Disable anti-bot measures for testing
    ENABLE_ANTIBOT = False
    REQUEST_DELAY_MIN = 0.0
    REQUEST_DELAY_MAX = 0.0

class ProductionConfig(Config):
    """Production configuration"""
    # Stricter security settings
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_CSRF_PROTECT = True
    
    # More aggressive connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 50,         # Larger pool for production
        "max_overflow": 100,      # More overflow connections
        "pool_timeout": 60,
    }
    
    # More worker threads for production
    MAX_WORKER_THREADS = 20
    
    # Enhanced cache settings
    CACHE_DEFAULT_TIMEOUT = 600  # Longer cache timeout
    MAX_CACHE_ENTRIES = 50000   # More cache entries
    
    # More aggressive anti-bot measures
    COOKIE_RENEWAL_INTERVAL = 30

# Load the appropriate configuration based on environment
def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig

# Active configuration
config = get_config()
