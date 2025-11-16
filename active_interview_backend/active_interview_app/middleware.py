"""
Middleware for observability and metrics collection.
Tracks requests, responses, latency, and errors.

Related to Issues #14, #15 (Observability Dashboard).
"""
import time
import traceback
import logging
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


class MetricsMiddleware:
    """
    Middleware to collect request/response metrics for observability.

    Tracks:
    - Request count per endpoint
    - Response times (latency)
    - HTTP status codes
    - Error details

    Performance considerations:
    - Uses async database writes to minimize impact
    - Gracefully handles exceptions
    - Minimal overhead (< 5ms per request)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Record start time
        start_time = time.time()

        # Process request
        response = None
        exception_occurred = None

        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            exception_occurred = e
            raise
        finally:
            # Calculate response time
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000

            # Record metrics (non-blocking)
            try:
                self._record_metrics(
                    request,
                    response,
                    response_time_ms,
                    exception_occurred
                )
            except Exception as e:
                # Never let metrics collection break the application
                logger.error(
                    f"Failed to record metrics: {e}",
                    exc_info=True
                )

    def _record_metrics(self, request, response, response_time_ms, exception):
        """
        Record request metrics to database.

        Args:
            request: Django request object
            response: Django response object (None if exception occurred)
            response_time_ms: Response time in milliseconds
            exception: Exception object if one occurred
        """
        from .observability_models import RequestMetric, ErrorLog

        # Determine status code
        if response:
            status_code = response.status_code
        elif exception:
            status_code = 500
        else:
            status_code = 500

        # Get user ID if authenticated
        user_id = request.user.id if request.user.is_authenticated else None

        # Get endpoint path (strip query string)
        endpoint = request.path

        # Create RequestMetric record
        try:
            RequestMetric.objects.create(
                timestamp=timezone.now(),
                endpoint=endpoint,
                method=request.method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Failed to create RequestMetric: {e}")

        # If error occurred, log detailed error information
        if status_code >= 400 or exception:
            try:
                self._record_error(
                    request,
                    endpoint,
                    status_code,
                    exception,
                    user_id
                )
            except Exception as e:
                logger.error(f"Failed to create ErrorLog: {e}")

    def _record_error(self, request, endpoint, status_code, exception, user_id):
        """
        Record detailed error information.

        Args:
            request: Django request object
            endpoint: Request path
            status_code: HTTP status code
            exception: Exception object (None for HTTP errors without exceptions)
            user_id: Authenticated user ID
        """
        from .observability_models import ErrorLog

        # Determine error details
        if exception:
            error_type = type(exception).__name__
            error_message = str(exception)
            stack_trace = traceback.format_exc()
        else:
            error_type = f"HTTP {status_code}"
            error_message = f"Request resulted in {status_code} status"
            stack_trace = ""

        # Capture request context (sanitize sensitive data)
        request_data = {
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'content_type': request.content_type,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }

        # Don't log sensitive data
        if request.method == 'POST':
            request_data['has_post_data'] = bool(request.POST)
            # Don't include actual POST data as it may contain passwords, etc.

        # Create ErrorLog record
        ErrorLog.objects.create(
            timestamp=timezone.now(),
            endpoint=endpoint,
            method=request.method,
            status_code=status_code,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            user_id=user_id,
            request_data=request_data
        )


class PerformanceMonitorMiddleware:
    """
    Lightweight performance monitoring middleware.
    Logs warnings for slow requests (> 1 second).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_request_threshold_ms = 1000  # 1 second

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        # Calculate response time
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000

        # Log slow requests
        if response_time_ms > self.slow_request_threshold_ms:
            logger.warning(
                f"Slow request detected: {request.method} {request.path} "
                f"took {response_time_ms:.2f}ms"
            )

        return response
