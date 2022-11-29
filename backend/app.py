from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from celery import Celery
from dotenv import load_dotenv
import os
import logging
import uuid
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config
from services.email_analyzer import EmailAnalyzer, EmailAnalysisError, EmailParsingError, FileValidationError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/app.log', mode='a') if os.path.exists('/app/logs') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app with static file serving (both dev and prod)
static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'build')
app = Flask(__name__, static_folder=static_folder, static_url_path='')
app.config.from_object(Config)
Config.init_app(app)

# Enable CORS
CORS(app, origins=app.config['CORS_ORIGINS'])

# Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Request logging middleware
@app.before_request
def log_request_info():
    """Log incoming requests"""
    logger.info(f"Request: {request.method} {request.url} - IP: {request.remote_addr}")

# Initialize Celery - simple approach
celery = Celery(
    'app',  # Simple name
    broker=app.config['CELERY_BROKER_URL'],
    backend=app.config['CELERY_RESULT_BACKEND']
)

# Celery tasks
@celery.task(bind=True)
def analyze_content_task(self, content):
    """Celery task for analyzing email content"""
    try:
        if not content or not content.strip():
            raise ValueError("Empty content provided")
        
        logger.info(f"Starting content analysis task: {self.request.id}")
        result = EmailAnalyzer.analyze_content(content)
        logger.info(f"Content analysis task completed: {self.request.id}")
        return result
    except EmailAnalysisError as e:
        logger.error(f"Email analysis error in task {self.request.id}: {str(e)}")
        return {
            'error': str(e),
            'threat_score': 0.0,
            'risk_level': 'unknown',
            'message': 'Analysis failed due to email processing error'
        }
    except Exception as e:
        logger.error(f"Unexpected error in analyze_content_task {self.request.id}: {str(e)}", exc_info=True)
        self.retry(countdown=60, max_retries=3, exc=e)

@celery.task(bind=True)
def analyze_file_task(self, file_path):
    """Celery task for analyzing email file"""
    try:
        if not file_path:
            raise ValueError("No file path provided")
        
        logger.info(f"Starting file analysis task: {self.request.id} - File: {os.path.basename(file_path)}")
        result = EmailAnalyzer.analyze_file(file_path)
        logger.info(f"File analysis task completed: {self.request.id}")
        
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up temporary file: {file_path}")
        
        return result
    except (FileValidationError, EmailParsingError) as e:
        logger.error(f"File processing error in task {self.request.id}: {str(e)}")
        # Clean up on error too
        if os.path.exists(file_path):
            os.remove(file_path)
        return {
            'error': str(e),
            'threat_score': 0.0,
            'risk_level': 'unknown',
            'message': 'File analysis failed'
        }
    except Exception as e:
        logger.error(f"Unexpected error in analyze_file_task {self.request.id}: {str(e)}", exc_info=True)
        # Clean up on error too
        if os.path.exists(file_path):
            os.remove(file_path)
        self.retry(countdown=60, max_retries=3, exc=e)

def validate_json_request(required_fields=None):
    """Validate JSON request data"""
    if not request.is_json:
        raise ValueError("Request must be JSON")
    
    data = request.get_json()
    if not data:
        raise ValueError("Empty JSON data")
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    return data

def validate_file_upload():
    """Validate file upload request"""
    if 'file' not in request.files:
        raise ValueError("No file provided in request")

    file = request.files['file']
    if not file or not file.filename:
        raise ValueError("No file selected")

    # Validate file extension
    if not file.filename.lower().endswith('.eml'):
        raise ValueError("Invalid file format. Only .eml files are supported")

    # Check file size
    if request.content_length and request.content_length > app.config['MAX_CONTENT_LENGTH']:
        raise ValueError(f"File too large. Maximum size is {app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB")

    return file

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        celery.control.inspect().stats()
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'services': {
                'redis': 'connected',
                'celery': 'running'
            }
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'version': '1.0.0',
            'error': str(e)
        }), 503

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Test endpoint for health check"""
    return jsonify({'status': 'ok', 'message': 'API is working'}), 200

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve React frontend (both dev and prod)"""
    if app.static_folder and os.path.exists(app.static_folder):
        index_path = os.path.join(app.static_folder, 'index.html')
        
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        elif os.path.exists(index_path):
            return send_from_directory(app.static_folder, 'index.html')
        else:
            return jsonify({
                'error': 'Frontend build incomplete',
                'message': 'React build directory exists but index.html is missing.',
                'static_folder': app.static_folder,
                'mode': os.environ.get('MODE', 'production')
            }), 404
    else:
        return jsonify({
            'error': 'Frontend not built',
            'message': 'React build files not found. Try rebuilding the container.',
            'static_folder': app.static_folder,
            'mode': os.environ.get('MODE', 'production'),
            'hint': 'Run: docker-compose up --build'
        }), 404

