from functools import wraps
from flask import request, jsonify, current_app
import redis
import time
from typing import Callable
import logging

logger = logging.getLogger(__name__)

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass

def rate_limit(f: Callable) -> Callable:
    """
    Decorator to implement rate limiting
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
        
    Raises:
        RateLimitExceeded: If rate limit is exceeded
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get client IP
            client_ip = request.remote_addr
            
            # Connect to Redis
            r = redis.from_url(current_app.config['RATELIMIT_STORAGE_URL'])
            
            # Get rate limit settings
            rate_limit = current_app.config['API_RATE_LIMIT']
            limit, period = _parse_rate_limit(rate_limit)
            
            # Generate Redis key
            key = f"rate_limit:{client_ip}:{f.__name__}"
            
            # Get current count
            current = r.get(key)
            
            if current is None:
                # First request, set initial count
                r.setex(key, period, 1)
            elif int(current) >= limit:
                # Rate limit exceeded
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': r.ttl(key)
                }), 429
            else:
                # Increment counter
                r.incr(key)
            
            return f(*args, **kwargs)
            
        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiter: {str(e)}")
            # Fall back to allowing the request if Redis is unavailable
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in rate limiter: {str(e)}")
            raise
    
    return decorated_function

def _parse_rate_limit(rate_limit: str) -> tuple:
    """
    Parse rate limit string (e.g., "100 per hour")
    
    Args:
        rate_limit: Rate limit string
        
    Returns:
        tuple: (limit, period in seconds)
    """
    try:
        count, _, period = rate_limit.split()
        count = int(count)
        
        # Convert period to seconds
        period_map = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400
        }
        
        period_seconds = period_map.get(period.lower(), 3600)  # Default to hour
        
        return count, period_seconds
        
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing rate limit: {str(e)}")
        # Return default values
        return 100, 3600  # 100 per hour