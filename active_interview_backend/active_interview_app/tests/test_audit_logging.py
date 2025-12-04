"""
Test suite for audit logging functionality.

Tests cover:
- AuditLog model (immutability, field validation)
- Middleware (request context capture, IP extraction)
- Authentication events (login, logout, failed login)
- Admin action logging (create, update, delete)

Related to Issues #66, #67, #68 (Audit Logging).
"""

from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from active_interview_app.models import AuditLog
from active_interview_app.middleware import (
    get_current_request,
    get_current_ip,
    get_user_agent,
    AuditLogMiddleware,
    _thread_locals
)
from active_interview_app.audit_utils import create_audit_log
import threading


class AuditLogModelTests(TestCase):
    """Test the AuditLog model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_audit_log(self):
        """Test creating an audit log entry."""
        log = AuditLog.objects.create(
            user=self.user,
            action_type='LOGIN',
            description='User logged in',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0'
        )

        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_type, 'LOGIN')
        self.assertEqual(log.description, 'User logged in')
        self.assertEqual(log.ip_address, '192.168.1.1')
        self.assertIsNotNone(log.timestamp)

    def test_audit_log_immutability(self):
        """Test that audit logs cannot be updated after creation."""
        log = AuditLog.objects.create(
            user=self.user,
            action_type='LOGIN',
            description='Original description',
            ip_address='192.168.1.1'
        )

        # Try to update - should raise ValueError
        with self.assertRaises(ValueError) as context:
            log.description = 'Modified description'
            log.save()

        self.assertIn('immutable', str(context.exception).lower())

    def test_audit_log_cannot_be_deleted(self):
        """Test that audit logs cannot be deleted."""
        log = AuditLog.objects.create(
            user=self.user,
            action_type='LOGIN',
            description='Test log',
            ip_address='192.168.1.1'
        )

        # Try to delete - should raise ValueError
        with self.assertRaises(ValueError) as context:
            log.delete()

        self.assertIn('cannot be deleted', str(context.exception).lower())

    def test_audit_log_anonymous_user(self):
        """Test creating audit log for anonymous user (failed login)."""
        log = AuditLog.objects.create(
            user=None,
            action_type='LOGIN_FAILED',
            description='Failed login attempt',
            ip_address='192.168.1.1',
            extra_data={'attempted_username': 'hacker'}
        )

        self.assertIsNone(log.user)
        self.assertEqual(log.action_type, 'LOGIN_FAILED')
        self.assertEqual(log.extra_data['attempted_username'], 'hacker')

    def test_audit_log_extra_data(self):
        """Test storing extra_data in JSONField."""
        log = AuditLog.objects.create(
            user=self.user,
            action_type='ADMIN_UPDATE',
            description='Admin updated user',
            resource_type='User',
            resource_id='123',
            extra_data={
                'change_message': 'Changed username',
                'previous_value': 'olduser',
                'new_value': 'newuser'
            }
        )

        self.assertEqual(log.extra_data['change_message'], 'Changed username')
        self.assertEqual(log.extra_data['previous_value'], 'olduser')

    def test_audit_log_str_representation(self):
        """Test string representation of audit log."""
        log = AuditLog.objects.create(
            user=self.user,
            action_type='LOGIN',
            description='Test login',
            ip_address='192.168.1.1'
        )

        str_repr = str(log)
        self.assertIn('testuser', str_repr)
        self.assertIn('User Login', str_repr)  # Display name of action type


class AuditLogMiddlewareTests(TestCase):
    """Test the AuditLogMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Create a mock get_response callable
        def mock_get_response(request):
            # Simple mock response
            from django.http import HttpResponse
            return HttpResponse("OK")

        self.mock_get_response = mock_get_response
        self.middleware = AuditLogMiddleware(self.mock_get_response)

    def tearDown(self):
        # Clean up thread-local storage
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request

    def test_middleware_stores_request(self):
        """Test that middleware stores request in thread-local storage."""
        request = self.factory.get('/')

        response = self.middleware(request)

        # Request should not be in thread-local after response
        # (middleware cleans up)
        self.assertIsNone(get_current_request())

    def test_get_current_ip_basic(self):
        """Test extracting IP from REMOTE_ADDR."""
        request = self.factory.get('/', REMOTE_ADDR='192.168.1.100')
        _thread_locals.request = request

        ip = get_current_ip()

        self.assertEqual(ip, '192.168.1.100')

        del _thread_locals.request

    def test_get_current_ip_with_proxy(self):
        """Test extracting IP from X-Forwarded-For header."""
        request = self.factory.get(
            '/',
            HTTP_X_FORWARDED_FOR='203.0.113.1, 198.51.100.1',
            REMOTE_ADDR='10.0.0.1'
        )
        _thread_locals.request = request

        ip = get_current_ip()

        # Should get the first IP in X-Forwarded-For (original client)
        self.assertEqual(ip, '203.0.113.1')

        del _thread_locals.request

    def test_get_user_agent(self):
        """Test extracting user agent from request."""
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        request = self.factory.get('/', HTTP_USER_AGENT=user_agent)
        _thread_locals.request = request

        extracted_ua = get_user_agent()

        self.assertEqual(extracted_ua, user_agent)

        del _thread_locals.request

    def test_middleware_cleans_up_thread_local(self):
        """Test that middleware cleans up thread-local storage."""
        request = self.factory.get('/')

        # Middleware should store and then clean up
        response = self.middleware(request)

        # After middleware processes request, thread-local should be clean
        self.assertIsNone(get_current_request())


