import os
from datetime import timedelta
from typing import List

class Config:
    """Application configuration with enhanced validation and logging"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///phishguard.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # File upload settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join('/app', 'uploads'))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FOLDER = os.getenv('LOG_FOLDER', os.path.join('/app', 'logs'))
    
    # Celery settings
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TASK_TIMEOUT = int(os.getenv('CELERY_TASK_TIMEOUT', 300))  # 5 minutes
    
    # Security settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Rate limiting settings
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'False').lower() == 'true'
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/1')
    
    # Analysis settings
    MAX_ANALYSIS_TIME = int(os.getenv('MAX_ANALYSIS_TIME', 180))  # 3 minutes
    ENABLE_DETAILED_LOGGING = os.getenv('ENABLE_DETAILED_LOGGING', 'True').lower() == 'true'
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required directories
        if not os.path.exists(cls.UPLOAD_FOLDER):
            issues.append(f"Upload folder does not exist: {cls.UPLOAD_FOLDER}")
        
        if not os.path.exists(cls.LOG_FOLDER):
            issues.append(f"Log folder does not exist: {cls.LOG_FOLDER}")
            
        # Check Redis connection string format
        if not cls.CELERY_BROKER_URL.startswith('redis://'):
            issues.append("CELERY_BROKER_URL must start with 'redis://'")
            
        # Check file size limits
        if cls.MAX_CONTENT_LENGTH > 100 * 1024 * 1024:  # 100MB
            issues.append("MAX_CONTENT_LENGTH should not exceed 100MB")
        
        # Warn about development settings in production
        if not cls.DEBUG and cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            issues.append("Using default SECRET_KEY in production is insecure")
            
        return issues
    
    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        # Create required directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.LOG_FOLDER, exist_ok=True)
        
        # Set directory permissions
        os.chmod(Config.UPLOAD_FOLDER, 0o755)
        os.chmod(Config.LOG_FOLDER, 0o755)
        
        # Validate configuration
        issues = Config.validate_config()
        if issues:
            import logging
            logger = logging.getLogger(__name__)
            for issue in issues:
                logger.warning(f"Configuration issue: {issue}")
        
        # Print configuration summary in debug mode
        if Config.DEBUG:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Configuration loaded:")
            logger.info(f"  Upload folder: {Config.UPLOAD_FOLDER}")
            logger.info(f"  Max file size: {Config.MAX_CONTENT_LENGTH // (1024*1024)}MB")
            logger.info(f"  Debug mode: {Config.DEBUG}")
            logger.info(f"  CORS origins: {Config.CORS_ORIGINS}")

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Production-specific setup
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            file_handler = RotatingFileHandler(
                os.path.join(Config.LOG_FOLDER, 'phishguard.log'),
                maxBytes=10240000,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('PhishGuard startup')

# Configuration selector
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}