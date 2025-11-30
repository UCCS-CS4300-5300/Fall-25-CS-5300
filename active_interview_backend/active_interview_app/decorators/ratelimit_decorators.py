"""
Rate limiting decorators for views and API endpoints.

Provides convenient decorators to apply rate limits based on user type
and operation sensitivity.
"""

from functools import wraps
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from ..ratelimit_config import (
    get_rate_for_user,
    ratelimit_key
)


def ratelimit_default(methods=None):
    """
    Apply default rate limiting (60/min authenticated, 30/min anonymous).

    Args:
        methods: HTTP methods to rate limit (default: ['GET', 'POST'])

    Returns:
        Decorator function
    """
    if methods is None:
        methods = ['GET', 'POST']

    def decorator(func):
        @wraps(func)
        @ratelimit(
            key=ratelimit_key,
            rate=lambda group, request: get_rate_for_user('default', request),
            method=methods,
            block=True
        )
        def wrapper(request, *args, **kwargs):
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def ratelimit_strict(methods=None):
    """
    Apply strict rate limiting for resource-intensive operations
    (20/min authenticated, 10/min anonymous).

    Args:
        methods: HTTP methods to rate limit (default: ['POST', 'PUT', 'DELETE'])

    Returns:
        Decorator function
    """
    if methods is None:
        methods = ['POST', 'PUT', 'DELETE']

    def decorator(func):
        @wraps(func)
        @ratelimit(
            key=ratelimit_key,
            rate=lambda group, request: get_rate_for_user('strict', request),
            method=methods,
            block=True
        )
        def wrapper(request, *args, **kwargs):
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def ratelimit_lenient(methods=None):
    """
    Apply lenient rate limiting for read-only operations
    (120/min authenticated, 60/min anonymous).

    Args:
        methods: HTTP methods to rate limit (default: ['GET'])

    Returns:
        Decorator function
    """
    if methods is None:
        methods = ['GET']

    def decorator(func):
        @wraps(func)
        @ratelimit(
            key=ratelimit_key,
            rate=lambda group, request: get_rate_for_user('lenient', request),
            method=methods,
            block=True
        )
        def wrapper(request, *args, **kwargs):
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def ratelimit_api(group='default'):
    """
    Apply rate limiting to class-based API views.

    This decorator can be used on individual methods of APIView classes.

    Args:
        group: Rate limit group ('default', 'strict', or 'lenient')

    Returns:
        Decorator function

    Example:
        class MyAPIView(APIView):
            @ratelimit_api('strict')
            def post(self, request):
                ...
    """
    def decorator(func):
        @wraps(func)
        @ratelimit(
            key=ratelimit_key,
            rate=lambda g, request: get_rate_for_user(group, request),
            method=ratelimit.ALL,
            block=True
        )
        def wrapper(self, request, *args, **kwargs):
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator
