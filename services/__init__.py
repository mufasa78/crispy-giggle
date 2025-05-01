# Services package initialization

# Import all service modules for easy access
try:
    from .job_service import (
        start_worker_threads,
        process_job,
        cancel_job,
        get_job_result
    )
    
    from .shopee_service import ShopeeService
    
    __all__ = [
        'start_worker_threads',
        'process_job',
        'cancel_job',
        'get_job_result',
        'ShopeeService'
    ]
except ImportError as e:
    print(f"Warning: Some service modules could not be imported: {e}")
    __all__ = []
