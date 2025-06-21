// Application Constants
export const APP_CONFIG = {
  NAME: 'PhishGuard',
  VERSION: '1.0.0',
  DESCRIPTION: 'Email Phishing Detection System',
};

// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || '',
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
};

// API Endpoints
export const API_ENDPOINTS = {
  HEALTH: '/api/health',
  TEST: '/api/test',
  ANALYZE_CONTENT: '/api/analyze/content',
  ANALYZE_FILE: '/api/analyze/file',
  ANALYZE_BATCH: '/api/analyze/batch',
  ANALYSIS_RESULT: (taskId) => `/api/analysis/${taskId}`,
};

// File Upload Configuration
export const FILE_CONFIG = {
  MAX_SIZE: 16 * 1024 * 1024, // 16MB
  ALLOWED_EXTENSIONS: ['.eml'],
  MIME_TYPES: {
    'message/rfc822': ['.eml'],
  },
};

// Content Validation
export const CONTENT_CONFIG = {
  MIN_LENGTH: 50,
  MAX_LENGTH: 1024 * 1024, // 1MB
};

// UI Configuration
export const UI_CONFIG = {
  POLL_INTERVAL: 2000, // 2 seconds
  NOTIFICATION_DURATION: 5000, // 5 seconds
  DEBOUNCE_DELAY: 300, // 300ms
  SKELETON_ANIMATION_DURATION: 1.5, // seconds
};

// Risk Level Configuration
export const RISK_LEVELS = {
  LOW: {
    value: 'low',
    label: 'Low Risk',
    color: 'success',
    threshold: 0.0,
  },
  MEDIUM: {
    value: 'medium',
    label: 'Medium Risk',
    color: 'warning',
    threshold: 0.35,
  },
  HIGH: {
    value: 'high',
    label: 'High Risk',
    color: 'error',
    threshold: 0.7,
  },
  UNKNOWN: {
    value: 'unknown',
    label: 'Unknown',
    color: 'info',
    threshold: null,
  },
};

// Analysis Status
export const ANALYSIS_STATUS = {
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  PENDING: 'pending',
  RETRY: 'retry',
  PROGRESS: 'progress',
};

// Error Types
export const ERROR_TYPES = {
  NETWORK: 'NETWORK_ERROR',
  VALIDATION: 'VALIDATION_ERROR',
  SERVER: 'SERVER_ERROR',
  FILE: 'FILE_ERROR',
  TIMEOUT: 'TIMEOUT_ERROR',
  UNKNOWN: 'UNKNOWN_ERROR',
};

// Success Messages
export const SUCCESS_MESSAGES = {
  FILE_UPLOADED: 'File uploaded successfully',
  ANALYSIS_STARTED: 'Analysis started successfully',
  ANALYSIS_COMPLETED: 'Analysis completed successfully',
};

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network connection error. Please check your internet connection.',
  SERVER_ERROR: 'Server error occurred. Please try again later.',
  FILE_TOO_LARGE: `File size exceeds ${FILE_CONFIG.MAX_SIZE / (1024 * 1024)}MB limit`,
  INVALID_FILE_TYPE: `Only ${FILE_CONFIG.ALLOWED_EXTENSIONS.join(', ')} files are supported`,
  EMPTY_CONTENT: 'Email content cannot be empty',
  CONTENT_TOO_SHORT: `Email content must be at least ${CONTENT_CONFIG.MIN_LENGTH} characters`,
  CONTENT_TOO_LARGE: `Email content exceeds ${CONTENT_CONFIG.MAX_LENGTH / (1024 * 1024)}MB limit`,
  ANALYSIS_NOT_FOUND: 'Analysis not found. The task may have expired.',
  INVALID_TASK_ID: 'Invalid task ID provided',
  TIMEOUT: 'Request timed out. Please try again.',
  UNKNOWN: 'An unexpected error occurred',
};

// Theme Configuration
export const THEME_CONFIG = {
  BREAKPOINTS: {
    xs: 0,
    sm: 600,
    md: 900,
    lg: 1200,
    xl: 1536,
  },
  SPACING: 8,
  BORDER_RADIUS: 4,
  SHADOWS: {
    LIGHT: '0 2px 4px rgba(0,0,0,0.1)',
    MEDIUM: '0 4px 8px rgba(0,0,0,0.15)',
    HEAVY: '0 8px 16px rgba(0,0,0,0.2)',
  },
};

// Route Paths
export const ROUTES = {
  HOME: '/',
  DASHBOARD: '/',
  ANALYSIS: '/analysis/:taskId',
  ANALYSIS_RESULT: (taskId) => `/analysis/${taskId}`,
  NOT_FOUND: '*',
};

// Local Storage Keys
export const STORAGE_KEYS = {
  THEME_MODE: 'phishguard_theme_mode',
  USER_PREFERENCES: 'phishguard_user_preferences',
  RECENT_ANALYSES: 'phishguard_recent_analyses',
};

// Validation Patterns
export const VALIDATION_PATTERNS = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  URL: /^https?:\/\/.+/,
  TASK_ID: /^[a-f0-9-]{36}$/i,
};

// Analytics Events
export const ANALYTICS_EVENTS = {
  FILE_UPLOAD: 'file_upload',
  CONTENT_ANALYSIS: 'content_analysis',
  ANALYSIS_COMPLETED: 'analysis_completed',
  ERROR_OCCURRED: 'error_occurred',
  EXPORT_RESULTS: 'export_results',
};

// Feature Flags
export const FEATURE_FLAGS = {
  ENABLE_ANALYTICS: process.env.REACT_APP_ENABLE_ANALYTICS === 'true',
  ENABLE_DEBUG: process.env.NODE_ENV === 'development',
  ENABLE_SERVICE_WORKER: process.env.REACT_APP_ENABLE_SW === 'true',
  ENABLE_NOTIFICATIONS: process.env.REACT_APP_ENABLE_NOTIFICATIONS === 'true',
};

export default {
  APP_CONFIG,
  API_CONFIG,
  API_ENDPOINTS,
  FILE_CONFIG,
  CONTENT_CONFIG,
  UI_CONFIG,
  RISK_LEVELS,
  ANALYSIS_STATUS,
  ERROR_TYPES,
  SUCCESS_MESSAGES,
  ERROR_MESSAGES,
  THEME_CONFIG,
  ROUTES,
  STORAGE_KEYS,
  VALIDATION_PATTERNS,
  ANALYTICS_EVENTS,
  FEATURE_FLAGS,
}; 