class AuditUtilsTests(TestCase):
    """Test the audit_utils.create_audit_log function."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.factory = RequestFactory()

    def tearDown(self):
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request

    def test_create_audit_log_with_request_context(self):
        """Test creating audit log with request context."""
        request = self.factory.get(
            '/',
            REMOTE_ADDR='192.168.1.50',
            HTTP_USER_AGENT='TestAgent/1.0'
        )
        _thread_locals.request = request

        log = create_audit_log(
            user=self.user,
            action_type='LOGIN',
            description='Test login'
        )

        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_type, 'LOGIN')
        self.assertEqual(log.ip_address, '192.168.1.50')
        self.assertEqual(log.user_agent, 'TestAgent/1.0')

        del _thread_locals.request

    def test_create_audit_log_without_request(self):
        """Test creating audit log when no request context available."""
        log = create_audit_log(
            user=self.user,
            action_type='LOGOUT',
            description='Test logout'
        )

        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.user)
        self.assertIsNone(log.ip_address)
        self.assertEqual(log.user_agent, '')

    def test_create_audit_log_with_resource_info(self):
        """Test creating audit log with resource details."""
        log = create_audit_log(
            user=self.user,
            action_type='ADMIN_DELETE',
            resource_type='Chat',
            resource_id=123,
            description='Deleted chat session',
            extra_data={'chat_title': 'Test Interview'}
        )

        self.assertEqual(log.resource_type, 'Chat')
        self.assertEqual(log.resource_id, '123')
        self.assertEqual(log.extra_data['chat_title'], 'Test Interview')


class AuthenticationLoggingTests(TestCase):
    """Test authentication event logging via signals."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_login_creates_audit_log(self):
        """Test that successful login creates an audit log."""
        # Clear any existing logs
        AuditLog.objects.all().delete()

        # Manually trigger the signal (simulating login)
        from django.contrib.auth.signals import user_logged_in
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.post('/accounts/login/')
        user_logged_in.send(sender=self.user.__class__, request=request, user=self.user)

        # Check that audit log was created
        logs = AuditLog.objects.filter(action_type='LOGIN')
        self.assertGreaterEqual(logs.count(), 1)

        log = logs.first()
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_type, 'LOGIN')
        self.assertIn('logged in', log.description.lower())

    def test_logout_creates_audit_log(self):
        """Test that logout creates an audit log."""
        # Clear logs
        AuditLog.objects.all().delete()

        # Manually trigger the logout signal (simulating logout)
        from django.contrib.auth.signals import user_logged_out
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.post('/accounts/logout/')
        user_logged_out.send(sender=self.user.__class__, request=request, user=self.user)

        # Check that audit log was created
        logs = AuditLog.objects.filter(action_type='LOGOUT')
        self.assertEqual(logs.count(), 1)

        log = logs.first()
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_type, 'LOGOUT')

    def test_failed_login_creates_audit_log(self):
        """Test that failed login attempt creates an audit log."""
        # Clear any existing logs
        AuditLog.objects.all().delete()

        # Manually trigger failed login signal
        from django.contrib.auth.signals import user_login_failed
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.post('/accounts/login/')
        credentials = {'username': 'testuser', 'password': 'wrongpassword'}
        user_login_failed.send(sender=User, credentials=credentials, request=request)

        # Check that audit log was created
        logs = AuditLog.objects.filter(action_type='LOGIN_FAILED')
        self.assertEqual(logs.count(), 1)

        log = logs.first()
        self.assertIsNone(log.user)  # No user for failed login
        self.assertEqual(log.action_type, 'LOGIN_FAILED')
        self.assertIn('testuser', log.extra_data.get('attempted_username', ''))


