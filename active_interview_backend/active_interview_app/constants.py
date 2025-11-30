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
