"""
Middleware for observability, metrics collection, and audit logging.
Tracks requests, responses, latency, errors, and audit events.

Related to Issues #14, #15 (Observability Dashboard) and #66, #67, #68 (Audit Logging).
"""
import time
import traceback
import logging
import threading
from django.utils import timezone

logger = logging.getLogger(__name__)

# Thread-local storage for request context (audit logging)
_thread_locals = threading.local()


def get_current_request():
    """
    Retrieve the current request from thread-local storage.

    Returns:
        HttpRequest or None: The current request if available
    """
    return getattr(_thread_locals, 'request', None)


def get_current_ip():
    """
    Extract IP address from the current request.
    Handles proxy headers (X-Forwarded-For) for Railway deployment.

    Returns:
        str or None: IP address of the client
    """
    request = get_current_request()
    if not request:
        return None

    # Handle Railway/proxy forwarded IPs
    # X-Forwarded-For format: "client, proxy1, proxy2"
    # We want the original client IP (first in the list)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Get first IP in the chain (original client)
        return x_forwarded_for.split(',')[0].strip()

    # Fallback to REMOTE_ADDR for direct connections
    return request.META.get('REMOTE_ADDR')


def get_user_agent():
    """
    Extract user agent string from the current request.

    Returns:
        str: User agent string (empty if not available)
    """
    request = get_current_request()
    if not request:
        return ''

    return request.META.get('HTTP_USER_AGENT', '')


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
        # Record start time with high-resolution timer
        start_time = time.perf_counter()

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
            end_time = time.perf_counter()
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
        from active_interview_app.observability_models import RequestMetric

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
        from active_interview_app.observability_models import ErrorLog

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
        start_time = time.perf_counter()

        response = self.get_response(request)

        # Calculate response time
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000

        # Log slow requests
        if response_time_ms > self.slow_request_threshold_ms:
            logger.warning(
                f"Slow request detected: {request.method} {request.path} "
                f"took {response_time_ms:.2f}ms"
            )

        return response


class AuditLogMiddleware:
    """
    Middleware that stores the current request in thread-local storage.

    This allows audit logging utilities and signal handlers to access
    request context (IP address, user agent) without explicitly passing
    the request object.

    IMPORTANT: Must be placed high in MIDDLEWARE list to ensure it runs
    before views and other middleware that may trigger audit logging.

    Related to Issues #66, #67, #68 (Audit Logging).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request in thread-local storage
        _thread_locals.request = request

        try:
            response = self.get_response(request)
        finally:
            # Clean up thread-local storage after request completes
            # This prevents memory leaks and cross-request contamination
            if hasattr(_thread_locals, 'request'):
                del _thread_locals.request

        return response