class AdminActionLoggingTests(TestCase):
    """Test admin action logging via LogEntry signals."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        self.regular_user = User.objects.create_user(
            username='regularuser',
            password='userpass123'
        )

    def test_admin_create_action_logged(self):
        """Test that admin create action is logged."""
        # Clear existing logs
        AuditLog.objects.all().delete()

        # Simulate admin creating a user via admin interface
        content_type = ContentType.objects.get_for_model(User)
        LogEntry.objects.create(
            user=self.admin_user,
            content_type=content_type,
            object_id=self.regular_user.id,
            object_repr=str(self.regular_user),
            action_flag=ADDITION,
            change_message='Created new user'
        )

        # Check that audit log was created
        logs = AuditLog.objects.filter(action_type='ADMIN_CREATE')
        self.assertEqual(logs.count(), 1)

        log = logs.first()
        self.assertEqual(log.user, self.admin_user)
        self.assertEqual(log.action_type, 'ADMIN_CREATE')
        self.assertIn('created', log.description.lower())
        self.assertIn('user', log.resource_type.lower())

    def test_admin_update_action_logged(self):
        """Test that admin update action is logged."""
        # Clear existing logs
        AuditLog.objects.all().delete()

        # Simulate admin updating a user
        content_type = ContentType.objects.get_for_model(User)
        LogEntry.objects.create(
            user=self.admin_user,
            content_type=content_type,
            object_id=self.regular_user.id,
            object_repr=str(self.regular_user),
            action_flag=CHANGE,
            change_message='Updated user email'
        )

        # Check that audit log was created
        logs = AuditLog.objects.filter(action_type='ADMIN_UPDATE')
        self.assertEqual(logs.count(), 1)

        log = logs.first()
        self.assertEqual(log.user, self.admin_user)
        self.assertEqual(log.action_type, 'ADMIN_UPDATE')
        self.assertIn('updated', log.description.lower())

    def test_admin_delete_action_logged(self):
        """Test that admin delete action is logged."""
        # Clear existing logs
        AuditLog.objects.all().delete()

        # Simulate admin deleting a user
        content_type = ContentType.objects.get_for_model(User)
        LogEntry.objects.create(
            user=self.admin_user,
            content_type=content_type,
            object_id=self.regular_user.id,
            object_repr=str(self.regular_user),
            action_flag=DELETION,
            change_message='Deleted user'
        )

        # Check that audit log was created
        logs = AuditLog.objects.filter(action_type='ADMIN_DELETE')
        self.assertEqual(logs.count(), 1)

        log = logs.first()
        self.assertEqual(log.user, self.admin_user)
        self.assertEqual(log.action_type, 'ADMIN_DELETE')
        self.assertIn('deleted', log.description.lower())


class AuditLogIntegrationTests(TestCase):
    """Integration tests for audit logging system."""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )

    def test_complete_login_flow_with_ip_capture(self):
        """Test complete login flow captures IP address."""
        AuditLog.objects.all().delete()

        # Manually trigger login signal with IP context
        from django.contrib.auth.signals import user_logged_in
        from django.test import RequestFactory
        from active_interview_app.middleware import _thread_locals

        factory = RequestFactory()
        request = factory.post('/accounts/login/', REMOTE_ADDR='203.0.113.50')

        # Set request in thread-local (simulating middleware)
        _thread_locals.request = request

        try:
            user_logged_in.send(sender=self.admin_user.__class__, request=request, user=self.admin_user)

            # Check audit log
            log = AuditLog.objects.filter(action_type='LOGIN').first()
            self.assertIsNotNone(log)
            self.assertEqual(log.ip_address, '203.0.113.50')
        finally:
            # Clean up thread-local
            if hasattr(_thread_locals, 'request'):
                del _thread_locals.request

    def test_audit_log_ordering(self):
        """Test that audit logs are ordered by timestamp descending."""
        AuditLog.objects.all().delete()

        # Create multiple logs
        user = User.objects.create_user(username='test', password='test123')

        log1 = create_audit_log(user=user, action_type='LOGIN', description='First')
        log2 = create_audit_log(user=user, action_type='LOGOUT', description='Second')
        log3 = create_audit_log(user=user, action_type='LOGIN', description='Third')

        # Get all logs
        logs = list(AuditLog.objects.all())

        # Should be ordered newest first
        self.assertEqual(logs[0].description, 'Third')
        self.assertEqual(logs[1].description, 'Second')
        self.assertEqual(logs[2].description, 'First')