@app.route('/api/analyze/content', methods=['POST'])
def analyze_email_content():
    """Analyze email content provided in the request body"""
    try:
        # Validate request data
        data = validate_json_request(required_fields=['content'])
        email_content = data['content']
        
        if not email_content or not email_content.strip():
            return jsonify({
                'error': 'Empty email content provided',
                'details': 'Email content cannot be empty'
            }), 400

        # Basic content length validation
        if len(email_content) > 1024 * 1024:  # 1MB limit for content
            return jsonify({
                'error': 'Email content too large',
                'details': 'Maximum content size is 1MB'
            }), 413

        # Create analysis task
        task = analyze_content_task.delay(email_content)
        logger.info(f"Created content analysis task: {task.id}")
        
        return jsonify({
            'task_id': task.id,
            'status': 'processing',
            'message': 'Analysis started successfully'
        }), 202

    except ValueError as e:
        logger.warning(f"Validation error in analyze_email_content: {str(e)}")
        return jsonify({
            'error': 'Invalid request',
            'details': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error analyzing email content: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'details': 'An unexpected error occurred while processing your request'
        }), 500

@app.route('/api/analyze/file', methods=['POST'])
def analyze_email_file():
    """Analyze uploaded email file"""
    try:
        # Validate file upload
        file = validate_file_upload()
        
        # Generate secure filename
        original_filename = secure_filename(file.filename)
        filename = f"{uuid.uuid4()}_{original_filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file with error handling
        try:
            file.save(file_path)
            logger.info(f"Saved uploaded file: {filename} (original: {original_filename})")
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {str(e)}")
            return jsonify({
                'error': 'File save failed',
                'details': 'Unable to save uploaded file'
            }), 500

        # Validate saved file
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return jsonify({
                'error': 'File validation failed',
                'details': 'Uploaded file is empty or corrupted'
            }), 400

        # Create analysis task
        task = analyze_file_task.delay(file_path)
        logger.info(f"Created file analysis task: {task.id} for file: {original_filename}")

        return jsonify({
            'task_id': task.id,
            'status': 'processing',
            'message': 'File analysis started successfully',
            'filename': original_filename
        }), 202

    except ValueError as e:
        logger.warning(f"Validation error in analyze_email_file: {str(e)}")
        return jsonify({
            'error': 'Invalid file upload',
            'details': str(e)
        }), 400
    except RequestEntityTooLarge:
        logger.warning("File upload too large")
        return jsonify({
            'error': 'File too large',
            'details': f'Maximum file size is {app.config["MAX_CONTENT_LENGTH"] // (1024*1024)}MB'
        }), 413
    except Exception as e:
        logger.error(f"Unexpected error analyzing email file: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'details': 'An unexpected error occurred while processing your file'
        }), 500

@app.route('/api/analysis/<task_id>', methods=['GET'])
def get_analysis_result(task_id):
    """Get the result of an analysis task"""
    try:
        # Validate task ID format
        if not task_id or len(task_id) < 10:
            return jsonify({
                'error': 'Invalid task ID',
                'details': 'Task ID format is invalid'
            }), 400
        
        logger.debug(f"Fetching result for task: {task_id}")
        task = celery.AsyncResult(task_id)
        
        # Handle different task states
        if task.state == 'PENDING':
            response = {
                'status': 'processing',
                'message': 'Task is waiting to be processed',
                'progress': 0
            }
        elif task.state == 'PROGRESS':
            response = {
                'status': 'processing',
                'message': 'Analysis in progress',
                'progress': task.info.get('progress', 50) if task.info else 50
            }
        elif task.state == 'SUCCESS':
            result = task.get()
            response = {
                'status': 'completed',
                'result': result,
                'message': 'Analysis completed successfully'
            }
            # Log successful analysis
            threat_score = result.get('threat_score', 0) if isinstance(result, dict) else 0
            logger.info(f"Analysis completed for task {task_id}: threat_score={threat_score}")
            
        elif task.state == 'FAILURE':
            error_info = str(task.result) if task.result else 'Unknown error occurred'
            response = {
                'status': 'failed',
                'error': error_info,
                'message': 'Analysis failed'
            }
            logger.warning(f"Task {task_id} failed: {error_info}")
            
        elif task.state == 'RETRY':
            response = {
                'status': 'processing',
                'message': 'Task is being retried due to temporary error',
                'progress': 25
            }
        else:
            response = {
                'status': task.state.lower(),
                'message': f'Task state: {task.state}',
                'progress': 10
            }
        
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Unexpected error fetching analysis result for task {task_id}: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'details': 'Unable to fetch analysis results'
        }), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    mode = os.environ.get('MODE', 'production')
    
    if mode == 'development':
        print("🚀 Starting Flask in DEVELOPMENT mode")
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        print("🚀 Starting Flask in PRODUCTION mode") 
        app.run(debug=False, host='0.0.0.0', port=port)