"""
Rate limiting mixins for Django REST Framework ViewSets.

Provides mixins to apply rate limits to ViewSet actions based on the
operation type (read vs write).
"""

from django_ratelimit.decorators import ratelimit
from ..ratelimit_config import get_rate_for_user, ratelimit_key


class RateLimitMixin:
    """
    Mixin to apply rate limiting to ViewSet actions.

    Automatically applies different rate limits to read vs. write operations:
    - List/Retrieve: Lenient rate limits (120/60 per minute)
    - Create/Update/Destroy: Strict rate limits (20/10 per minute)
    - Custom actions: Default rate limits (60/30 per minute)
    """

    def get_throttles(self):
        """Override to use rate limiting instead of DRF throttles."""
        return []

    def initial(self, request, *args, **kwargs):
        """Apply rate limiting before processing the request."""
        # Determine rate limit group based on action
        action = getattr(self, 'action', None)

        if action in ['list', 'retrieve']:
            group = 'lenient'
        elif action in ['create', 'update', 'partial_update', 'destroy']:
            group = 'strict'
        else:
            group = 'default'

        # Apply rate limit using decorator BEFORE calling parent initial
        rate = get_rate_for_user(group, request)

        @ratelimit(
            key=ratelimit_key,
            rate=lambda g, r: rate,
            method=ratelimit.ALL,
            block=True
        )
        def check_rate_limit(req):
            pass  # Just check the rate limit

        check_rate_limit(request)

        # Call parent initial after rate limiting
        super().initial(request, *args, **kwargs)


class StrictRateLimitMixin:
    """
    Mixin to apply strict rate limiting to all ViewSet actions.

    Use this for resource-intensive operations that should be
    heavily rate-limited regardless of the action type.
    """

    def get_throttles(self):
        """Override to use rate limiting instead of DRF throttles."""
        return []

    def initial(self, request, *args, **kwargs):
        """Apply strict rate limiting before processing the request."""
        # Apply rate limiting BEFORE calling parent initial
        rate = get_rate_for_user('strict', request)

        @ratelimit(
            key=ratelimit_key,
            rate=lambda g, r: rate,
            method=ratelimit.ALL,
            block=True
        )
        def check_rate_limit(req):
            pass  # Just check the rate limit

        check_rate_limit(request)

        # Call parent initial after rate limiting
        super().initial(request, *args, **kwargs)


class LenientRateLimitMixin:
    """
    Mixin to apply lenient rate limiting to all ViewSet actions.

    Use this for read-only or low-cost operations that can
    handle higher request volumes.
    """

    def get_throttles(self):
        """Override to use rate limiting instead of DRF throttles."""
        return []

    def initial(self, request, *args, **kwargs):
        """Apply lenient rate limiting before processing the request."""
        # Apply rate limiting BEFORE calling parent initial
        rate = get_rate_for_user('lenient', request)

        @ratelimit(
            key=ratelimit_key,
            rate=lambda g, r: rate,
            method=ratelimit.ALL,
            block=True
        )
        def check_rate_limit(req):
            pass  # Just check the rate limit

        check_rate_limit(request)

        # Call parent initial after rate limiting
        super().initial(request, *args, **kwargs)
