"""
Rate limiting decorators for views and API endpoints.

Provides convenient decorators to apply rate limits based on user type
and operation sensitivity.
"""

from functools import wraps
from django_ratelimit.decorators import ratelimit
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
        def wrapper(request, *args, **kwargs):
            # Set metadata for middleware logging BEFORE rate limit check
            request._ratelimit_type = 'default'
            request._ratelimit_value = 60 if request.user.is_authenticated else 30

            # Apply rate limiting decorator
            @ratelimit(
                group='default',
                key=ratelimit_key,
                rate=lambda group, request: get_rate_for_user('default', request),
                method=methods,
                block=True
            )
            def inner(req, *inner_args, **inner_kwargs):
                return func(req, *inner_args, **inner_kwargs)

            return inner(request, *args, **kwargs)
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
        def wrapper(request, *args, **kwargs):
            # Set metadata for middleware logging BEFORE rate limit check
            request._ratelimit_type = 'strict'
            request._ratelimit_value = 20 if request.user.is_authenticated else 10

            # Apply rate limiting decorator
            @ratelimit(
                group='strict',
                key=ratelimit_key,
                rate=lambda group, request: get_rate_for_user('strict', request),
                method=methods,
                block=True
            )
            def inner(req, *inner_args, **inner_kwargs):
                return func(req, *inner_args, **inner_kwargs)

            return inner(request, *args, **kwargs)
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
        def wrapper(request, *args, **kwargs):
            # Set metadata for middleware logging BEFORE rate limit check
            request._ratelimit_type = 'lenient'
            request._ratelimit_value = 120 if request.user.is_authenticated else 60

            # Apply rate limiting decorator
            @ratelimit(
                group='lenient',
                key=ratelimit_key,
                rate=lambda group, request: get_rate_for_user('lenient', request),
                method=methods,
                block=True
            )
            def inner(req, *inner_args, **inner_kwargs):
                return func(req, *inner_args, **inner_kwargs)

            return inner(request, *args, **kwargs)
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
        # Create a simple wrapper function for rate limiting
        def rate_func(g, r):
            # g is group (from ratelimit), r is request
            return get_rate_for_user(group, r)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Handle both class methods (self, request) and functions (request)
            # For class methods: args = (self, request, ...)
            # For functions: args = (request, ...)
            if len(args) >= 2 and hasattr(args[0], '__class__'):
                # Class method: self is args[0], request is args[1]
                request = args[1]

                # Apply rate limiting with a helper function
                @ratelimit(
                    key=ratelimit_key,
                    rate=rate_func,
                    method=ratelimit.ALL,
                    block=True
                )
                def check_limit(req):
                    pass

                check_limit(request)
                return func(*args, **kwargs)
            else:
                # Regular function: request is args[0]
                @ratelimit(
                    key=ratelimit_key,
                    rate=rate_func,
                    method=ratelimit.ALL,
                    block=True
                )
                def inner(*inner_args, **inner_kwargs):
                    return func(*inner_args, **inner_kwargs)

                return inner(*args, **kwargs)

        return wrapper
    return decorator
