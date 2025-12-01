"""
Tests for rate limit violation monitoring and admin dashboard.

Tests:
- RateLimitViolation model creation and queries
- Violation logging in middleware
- Alert threshold checking and email sending
- Admin dashboard views
- Export functionality
- Analytics views
"""

import json
from datetime import timedelta
from unittest.mock import patch, MagicMock, Mock

from django.test import TestCase, RequestFactory, Client, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.core import mail

from ..models import RateLimitViolation
from ..middleware.ratelimit_middleware import RateLimitMiddleware


class RateLimitViolationModelTest(TestCase):
    """Tests for RateLimitViolation model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_violation(self):
        """Test creating a rate limit violation record."""
        violation = RateLimitViolation.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            endpoint='/api/test/',
            method='POST',
            rate_limit_type='default',
            limit_value=60
        )

        self.assertEqual(violation.user, self.user)
        self.assertEqual(violation.ip_address, '192.168.1.1')
        self.assertEqual(violation.endpoint, '/api/test/')
        self.assertEqual(violation.method, 'POST')
        self.assertEqual(violation.rate_limit_type, 'default')
        self.assertEqual(violation.limit_value, 60)
        self.assertFalse(violation.alert_sent)

    def test_create_anonymous_violation(self):
        """Test creating violation for anonymous user."""
        violation = RateLimitViolation.objects.create(
            user=None,
            ip_address='10.0.0.1',
            endpoint='/api/public/',
            method='GET',
            rate_limit_type='lenient',
            limit_value=120
        )

        self.assertIsNone(violation.user)
        self.assertEqual(violation.ip_address, '10.0.0.1')

    def test_violation_str_representation(self):
        """Test string representation of violation."""
        violation = RateLimitViolation.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            endpoint='/api/test/',
            method='POST',
            rate_limit_type='default',
            limit_value=60
        )

        str_repr = str(violation)
        self.assertIn('testuser', str_repr)
        self.assertIn('/api/test/', str_repr)

    def test_get_top_violators_authenticated(self):
        """Test getting top violators for authenticated users."""
        # Create violations for multiple users
        user2 = User.objects.create_user(username='user2', password='pass')

        # User 1: 5 violations
        for _ in range(5):
            RateLimitViolation.objects.create(
                user=self.user,
                ip_address='192.168.1.1',
                endpoint='/api/test/',
                method='POST',
                rate_limit_type='default',
                limit_value=60
            )

        # User 2: 3 violations
        for _ in range(3):
            RateLimitViolation.objects.create(
                user=user2,
                ip_address='192.168.1.2',
                endpoint='/api/test/',
                method='POST',
                rate_limit_type='default',
                limit_value=60
            )

        top_violators = RateLimitViolation.get_top_violators(limit=10, days=7)

        self.assertEqual(len(top_violators), 2)
        # get_top_violators returns tuples: (identifier, count, type)
        self.assertEqual(top_violators[0][1], 5)  # count is at index 1
        self.assertIn('testuser', top_violators[0][0])  # identifier is at index 0

    def test_get_top_violators_anonymous(self):
        """Test getting top violators for anonymous users."""
        # Create violations for multiple IPs
        for _ in range(4):
            RateLimitViolation.objects.create(
                user=None,
                ip_address='10.0.0.1',
                endpoint='/api/test/',
                method='GET',
                rate_limit_type='default',
                limit_value=30
            )

        for _ in range(2):
            RateLimitViolation.objects.create(
                user=None,
                ip_address='10.0.0.2',
                endpoint='/api/test/',
                method='GET',
                rate_limit_type='default',
                limit_value=30
            )

        top_violators = RateLimitViolation.get_top_violators(limit=10, days=7)

        self.assertEqual(len(top_violators), 2)
        # get_top_violators returns tuples: (identifier, count, type)
        self.assertEqual(top_violators[0][1], 4)  # count is at index 1
        self.assertIn('10.0.0.1', top_violators[0][0])  # identifier is at index 0

    def test_check_threshold_not_exceeded(self):
        """Test threshold checking when not exceeded."""
        # Create 5 violations (threshold is 10)
        for _ in range(5):
            RateLimitViolation.objects.create(
                user=self.user,
                ip_address='192.168.1.1',
                endpoint='/api/test/',
                method='POST',
                rate_limit_type='default',
                limit_value=60
            )

        exceeded, count, violators = RateLimitViolation.check_threshold_exceeded(
            minutes=5,
            threshold=10
        )

        self.assertFalse(exceeded)
        self.assertEqual(count, 5)

    def test_check_threshold_exceeded(self):
        """Test threshold checking when exceeded."""
        # Create 15 violations (threshold is 10)
        for _ in range(15):
            RateLimitViolation.objects.create(
                user=self.user,
                ip_address='192.168.1.1',
                endpoint='/api/test/',
                method='POST',
                rate_limit_type='default',
                limit_value=60
            )

        exceeded, count, violators = RateLimitViolation.check_threshold_exceeded(
            minutes=5,
            threshold=10
        )

        self.assertTrue(exceeded)
        self.assertEqual(count, 15)
        self.assertGreater(len(violators), 0)

    def test_get_recent_violations(self):
        """Test getting recent violations."""
        # Create violations at different times
        now = timezone.now()

        # Recent violation
        RateLimitViolation.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            endpoint='/api/test/',
            method='POST',
            rate_limit_type='default',
            limit_value=60
        )

        # Old violation (will be excluded)
        old_violation = RateLimitViolation.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            endpoint='/api/test/',
            method='POST',
            rate_limit_type='default',
            limit_value=60
        )
        old_violation.timestamp = now - timedelta(hours=2)
        old_violation.save()

        recent = RateLimitViolation.get_recent_violations(minutes=60)
        self.assertEqual(recent.count(), 1)

    def test_violation_with_country_code(self):
        """Test creating violation with country code."""
        violation = RateLimitViolation.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            endpoint='/api/test/',
            method='POST',
            rate_limit_type='default',
            limit_value=60,
            country_code='US'
        )

        self.assertEqual(violation.country_code, 'US')

    def test_violation_with_long_user_agent(self):
        """Test creating violation with very long user agent."""
        long_user_agent = 'A' * 600
        violation = RateLimitViolation.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            endpoint='/api/test/',
            method='POST',
            rate_limit_type='default',
            limit_value=60,
            user_agent=long_user_agent
        )

        # Should store the full user agent
        self.assertEqual(len(violation.user_agent), 600)


class RateLimitMiddlewareTest(TestCase):
    """Tests for RateLimitMiddleware logging functionality."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.middleware = RateLimitMiddleware(get_response=lambda r: None)

    def test_log_violation_authenticated_user(self):
        """Test logging violation for authenticated user."""
        request = self.factory.post('/api/test/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'TestAgent/1.0'

        self.middleware._log_violation(
            request,
            rate_limit_type='strict',
            limit_value=20
        )

        violations = RateLimitViolation.objects.all()
        self.assertEqual(violations.count(), 1)

        violation = violations.first()
        self.assertEqual(violation.user, self.user)
        self.assertEqual(violation.ip_address, '192.168.1.1')
        self.assertEqual(violation.endpoint, '/api/test/')
        self.assertEqual(violation.rate_limit_type, 'strict')

    def test_log_violation_anonymous_user(self):
        """Test logging violation for anonymous user."""
        request = self.factory.get('/api/public/')
        request.user = MagicMock(is_authenticated=False)
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'curl/7.68.0'

        self.middleware._log_violation(
            request,
            rate_limit_type='default',
            limit_value=30
        )

        violations = RateLimitViolation.objects.all()
        self.assertEqual(violations.count(), 1)

        violation = violations.first()
        self.assertIsNone(violation.user)
        self.assertEqual(violation.ip_address, '10.0.0.1')

    @patch('django.core.mail.mail_admins')
    def test_send_threshold_alert(self, mock_mail_admins):
        """Test sending alert when threshold exceeded."""
        # Create violations to exceed threshold
        for _ in range(12):
            RateLimitViolation.objects.create(
                user=self.user,
                ip_address='192.168.1.1',
                endpoint='/api/test/',
                method='POST',
                rate_limit_type='default',
                limit_value=60,
                alert_sent=False
            )

        self.middleware._send_threshold_alert(
            count=12,
            violators=['testuser (User ID: 1)'],
            window_minutes=5
        )

        # Verify email was sent
        mock_mail_admins.assert_called_once()
        call_args = mock_mail_admins.call_args
        subject = call_args[1]['subject']
        self.assertIn('12 violations', subject)

    def test_log_violation_handles_missing_user_agent(self):
        """Test logging violation when user agent is missing."""
        request = self.factory.post('/api/test/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        # No HTTP_USER_AGENT

        self.middleware._log_violation(request)

        violation = RateLimitViolation.objects.first()
        self.assertIsNotNone(violation)
        self.assertEqual(violation.user_agent, '')

    def test_log_violation_error_handling(self):
        """Test logging violation handles errors gracefully."""
        request = self.factory.post('/api/test/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        # Mock a database error
        with patch('active_interview_app.models.RateLimitViolation.objects.create') as mock_create:
            mock_create.side_effect = Exception('Database error')

            # Should not raise exception
            try:
                self.middleware._log_violation(request)
            except Exception:
                self.fail('_log_violation should handle exceptions gracefully')

    def test_check_and_send_alert_no_violations(self):
        """Test check_and_send_alert when no violations exist."""
        # Should not raise exception
        try:
            self.middleware._check_and_send_alert()
        except Exception:
            self.fail('_check_and_send_alert should handle no violations gracefully')

    def test_process_exception_non_ratelimited(self):
        """Test process_exception with non-Ratelimited exception."""
        request = self.factory.get('/')
        request.user = self.user

        exception = ValueError('Not a rate limit exception')
        result = self.middleware.process_exception(request, exception)

        # Should return None for non-Ratelimited exceptions
        self.assertIsNone(result)

    def test_process_exception_ratelimited_api(self):
        """Test process_exception returns JSON for API requests."""
        from django_ratelimit.exceptions import Ratelimited

        request = self.factory.post('/api/test/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'TestAgent/1.0'

        exception = Ratelimited()
        response = self.middleware.process_exception(request, exception)

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_process_exception_ratelimited_web(self):
        """Test process_exception returns HTML for web requests."""
        from django_ratelimit.exceptions import Ratelimited

        request = self.factory.get('/test/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'

        exception = Ratelimited()
        response = self.middleware.process_exception(request, exception)

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response)

    def test_process_exception_creates_violation_log(self):
        """Test process_exception logs the violation."""
        from django_ratelimit.exceptions import Ratelimited

        request = self.factory.post('/api/test/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'TestAgent/1.0'

        exception = Ratelimited()
        self.middleware.process_exception(request, exception)

        # Should have created a violation log
        self.assertTrue(RateLimitViolation.objects.exists())


@override_settings(ROOT_URLCONF='active_interview_app.urls', TESTING=True)
class RateLimitDashboardViewTest(TestCase):
    """Tests for rate limit dashboard view."""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            password='pass123'
        )

    def test_dashboard_requires_staff(self):
        """Test dashboard requires staff permissions."""
        response = self.client.get(reverse('ratelimit_dashboard'))

        # Should redirect to login or return 403/302
        self.assertIn(response.status_code, [302, 403])

    def test_dashboard_accessible_by_staff(self):
        """Test dashboard is accessible by staff users."""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ratelimit_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('stats', response.context)
        self.assertIn('recent_violations', response.context)

    def test_dashboard_displays_statistics(self):
        """Test dashboard displays violation statistics."""
        # Create some violations
        for _ in range(5):
            RateLimitViolation.objects.create(
                user=self.regular_user,
                ip_address='192.168.1.1',
                endpoint='/api/test/',
                method='POST',
                rate_limit_type='default',
                limit_value=60
            )

        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('ratelimit_dashboard'))

        self.assertEqual(response.status_code, 200)
        stats = response.context['stats']
        self.assertGreater(stats['total'], 0)


@override_settings(ROOT_URLCONF='active_interview_app.urls', TESTING=True)
class ExportViolationsViewTest(TestCase):
    """Tests for violation export functionality."""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )

    def test_export_requires_staff(self):
        """Test export requires staff permissions."""
        response = self.client.get(reverse('export_violations'))
        self.assertIn(response.status_code, [302, 403])

    def test_export_csv_format(self):
        """Test CSV export has correct format."""
        # Create violation
        RateLimitViolation.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            endpoint='/api/test/',
            method='POST',
            rate_limit_type='default',
            limit_value=60
        )

        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('export_violations'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])

        # Check CSV content
        content = response.content.decode('utf-8')
        self.assertIn('Timestamp', content)
        self.assertIn('Username', content)
        self.assertIn('testuser', content)

    def test_export_with_filters(self):
        """Test CSV export with query filters."""
        # Create violations
        RateLimitViolation.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            endpoint='/api/test/',
            method='POST',
            rate_limit_type='default',
            limit_value=60
        )

        RateLimitViolation.objects.create(
            user=None,
            ip_address='10.0.0.1',
            endpoint='/api/other/',
            method='GET',
            rate_limit_type='lenient',
            limit_value=120
        )

        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('export_violations'),
            {'user_id': self.user.id}
        )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('testuser', content)
        # Should not include the anonymous violation
        self.assertNotIn('10.0.0.1', content)


