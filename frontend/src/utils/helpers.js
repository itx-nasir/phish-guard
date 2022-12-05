import { 
  FILE_CONFIG, 
  CONTENT_CONFIG, 
  ERROR_MESSAGES, 
  RISK_LEVELS,
  VALIDATION_PATTERNS 
} from './constants';

/**
 * File validation utilities
 */
export const validateFile = (file) => {
  const errors = {};
  
  if (!file) {
    errors.file = 'No file provided';
    return errors;
  }
  
  // Check file extension
  const extension = `.${file.name.split('.').pop().toLowerCase()}`;
  if (!FILE_CONFIG.ALLOWED_EXTENSIONS.includes(extension)) {
    errors.extension = ERROR_MESSAGES.INVALID_FILE_TYPE;
  }
  
  // Check file size
  if (file.size > FILE_CONFIG.MAX_SIZE) {
    errors.size = ERROR_MESSAGES.FILE_TOO_LARGE;
  }
  
  if (file.size === 0) {
    errors.empty = 'File appears to be empty';
  }
  
  return errors;
};

/**
 * Content validation utilities
 */
export const validateEmailContent = (content) => {
  const errors = {};
  
  if (!content || !content.trim()) {
    errors.content = ERROR_MESSAGES.EMPTY_CONTENT;
    return errors;
  }
  
  if (content.length < CONTENT_CONFIG.MIN_LENGTH) {
    errors.content = ERROR_MESSAGES.CONTENT_TOO_SHORT;
  }
  
  if (content.length > CONTENT_CONFIG.MAX_LENGTH) {
    errors.content = ERROR_MESSAGES.CONTENT_TOO_LARGE;
  }
  
  // Basic email format validation
  if (!content.includes('@') && !content.toLowerCase().includes('from:')) {
    errors.format = 'This doesn\'t appear to be valid email content';
  }
  
  return errors;
};

/**
 * Task ID validation
 */
export const validateTaskId = (taskId) => {
  if (!taskId) return false;
  return VALIDATION_PATTERNS.TASK_ID.test(taskId);
};

/**
 * Format file size for display
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Format threat score for display
 */
export const formatThreatScore = (score) => {
  if (typeof score !== 'number') return '0.0%';
  return `${(score * 100).toFixed(1)}%`;
};

/**
 * Get risk level configuration based on score
 */
export const getRiskLevel = (score) => {
  if (typeof score !== 'number') return RISK_LEVELS.UNKNOWN;
  
  if (score >= RISK_LEVELS.HIGH.threshold) return RISK_LEVELS.HIGH;
  if (score >= RISK_LEVELS.MEDIUM.threshold) return RISK_LEVELS.MEDIUM;
  return RISK_LEVELS.LOW;
};

/**
 * Get risk color based on risk level
 */
export const getRiskColor = (riskLevel) => {
  const level = typeof riskLevel === 'string' 
    ? Object.values(RISK_LEVELS).find(r => r.value === riskLevel.toLowerCase())
    : riskLevel;
  
  return level?.color || RISK_LEVELS.UNKNOWN.color;
};

/**
 * Error handling utilities
 */
export const parseApiError = (error) => {
  if (!error) return ERROR_MESSAGES.UNKNOWN;
  
  // Network errors
  if (error.code === 'NETWORK_ERROR' || error.message?.includes('Network Error')) {
    return ERROR_MESSAGES.NETWORK_ERROR;
  }
  
  // Timeout errors
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    return ERROR_MESSAGES.TIMEOUT;
  }
  
  // HTTP errors
  if (error.response) {
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        return data?.details || data?.error || 'Invalid request';
      case 404:
        return ERROR_MESSAGES.ANALYSIS_NOT_FOUND;
      case 413:
        return ERROR_MESSAGES.FILE_TOO_LARGE;
      case 429:
        return 'Too many requests. Please try again later.';
      case 500:
      case 502:
      case 503:
      case 504:
        return ERROR_MESSAGES.SERVER_ERROR;
      default:
        return data?.details || data?.error || `HTTP ${status} error`;
    }
  }
  
  return error.message || ERROR_MESSAGES.UNKNOWN;
};

/**
 * Debounce function for performance optimization
 */
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * Throttle function for performance optimization
 */
export const throttle = (func, limit) => {
  let inThrottle;
  return function() {
    const args = arguments;
    const context = this;
    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

/**
 * Deep clone utility
 */
export const deepClone = (obj) => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime());
  if (obj instanceof Array) return obj.map(item => deepClone(item));
  if (typeof obj === 'object') {
    const cloned = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        cloned[key] = deepClone(obj[key]);
      }
    }
    return cloned;
  }
};

/**
 * Local storage utilities with error handling
 */
export const storage = {
  get: (key, defaultValue = null) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.warn('Failed to get item from localStorage:', error);
      return defaultValue;
    }
  },
  
  set: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.warn('Failed to set item in localStorage:', error);
      return false;
    }
  },
  
  remove: (key) => {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.warn('Failed to remove item from localStorage:', error);
      return false;
    }
  },
  
  clear: () => {
    try {
      localStorage.clear();
      return true;
    } catch (error) {
      console.warn('Failed to clear localStorage:', error);
      return false;
    }
  }
};

/**
 * URL utilities
 */
export const urlUtils = {
  isValidUrl: (string) => {
    try {
      new URL(string);
      return true;
    } catch (_) {
      return false;
    }
  },
  
  getDomain: (url) => {
    try {
      return new URL(url).hostname;
    } catch (_) {
      return '';
    }
  },
  
  addQueryParams: (url, params) => {
    const urlObj = new URL(url, window.location.origin);
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined) {
        urlObj.searchParams.set(key, params[key]);
      }
    });
    return urlObj.toString();
  }
};

/**
 * Date/Time utilities
 */
export const dateUtils = {
  formatRelative: (date) => {
    const now = new Date();
    const target = new Date(date);
    const diffMs = now - target;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
    
    return target.toLocaleDateString();
  },
  
  format: (date, options = {}) => {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      ...options
    });
  }
};

/**
 * Analytics utilities
 */
export const analytics = {
  track: (event, properties = {}) => {
    if (process.env.NODE_ENV === 'development') {
      console.log('Analytics Event:', event, properties);
    }
    // Add actual analytics integration here (Google Analytics, etc.)
  },
  
  page: (pageName) => {
    if (process.env.NODE_ENV === 'development') {
      console.log('Page View:', pageName);
    }
    // Add actual page tracking here
  }
};

/**
 * Export data utilities
 */
export const exportUtils = {
  downloadJSON: (data, filename = 'data.json') => {
    try {
      const dataStr = JSON.stringify(data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      return true;
    } catch (error) {
      console.error('Failed to download JSON:', error);
      return false;
    }
  },
  
  downloadCSV: (data, filename = 'data.csv') => {
    try {
      // Simple CSV conversion - can be enhanced
      const csv = Array.isArray(data) 
        ? data.map(row => Object.values(row).join(',')).join('\n')
        : Object.values(data).join(',');
      
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      return true;
    } catch (error) {
      console.error('Failed to download CSV:', error);
      return false;
    }
  }
};

// Default export with all utilities
export default {
  validateFile,
  validateEmailContent,
  validateTaskId,
  formatFileSize,
  formatThreatScore,
  getRiskLevel,
  getRiskColor,
  parseApiError,
  debounce,
  throttle,
  deepClone,
  storage,
  urlUtils,
  dateUtils,
  analytics,
  exportUtils,
}; 