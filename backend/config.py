import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join('/app', 'uploads')  # Docker container path
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'eml'}
    
    # Celery settings (using new format without CELERY_ prefix)
    broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    result_expires = timedelta(hours=1)
    timezone = 'UTC'
    enable_utc = True
    
    # Backward compatibility for old Celery settings
    CELERY_BROKER_URL = broker_url
    CELERY_RESULT_BACKEND = result_backend
    CELERY_TASK_SERIALIZER = task_serializer
    CELERY_RESULT_SERIALIZER = result_serializer
    CELERY_ACCEPT_CONTENT = accept_content
    CELERY_TASK_RESULT_EXPIRES = result_expires
    
    # Rate limiting
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
    
    # Security settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Analysis settings
    PHISHING_SCORE_THRESHOLD = 0.7  # Score above this is considered high risk
    SUSPICIOUS_KEYWORDS = {
        'urgent', 'account suspended', 'verify your account', 'click here',
        'update your information', 'password expired', 'security alert',
        'unusual activity', 'limited time', 'act now'
    }
    
    # API settings
    API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '100 per hour')
    
    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        # Create upload folder if it doesn't exist
        try:
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        except PermissionError:
            # If we can't create the folder, use a temporary directory
            import tempfile
            Config.UPLOAD_FOLDER = tempfile.gettempdir()
            print(f"Warning: Using temporary directory for uploads: {Config.UPLOAD_FOLDER}")
        
        # Ensure all Celery configurations are available
        if not hasattr(Config, 'broker_url'):
            Config.broker_url = Config.CELERY_BROKER_URL
        if not hasattr(Config, 'result_backend'):
            Config.result_backend = Config.CELERY_RESULT_BACKEND
        if not hasattr(Config, 'task_serializer'):
            Config.task_serializer = Config.CELERY_TASK_SERIALIZER
        if not hasattr(Config, 'result_serializer'):
            Config.result_serializer = Config.CELERY_RESULT_SERIALIZER
        if not hasattr(Config, 'accept_content'):
            Config.accept_content = Config.CELERY_ACCEPT_CONTENT
        if not hasattr(Config, 'result_expires'):
            Config.result_expires = Config.CELERY_TASK_RESULT_EXPIRES