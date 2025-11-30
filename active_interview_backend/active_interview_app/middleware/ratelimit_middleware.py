"""
Rate limiting middleware to handle 429 Too Many Requests responses.

This middleware ensures that when rate limits are exceeded, the response
includes appropriate headers and error messages, and logs violations
for monitoring and analysis.
"""

import time
import logging
from django.http import JsonResponse
from django.shortcuts import render
from django_ratelimit.exceptions import Ratelimited
from ..ratelimit_config import get_client_ip
from ..models import RateLimitViolation

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Middleware to handle rate limit exceeded exceptions.

    Catches Ratelimited exceptions, logs violations, and returns
    a properly formatted HTTP 429 response with Retry-After header.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def _log_violation(self, request, rate_limit_type='default', limit_value=60):
        """
        Log rate limit violation to database.

        Args:
            request: Django request object
            rate_limit_type: Type of rate limit (default/strict/lenient)
            limit_value: Limit value that was exceeded
        """
        try:
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

            violation = RateLimitViolation.objects.create(
                user=request.user if request.user.is_authenticated else None,
                ip_address=ip_address,
                endpoint=request.path,
                method=request.method,
                rate_limit_type=rate_limit_type,
                limit_value=limit_value,
                user_agent=user_agent
            )

            # Check if alert threshold exceeded
            self._check_and_send_alert()

            logger.warning(
                f"Rate limit violation: {violation} "
                f"(type={rate_limit_type}, limit={limit_value})"
            )

        except Exception as e:
            # Don't let logging errors affect the response
            logger.error(f"Error logging rate limit violation: {e}")

    def _check_and_send_alert(self):
        """
        Check if alert threshold is exceeded and send alert if needed.
        """
        from django.conf import settings

        # Get threshold from settings (default: 10 violations in 5 minutes)
        threshold = getattr(settings, 'RATELIMIT_ALERT_THRESHOLD', 10)
        window_minutes = getattr(settings, 'RATELIMIT_ALERT_WINDOW', 5)

        exceeded, count, violators = RateLimitViolation.check_threshold_exceeded(
            minutes=window_minutes,
            threshold=threshold
        )

        if exceeded:
            # Get recent violations that haven't triggered an alert
            recent_violations = RateLimitViolation.get_recent_violations(
                minutes=window_minutes
            ).filter(alert_sent=False)

            if recent_violations.exists():
                # Send alert
                self._send_threshold_alert(count, violators, window_minutes)

                # Mark violations as alerted
                recent_violations.update(alert_sent=True)

    def _send_threshold_alert(self, count, violators, window_minutes):
        """
        Send alert when rate limit violation threshold is exceeded.

        Args:
            count: Number of violations
            violators: List of violator identifiers
            window_minutes: Time window in minutes
        """
        from django.core.mail import mail_admins
        from django.conf import settings

        try:
            subject = f"⚠️ Rate Limit Alert: {count} violations in {window_minutes} minutes"

            message = f"""
Rate Limit Threshold Exceeded

Total Violations: {count}
Time Window: {window_minutes} minutes
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}

Top Violators:
{chr(10).join(f"- {v}" for v in violators[:10])}

Please review the rate limit violations in the admin dashboard:
{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/admin/active_interview_app/ratelimitviolation/

This is an automated alert from the rate limiting system.
            """

            mail_admins(
                subject=subject,
                message=message,
                fail_silently=True
            )

            logger.info(f"Rate limit alert sent: {count} violations")

        except Exception as e:
            logger.error(f"Error sending rate limit alert: {e}")

    def process_exception(self, request, exception):
        """
        Process Ratelimited exceptions and return 429 response.

        Args:
            request: Django request object
            exception: Exception that was raised

        Returns:
            JsonResponse or HttpResponse with 429 status code if rate limited,
            None otherwise to allow normal exception handling.
        """
        if isinstance(exception, Ratelimited):
            # Determine rate limit type and value from request
            # This is a best-effort extraction
            rate_limit_type = getattr(request, '_ratelimit_type', 'default')
            limit_value = getattr(request, '_ratelimit_value', 60)

            # Log the violation
            self._log_violation(request, rate_limit_type, limit_value)

            # Calculate retry-after value (default to 60 seconds)
            retry_after = 60

            # Check if this is an API request (JSON expected)
            is_api_request = (
                request.path.startswith('/api/') or
                request.META.get('HTTP_ACCEPT', '').startswith('application/json') or
                request.META.get('CONTENT_TYPE', '').startswith('application/json')
            )

            if is_api_request:
                # Return JSON response for API endpoints
                response = JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.',
                    'retry_after': retry_after
                }, status=429)
            else:
                # Return HTML response for web pages
                response = render(request, '429.html', {
                    'retry_after': retry_after
                }, status=429)

            # Add Retry-After header
            response['Retry-After'] = str(retry_after)

            # Add rate limit headers for debugging
            response['X-RateLimit-Limit'] = str(limit_value)
            response['X-RateLimit-Remaining'] = '0'
            response['X-RateLimit-Reset'] = str(int(time.time()) + retry_after)

            return response

        return None
