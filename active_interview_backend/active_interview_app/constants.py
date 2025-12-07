"""
Configuration constants for the Active Interview application.
Centralizes hardcoded values for better maintainability.
"""

# Data Export Configuration
# Number of days before export download link expires
EXPORT_EXPIRATION_DAYS = 7
EXPORT_FILE_PREFIX = 'user_data'  # Prefix for exported ZIP filenames

# Email Configuration
# Don't raise exceptions on email failures in development
EMAIL_FAIL_SILENTLY = True

# File Size Units
FILE_SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB']
FILE_SIZE_THRESHOLD = 1024.0  # Threshold for converting between units

# Cache Configuration
CACHE_MAX_ENTRIES = 10000  # Maximum number of entries in cache
CACHE_DEFAULT_TIMEOUT = 300  # Default cache timeout in seconds (5 minutes)
BIAS_TERMS_CACHE_TIMEOUT = 3600  # Bias terms cache timeout (1 hour)

# Error Messages
ERROR_AI_DISABLED = "AI features are disabled on this server."
ERROR_KEY_QUESTIONS_FAILED = "Failed to generate key questions. Please try again."
ERROR_RESUME_UPLOAD_FAILED = "Failed to upload resume. Please try again."

# Success Messages
SUCCESS_ACCOUNT_CREATED = "Account was created for {username}"
SUCCESS_RESUME_UPLOADED = "Resume uploaded and parsed successfully!"
SUCCESS_FEEDBACK_SAVED = "Feedback submitted successfully!"

# Bias Detection Messages
ERROR_BIAS_BLOCKING = (
    "Your feedback contains language that may indicate bias. "
    "Please review the highlighted terms and revise your feedback."
)
WARNING_BIAS_DETECTED = (
    "Your feedback may contain biased language. "
    "Please review the suggestions below."
)
INFO_BIAS_ACKNOWLEDGED = (
    "You have acknowledged the potential bias warnings. "
    "Please ensure your feedback is fair and objective."
)

# Rate Limiting
RATELIMIT_DEFAULT_RATE = "60/m"  # 60 requests per minute
RATELIMIT_STRICT_RATE = "20/m"   # 20 requests per minute for write operations
RATELIMIT_LENIENT_RATE = "120/m"  # 120 requests per minute for read operations