@override_settings(ROOT_URLCONF='active_interview_app.urls', TESTING=True)
class ViolationDetailViewTest(TestCase):
    """Tests for violation detail view."""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )

    def test_detail_view_requires_staff(self):
        """Test detail view requires staff permissions."""
        violation = RateLimitViolation.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            endpoint='/api/test/',
            method='POST',
            rate_limit_type='default',
            limit_value=60
        )

        response = self.client.get(
            reverse('violation_detail', args=[violation.id])
        )
        self.assertIn(response.status_code, [302, 403])

    def test_detail_view_shows_violation(self):
        """Test detail view displays violation information."""
        violation = RateLimitViolation.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            endpoint='/api/test/',
            method='POST',
            rate_limit_type='default',
            limit_value=60,
            user_agent='TestAgent/1.0'
        )

        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('violation_detail', args=[violation.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['violation'], violation)
        self.assertIn('related_violations', response.context)


@override_settings(ROOT_URLCONF='active_interview_app.urls', TESTING=True)
class ViolationAnalyticsViewTest(TestCase):
    """Tests for violation analytics view."""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )

    def test_analytics_requires_admin(self):
        """Test analytics requires admin permissions."""
        response = self.client.get(reverse('violation_analytics'))
        self.assertIn(response.status_code, [302, 403])

    def test_analytics_displays_data(self):
        """Test analytics view displays analytics data."""
        # Create violations at different hours
        for hour in range(3):
            violation = RateLimitViolation.objects.create(
                user=None,
                ip_address='192.168.1.1',
                endpoint='/api/test/',
                method='POST',
                rate_limit_type='default',
                limit_value=60
            )
            # Set different hours
            violation.timestamp = violation.timestamp.replace(hour=hour)
            violation.save()

        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('violation_analytics'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('hourly_dist', response.context)
        self.assertIn('daily_dist', response.context)
        self.assertEqual(len(response.context['hourly_dist']), 24)

    def test_analytics_with_time_range(self):
        """Test analytics with different time ranges."""
        self.client.login(username='admin', password='admin123')

        for days in [1, 7, 30]:
            response = self.client.get(
                reverse('violation_analytics'),
                {'days': days}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['days'], days)
