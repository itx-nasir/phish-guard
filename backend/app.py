from flask import Flask, request, jsonify
from flask_cors import CORS
from celery import Celery
from dotenv import load_dotenv
import os
import logging

from config import Config
from services.email_analyzer import EmailAnalyzer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Enable CORS
CORS(app, origins=app.config['CORS_ORIGINS'])

# Initialize Celery
celery = Celery(
    app.import_name,
    broker=app.config['CELERY_BROKER_URL'],
    backend=app.config['CELERY_RESULT_BACKEND']
)

# Celery tasks
@celery.task(bind=True)
def analyze_content_task(self, content):
    """Celery task for analyzing email content"""
    try:
        result = EmailAnalyzer.analyze_content(content)
        return result
    except Exception as e:
        logger.error(f"Error in analyze_content_task: {str(e)}")
        self.retry(countdown=60, max_retries=3)

@celery.task(bind=True)
def analyze_file_task(self, file_path):
    """Celery task for analyzing email file"""
    try:
        result = EmailAnalyzer.analyze_file(file_path)
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
        return result
    except Exception as e:
        logger.error(f"Error in analyze_file_task: {str(e)}")
        # Clean up on error too
        if os.path.exists(file_path):
            os.remove(file_path)
        self.retry(countdown=60, max_retries=3)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'version': '1.0.0'}), 200

@app.route('/api/analyze/content', methods=['POST'])
def analyze_email_content():
    """Analyze email content provided in the request body"""
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'No email content provided'}), 400

        email_content = data['content']
        if not email_content.strip():
            return jsonify({'error': 'Empty email content'}), 400

        # Create analysis task
        task = analyze_content_task.delay(email_content)
        
        return jsonify({
            'task_id': task.id,
            'status': 'processing',
            'message': 'Analysis started successfully'
        }), 202

    except Exception as e:
        logger.error(f"Error analyzing email content: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analyze/file', methods=['POST'])
def analyze_email_file():
    """Analyze uploaded email file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'error': 'No file selected'}), 400

        # Simple file validation
        if not file.filename.lower().endswith('.eml'):
            return jsonify({'error': 'Invalid file format. Please upload .eml files only'}), 400

        # Check file size
        if request.content_length > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413

        # Save file temporarily to shared volume
        import uuid
        
        filename = f"{uuid.uuid4()}.eml"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Create analysis task
        task = analyze_file_task.delay(file_path)

        return jsonify({
            'task_id': task.id,
            'status': 'processing',
            'message': 'File analysis started successfully'
        }), 202

    except Exception as e:
        logger.error(f"Error analyzing email file: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analysis/<task_id>', methods=['GET'])
def get_analysis_result(task_id):
    """Get the result of an analysis task"""
    try:
        task = celery.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'status': 'processing',
                'message': 'Task is waiting to be processed'
            }
        elif task.state == 'SUCCESS':
            response = {
                'status': 'completed',
                'result': task.get(),
                'message': 'Analysis completed successfully'
            }
        elif task.state == 'FAILURE':
            response = {
                'status': 'failed',
                'error': str(task.result),
                'message': 'Analysis failed'
            }
        else:
            response = {
                'status': task.state.lower(),
                'message': f'Task state: {task.state}'
            }
        
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error fetching analysis result: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

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
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=port)