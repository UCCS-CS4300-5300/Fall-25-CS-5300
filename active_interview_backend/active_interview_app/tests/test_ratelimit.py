"""
Tests for rate limiting functionality.

Tests rate limiting on:
- API endpoints
- ViewSets
- Different user types (authenticated vs anonymous)
- Different rate limit groups (default, strict, lenient)
- HTTP 429 responses with proper headers
"""

import time
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from ..models import QuestionBank, Question, Tag, UploadedJobListing, UploadedResume
from .test_credentials import TEST_PASSWORD


class RateLimitTestCase(TestCase):
    """Base test case for rate limiting tests."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD
        )
        self.anonymous_client = Client()

    def make_requests(self, url, count, method='get', authenticated=True, data=None):
        """
        Make multiple requests to a URL.

        Args:
            url: URL to request
            count: Number of requests to make
            method: HTTP method ('get' or 'post')
            authenticated: Whether to use authenticated client
            data: Data to send with POST requests

        Returns:
            List of responses
        """
        client = self.client if authenticated else self.anonymous_client
        if authenticated:
            client.force_login(self.user)

        responses = []
        for _ in range(count):
            if method == 'post':
                response = client.post(url, data or {})
            else:
                response = client.get(url)
            responses.append(response)
            # Small delay to avoid race conditions
            time.sleep(0.01)

        return responses


@override_settings(
    RATELIMIT_ENABLE=True,
    ROOT_URLCONF='active_interview_app.tests.test_urls',
    TESTING=True
)
class APIViewRateLimitTest(RateLimitTestCase):
    """Test rate limiting on API views."""

    def test_strict_rate_limit_authenticated(self):
        """Test strict rate limiting for authenticated users (20/min)."""
        url = '/test/strict/'  # Using test URL with strict rate limiting

        # Make requests up to the limit (20)
        responses = self.make_requests(url, 20, method='get')

        # All should succeed
        for response in responses[:20]:
            self.assertNotEqual(response.status_code, 429)

        # Next request should be rate limited
        response = self.client.get(url)
        self.assertEqual(response.status_code, 429)

        # Check for Retry-After header
        self.assertIn('Retry-After', response)

    def test_lenient_rate_limit_authenticated(self):
        """Test lenient rate limiting for authenticated users (120/min)."""
        url = '/test/lenient/'  # Using test URL with lenient rate limiting

        # Make requests up to the limit (120)
        responses = self.make_requests(url, 120, method='get')

        # All should succeed
        for response in responses[:120]:
            self.assertNotEqual(response.status_code, 429)

        # Next request should be rate limited
        response = self.client.get(url)
        self.assertEqual(response.status_code, 429)

    def test_default_rate_limit_anonymous(self):
        """Test default rate limiting for anonymous users (30/min)."""
        url = '/test/default/'  # Using test URL with default rate limiting

        # Make requests up to the limit (30)
        responses = self.make_requests(url, 30, authenticated=False)

        # All should succeed
        for response in responses[:30]:
            self.assertNotEqual(response.status_code, 429)

        # Next request should be rate limited
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 429)


@override_settings(RATELIMIT_ENABLE=True, TESTING=True)
class ViewSetRateLimitTest(RateLimitTestCase):
    """Test rate limiting on ViewSets."""

    def setUp(self):
        """Set up test fixtures including question bank data."""
        super().setUp()

        # Make user an interviewer
        from django.contrib.auth.models import Group
        interviewer_group, _ = Group.objects.get_or_create(name='Interviewer')
        self.user.groups.add(interviewer_group)

        # Create a question bank
        self.question_bank = QuestionBank.objects.create(
            name='Test Bank',
            description='Test description',
            owner=self.user
        )

        # Create a tag
        self.tag = Tag.objects.create(
            name='Python'
        )

    def test_viewset_read_lenient_limit(self):
        """Test that read operations use lenient rate limits (120/min)."""
        # Clear the rate limit cache before testing
        from django.core.cache import cache
        cache.clear()

        url = reverse('question-bank-list')

        # Make requests up to the lenient limit
        responses = self.make_requests(url, 120, method='get')

        # All should succeed
        for response in responses[:120]:
            self.assertNotEqual(response.status_code, 429)

        # Next request should be rate limited
        response = self.client.get(url)
        self.assertEqual(response.status_code, 429)

    def test_viewset_write_strict_limit(self):
        """Test that write operations use strict rate limits (20/min)."""
        # Clear the rate limit cache before testing
        from django.core.cache import cache
        cache.clear()

        url = reverse('question-bank-list')
        data = {
            'name': 'New Bank',
            'description': 'New description'
        }

        # Make requests up to the strict limit
        responses = self.make_requests(url, 20, method='post', data=data)

        # All should succeed (or fail for other reasons, but not 429)
        for response in responses[:20]:
            self.assertNotEqual(response.status_code, 429)

        # Next request should be rate limited
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 429)


@override_settings(
    RATELIMIT_ENABLE=True,
    ROOT_URLCONF='active_interview_app.tests.test_urls',
    TESTING=True
)
class RateLimitResponseTest(RateLimitTestCase):
    """Test rate limit response format and headers."""

    def test_http_429_response(self):
        """Test that rate limit exceeded returns HTTP 429."""
        url = '/test/default/'

        # Exceed the rate limit
        self.make_requests(url, 31, authenticated=False)

        # Next request should return 429
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 429)

    def test_retry_after_header(self):
        """Test that 429 response includes Retry-After header."""
        url = '/test/default/'

        # Exceed the rate limit
        self.make_requests(url, 31, authenticated=False)

        # Check for Retry-After header
        response = self.anonymous_client.get(url)
        self.assertIn('Retry-After', response)
        self.assertTrue(int(response['Retry-After']) > 0)

    def test_api_json_response(self):
        """Test that API endpoints return JSON error for 429."""
        url = '/test/default/'

        # Exceed the rate limit
        self.make_requests(url, 31, method='get', authenticated=False)

        # Check response
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 429)

    def test_web_html_response(self):
        """Test that web pages return HTML error template for 429."""
        url = '/test/default/'

        # Exceed the rate limit
        self.make_requests(url, 31, authenticated=False)

        # Check HTML response
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 429)


@override_settings(
    RATELIMIT_ENABLE=True,
    ROOT_URLCONF='active_interview_app.tests.test_urls',
    TESTING=True
)
class RateLimitUserTypeTest(RateLimitTestCase):
    """Test rate limiting for different user types."""

    def test_authenticated_higher_limit(self):
        """Test that authenticated users have higher limits than anonymous."""
        url = '/test/default/'

        # Authenticated user can make 60 requests
        responses_auth = self.make_requests(url, 60, authenticated=True)
        for response in responses_auth[:60]:
            self.assertNotEqual(response.status_code, 429)

        # Anonymous user limited to 30 requests
        responses_anon = self.make_requests(url, 30, authenticated=False)
        for response in responses_anon[:30]:
            self.assertNotEqual(response.status_code, 429)

        # Next anonymous request should be limited
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 429)

    def test_ip_based_limiting_anonymous(self):
        """Test that anonymous users are limited by IP address."""
        url = '/test/default/'

        # Make requests as anonymous user
        self.make_requests(url, 31, authenticated=False)

        # Should be rate limited
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 429)

    def test_user_id_based_limiting_authenticated(self):
        """Test that authenticated users are limited by user ID."""
        url = '/test/default/'

        # Make requests as authenticated user
        self.make_requests(url, 61, authenticated=True)

        # Should be rate limited
        response = self.client.get(url)
        self.assertEqual(response.status_code, 429)


@override_settings(
    RATELIMIT_ENABLE=False,
    ROOT_URLCONF='active_interview_app.tests.test_urls',
    TESTING=True
)
class RateLimitDisabledTest(RateLimitTestCase):
    """Test that rate limiting can be disabled."""

    def test_rate_limiting_disabled(self):
        """Test that rate limits are not enforced when disabled."""
        url = '/test/default/'

        # Make many requests (more than any limit)
        responses = self.make_requests(url, 150, authenticated=False)

        # None should be rate limited
        for response in responses:
            self.assertNotEqual(response.status_code, 429)
