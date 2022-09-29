import os
import uuid
from werkzeug.utils import secure_filename
from typing import Optional
from flask import current_app
import magic
import logging
import time

logger = logging.getLogger(__name__)

class FileHandler:
    """Service for handling file uploads"""

    def __init__(self):
        self.upload_folder = current_app.config['UPLOAD_FOLDER']
        self.allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
        self.mime = magic.Magic(mime=True)

    def save_file(self, file) -> str:
        """
        Save uploaded file to a secure location
        
        Args:
            file: FileStorage object from Flask request
            
        Returns:
            str: Path to saved file
            
        Raises:
            ValueError: If file is invalid or unsafe
        """
        try:
            if not self.is_valid_email_file(file):
                raise ValueError("Invalid or unsafe file")

            # Generate secure filename
            original_filename = secure_filename(file.filename)
            extension = original_filename.rsplit('.', 1)[1].lower()
            filename = f"{str(uuid.uuid4())}.{extension}"
            
            # Create full path
            file_path = os.path.join(self.upload_folder, filename)
            
            # Save file
            file.save(file_path)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise

    def is_valid_email_file(self, file) -> bool:
        """
        Check if file is a valid email file
        
        Args:
            file: FileStorage object from Flask request
            
        Returns:
            bool: True if file is valid, False otherwise
        """
        if not file or not file.filename:
            return False
            
        # Check file extension
        if not self._allowed_file(file.filename):
            return False
            
        # Check MIME type
        try:
            # Read a small portion of the file to check MIME type
            file_content = file.read(2048)
            file.seek(0)  # Reset file pointer
            
            mime_type = self.mime.from_buffer(file_content)
            
            # Allowed MIME types for email files
            allowed_mime_types = {
                'message/rfc822',
                'text/plain',
                'application/octet-stream'  # Some .eml files might have this type
            }
            
            return mime_type in allowed_mime_types
            
        except Exception as e:
            logger.error(f"Error checking file MIME type: {str(e)}")
            return False

    def _allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Clean up old uploaded files
        
        Args:
            max_age_hours (int): Maximum age of files in hours
        """
        try:
            current_time = time.time()
            
            for filename in os.listdir(self.upload_folder):
                file_path = os.path.join(self.upload_folder, filename)
                
                # Skip if not a file
                if not os.path.isfile(file_path):
                    continue
                    
                # Remove if older than max age
                file_age = current_time - os.path.getctime(file_path)
                if file_age > (max_age_hours * 3600):
                    os.remove(file_path)
                    
        except Exception as e:
            logger.error(f"Error cleaning up old files: {str(e)}")
            raise