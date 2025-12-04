"""Tests for rate limit configuration."""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from ..ratelimit_config import (
    get_rate_for_user,
    get_client_ip,
    ratelimit_key,
    DEFAULT_AUTHENTICATED_RATE,
    DEFAULT_ANONYMOUS_RATE,
    STRICT_AUTHENTICATED_RATE,
    STRICT_ANONYMOUS_RATE,
    LENIENT_AUTHENTICATED_RATE,
    LENIENT_ANONYMOUS_RATE
)


class GetRateForUserTest(TestCase):
    """Tests for get_rate_for_user function."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_default_rate_authenticated(self):
        """Test default rate for authenticated user."""
        request = self.factory.get('/')
        request.user = self.user

        rate = get_rate_for_user('default', request)
        self.assertEqual(rate, DEFAULT_AUTHENTICATED_RATE)

    def test_default_rate_anonymous(self):
        """Test default rate for anonymous user."""
        request = self.factory.get('/')
        request.user = type('User', (), {'is_authenticated': False})()

        rate = get_rate_for_user('default', request)
        self.assertEqual(rate, DEFAULT_ANONYMOUS_RATE)

    def test_strict_rate_authenticated(self):
        """Test strict rate for authenticated user."""
        request = self.factory.get('/')
        request.user = self.user

        rate = get_rate_for_user('strict', request)
        self.assertEqual(rate, STRICT_AUTHENTICATED_RATE)

    def test_strict_rate_anonymous(self):
        """Test strict rate for anonymous user."""
        request = self.factory.get('/')
        request.user = type('User', (), {'is_authenticated': False})()

        rate = get_rate_for_user('strict', request)
        self.assertEqual(rate, STRICT_ANONYMOUS_RATE)

    def test_lenient_rate_authenticated(self):
        """Test lenient rate for authenticated user."""
        request = self.factory.get('/')
        request.user = self.user

        rate = get_rate_for_user('lenient', request)
        self.assertEqual(rate, LENIENT_AUTHENTICATED_RATE)

    def test_lenient_rate_anonymous(self):
        """Test lenient rate for anonymous user."""
        request = self.factory.get('/')
        request.user = type('User', (), {'is_authenticated': False})()

        rate = get_rate_for_user('lenient', request)
        self.assertEqual(rate, LENIENT_ANONYMOUS_RATE)

    def test_unknown_group_authenticated(self):
        """Test unknown group defaults to default rate for authenticated."""
        request = self.factory.get('/')
        request.user = self.user

        rate = get_rate_for_user('unknown', request)
        self.assertEqual(rate, DEFAULT_AUTHENTICATED_RATE)

    def test_unknown_group_anonymous(self):
        """Test unknown group defaults to default rate for anonymous."""
        request = self.factory.get('/')
        request.user = type('User', (), {'is_authenticated': False})()

        rate = get_rate_for_user('unknown', request)
        self.assertEqual(rate, DEFAULT_ANONYMOUS_RATE)


class GetClientIpTest(TestCase):
    """Tests for get_client_ip function."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_direct_ip(self):
        """Test getting IP from REMOTE_ADDR."""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')

    def test_forwarded_ip_single(self):
        """Test getting IP from X-Forwarded-For with single IP."""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1'
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        ip = get_client_ip(request)
        self.assertEqual(ip, '10.0.0.1')

    def test_forwarded_ip_multiple(self):
        """Test getting IP from X-Forwarded-For with multiple IPs."""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1, 172.16.0.1'
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        ip = get_client_ip(request)
        # Should return the first IP (client's real IP)
        self.assertEqual(ip, '10.0.0.1')

    def test_forwarded_ip_with_spaces(self):
        """Test getting IP from X-Forwarded-For with spaces."""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '  10.0.0.1  ,  192.168.1.1  '
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        ip = get_client_ip(request)
        # Should strip whitespace
        self.assertEqual(ip, '10.0.0.1')

    def test_no_remote_addr(self):
        """Test getting IP when REMOTE_ADDR is not present."""
        request = self.factory.get('/')
        # RequestFactory sets REMOTE_ADDR to 127.0.0.1 by default
        # Remove it to test the None case
        if 'REMOTE_ADDR' in request.META:
            del request.META['REMOTE_ADDR']

        ip = get_client_ip(request)
        # Should return None when no IP available
        self.assertIsNone(ip)


class RatelimitKeyTest(TestCase):
    """Tests for ratelimit_key function."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_key_for_authenticated_user(self):
        """Test rate limit key for authenticated user."""
        request = self.factory.get('/')
        request.user = self.user

        key = ratelimit_key('default', request)
        self.assertEqual(key, f'user:{self.user.id}')

    def test_key_for_anonymous_user(self):
        """Test rate limit key for anonymous user."""
        request = self.factory.get('/')
        request.user = type('User', (), {'is_authenticated': False})()
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        key = ratelimit_key('default', request)
        self.assertEqual(key, 'ip:192.168.1.1')

    def test_key_for_anonymous_with_forwarded_ip(self):
        """Test rate limit key for anonymous user with X-Forwarded-For."""
        request = self.factory.get('/')
        request.user = type('User', (), {'is_authenticated': False})()
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1'
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        key = ratelimit_key('default', request)
        self.assertEqual(key, 'ip:10.0.0.1')

    def test_key_group_parameter(self):
        """Test that group parameter doesn't affect key."""
        request = self.factory.get('/')
        request.user = self.user

        # Group parameter is unused but required by django-ratelimit
        key1 = ratelimit_key('default', request)
        key2 = ratelimit_key('strict', request)
        key3 = ratelimit_key('lenient', request)

        # All should return the same key
        self.assertEqual(key1, key2)
        self.assertEqual(key2, key3)


class RateLimitConstantsTest(TestCase):
    """Tests for rate limit constants."""

    def test_default_authenticated_rate(self):
        """Test default authenticated rate is 60/m."""
        self.assertEqual(DEFAULT_AUTHENTICATED_RATE, '60/m')

    def test_default_anonymous_rate(self):
        """Test default anonymous rate is 30/m."""
        self.assertEqual(DEFAULT_ANONYMOUS_RATE, '30/m')

    def test_strict_authenticated_rate(self):
        """Test strict authenticated rate is 20/m."""
        self.assertEqual(STRICT_AUTHENTICATED_RATE, '20/m')

    def test_strict_anonymous_rate(self):
        """Test strict anonymous rate is 10/m."""
        self.assertEqual(STRICT_ANONYMOUS_RATE, '10/m')

    def test_lenient_authenticated_rate(self):
        """Test lenient authenticated rate is 120/m."""
        self.assertEqual(LENIENT_AUTHENTICATED_RATE, '120/m')

    def test_lenient_anonymous_rate(self):
        """Test lenient anonymous rate is 60/m."""
        self.assertEqual(LENIENT_ANONYMOUS_RATE, '60/m')
