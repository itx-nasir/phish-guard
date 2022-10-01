import re
from email.parser import Parser
from email.policy import default
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)

def validate_email_content(content: str) -> bool:
    """
    Validate email content format
    
    Args:
        content: Raw email content
        
    Returns:
        bool: True if content is valid, False otherwise
    """
    try:
        # Try to parse the content as an email
        parser = Parser(policy=default)
        email_message = parser.parsestr(content)
        
        # Check required headers
        required_headers = {'From', 'To', 'Subject', 'Date'}
        missing_headers = required_headers - set(email_message.keys())
        
        if missing_headers:
            logger.warning(f"Missing required headers: {missing_headers}")
            return False
        
        # Validate From address
        from_address = email_message.get('From', '')
        if not _validate_email_address(from_address):
            logger.warning(f"Invalid From address: {from_address}")
            return False
        
        # Validate To address
        to_address = email_message.get('To', '')
        if not _validate_email_address(to_address):
            logger.warning(f"Invalid To address: {to_address}")
            return False
        
        # Check for message body
        if not _has_message_body(email_message):
            logger.warning("Email has no message body")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating email content: {str(e)}")
        return False

def _validate_email_address(address: str) -> bool:
    """
    Validate email address format
    
    Args:
        address: Email address string
        
    Returns:
        bool: True if address is valid, False otherwise
    """
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Extract email from "Display Name <email@domain.com>" format
    match = re.search(r'<(.+?)>', address)
    if match:
        address = match.group(1)
    
    return bool(re.match(pattern, address.strip()))

def _has_message_body(email_message) -> bool:
    """
    Check if email has a message body
    
    Args:
        email_message: Email message object
        
    Returns:
        bool: True if message has body, False otherwise
    """
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() in ["text/plain", "text/html"]:
                if part.get_payload(decode=True):
                    return True
    else:
        if email_message.get_payload(decode=True):
            return True
    
    return False

def validate_file_size(file_size: int, max_size: Optional[int] = None) -> bool:
    """
    Validate file size
    
    Args:
        file_size: Size of file in bytes
        max_size: Maximum allowed size in bytes
        
    Returns:
        bool: True if file size is valid, False otherwise
    """
    if max_size is None:
        from flask import current_app
        max_size = current_app.config['MAX_CONTENT_LENGTH']
    
    return file_size <= max_size

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove path components
    filename = re.sub(r'[/\\]', '', filename)
    
    # Remove non-ASCII characters
    filename = re.sub(r'[^\x00-\x7F]+', '', filename)
    
    # Remove special characters
    filename = re.sub(r'[<>:"|?*]', '', filename)
    
    return filename.strip()