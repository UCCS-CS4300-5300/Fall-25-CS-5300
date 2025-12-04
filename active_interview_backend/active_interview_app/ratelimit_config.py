"""
Rate limiting configuration for API endpoints.

This module defines rate limits for different types of users and endpoints
to prevent abuse and excessive usage.
"""

# Rate limit configurations
# Format: "number/period" where period can be: s, m, h, d (seconds, minutes, hours, days)

# Default rate limits
DEFAULT_AUTHENTICATED_RATE = '60/m'  # 60 requests per minute for authenticated users
DEFAULT_ANONYMOUS_RATE = '30/m'      # 30 requests per minute for anonymous users

# Strict rate limits for resource-intensive operations
STRICT_AUTHENTICATED_RATE = '20/m'   # 20 requests per minute for authenticated users
STRICT_ANONYMOUS_RATE = '10/m'       # 10 requests per minute for anonymous users

# Lenient rate limits for read-only operations
LENIENT_AUTHENTICATED_RATE = '120/m'  # 120 requests per minute for authenticated users
LENIENT_ANONYMOUS_RATE = '60/m'       # 60 requests per minute for anonymous users


def get_rate_for_user(group, request):
    """
    Return the appropriate rate limit based on user authentication status.

    Args:
        group (str): The rate limit group ('default', 'strict', or 'lenient')
        request: Django request object

    Returns:
        str: Rate limit string (e.g., '60/m')
    """
    if request.user.is_authenticated:
        if group == 'strict':
            return STRICT_AUTHENTICATED_RATE
        elif group == 'lenient':
            return LENIENT_AUTHENTICATED_RATE
        else:
            return DEFAULT_AUTHENTICATED_RATE
    else:
        if group == 'strict':
            return STRICT_ANONYMOUS_RATE
        elif group == 'lenient':
            return LENIENT_ANONYMOUS_RATE
        else:
            return DEFAULT_ANONYMOUS_RATE


def get_client_ip(request):
    """
    Get the client's IP address from the request, accounting for proxies.

    Args:
        request: Django request object

    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def ratelimit_key(group, request):
    """
    Generate a rate limit key based on user or IP address.

    For authenticated users, use their user ID.
    For anonymous users, use their IP address.

    Args:
        group: Rate limit group (unused but required by django-ratelimit)
        request: Django request object

    Returns:
        str: Unique key for rate limiting
    """
    if request.user.is_authenticated:
        return f'user:{request.user.id}'
    else:
        return f'ip:{get_client_ip(request)}'
