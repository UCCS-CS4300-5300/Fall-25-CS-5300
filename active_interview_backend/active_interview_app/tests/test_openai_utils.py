"""
Tests for OpenAI utility functions

This module tests the centralized OpenAI client management and graceful degradation.
Updated for Issue #13 to include tests for API key pool integration.
"""

import pytest
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock  # noqa: F401
from active_interview_app.openai_utils import (
    get_openai_client,
    ai_available,
    get_api_key_from_pool,
    get_current_api_key_info
)


class OpenAIUtilsTest(TestCase):
    """Test OpenAI utility functions"""

    def setUp(self):
        """Reset the global OpenAI client before each test"""
        import active_interview_app.openai_utils as openai_utils
        openai_utils._openai_client = None

    def tearDown(self):
        """Reset the global OpenAI client after each test"""
        import active_interview_app.openai_utils as openai_utils
        openai_utils._openai_client = None

    @override_settings(OPENAI_API_KEY='test-key-123')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_get_openai_client_success(self, mock_openai):
        """Test successful OpenAI client initialization"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        client = get_openai_client()

        # Verify OpenAI was called with the API key
        mock_openai.assert_called_once_with(api_key='test-key-123')
        self.assertEqual(client, mock_client)

    @override_settings(OPENAI_API_KEY='test-key-123')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_get_openai_client_singleton(self, mock_openai):
        """Test that get_openai_client returns the same instance (singleton pattern)"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Call twice
        client1 = get_openai_client()  # noqa: F841
        client2 = get_openai_client()  # noqa: F841

        # Should only initialize once
        mock_openai.assert_called_once()
        self.assertEqual(client1, client2)

    @override_settings(OPENAI_API_KEY='')
    def test_get_openai_client_missing_api_key(self):
        """Test that ValueError is raised when API key is missing"""
        with self.assertRaises(ValueError) as context:
            get_openai_client()

        self.assertIn('No OpenAI API key available', str(context.exception))

    @override_settings(OPENAI_API_KEY=None)
    def test_get_openai_client_none_api_key(self):
        """Test that ValueError is raised when API key is None"""
        with self.assertRaises(ValueError) as context:
            get_openai_client()

        self.assertIn('No OpenAI API key available', str(context.exception))

    @override_settings(OPENAI_API_KEY='test-key-123')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_get_openai_client_initialization_error(self, mock_openai):
        """Test that ValueError is raised when client initialization fails"""
        mock_openai.side_effect = Exception('Connection failed')

        with self.assertRaises(ValueError) as context:
            get_openai_client()

        self.assertIn('Failed to initialize OpenAI client',
                      str(context.exception))

    @override_settings(OPENAI_API_KEY='test-key-123')
    @patch('active_interview_app.openai_utils.OpenAI')
    def testai_available_when_client_initializes(self, mock_openai):
        """Test ai_available returns True when client can be initialized"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        self.assertTrue(ai_available())

    @override_settings(OPENAI_API_KEY='')
    def testai_available_when_api_key_missing(self):
        """Test ai_available returns False when API key is missing"""
        self.assertFalse(ai_available())

    @override_settings(OPENAI_API_KEY='test-key-123')
    @patch('active_interview_app.openai_utils.OpenAI')
    def testai_available_when_initialization_fails(self, mock_openai):
        """Test ai_available returns False when initialization fails"""
        mock_openai.side_effect = Exception('Connection failed')

        self.assertFalse(ai_available())

    @override_settings(OPENAI_API_KEY='test-key-123')
    @patch('active_interview_app.openai_utils.OpenAI')
    def testai_available_does_not_raise_exception(self, mock_openai):
        """Test that ai_available never raises exceptions"""
        mock_openai.side_effect = RuntimeError('Unexpected error')

        # Should not raise, just return False
        result = ai_available()
        self.assertFalse(result)

    @override_settings(OPENAI_API_KEY='sk-test123')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_max_tokens_constant(self, mock_openai):
        """Test that MAX_TOKENS constant is accessible"""
        from active_interview_app.openai_utils import MAX_TOKENS

        self.assertEqual(MAX_TOKENS, 15000)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_client_reset_after_error(self, mock_openai):
        """Test that client can be reinitialized after an error"""
        import active_interview_app.openai_utils as openai_utils

        # First call fails
        mock_openai.side_effect = Exception('First failure')
        with self.assertRaises(ValueError):
            get_openai_client()

        # Reset client
        openai_utils._openai_client = None

        # Second call succeeds
        mock_client = MagicMock()
        mock_openai.side_effect = None
        mock_openai.return_value = mock_client

        client = get_openai_client()
        self.assertEqual(client, mock_client)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_multipleai_available_calls(self, mock_openai):
        """Test multiple calls to ai_available use singleton pattern"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Call multiple times
        result1 = ai_available()
        result2 = ai_available()
        result3 = ai_available()

        # All should be True
        self.assertTrue(result1)
        self.assertTrue(result2)
        self.assertTrue(result3)

        # Client should only be initialized once
        mock_openai.assert_called_once()


class OpenAIUtilsPytestTest(TestCase):
    """Django TestCase-based tests for OpenAI utilities"""

    @override_settings(OPENAI_API_KEY='sk-test123')
    def test_get_openai_client_with_valid_key(self):
        """Test client initialization with valid API key"""
        import active_interview_app.openai_utils as openai_utils
        openai_utils._openai_client = None

        with patch('active_interview_app.openai_utils.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            client = get_openai_client()
            self.assertEqual(client, mock_client)

        # Cleanup
        openai_utils._openai_client = None

    @override_settings(OPENAI_API_KEY='')
    def testai_available_graceful_degradation(self):
        """Test graceful degradation when OpenAI is not available"""
        import active_interview_app.openai_utils as openai_utils
        openai_utils._openai_client = None

        # Should not raise, just return False
        result = ai_available()
        self.assertFalse(result)

        # Cleanup
        openai_utils._openai_client = None

    @override_settings(OPENAI_API_KEY='')
    def test_error_message_includes_configuration_hint(self):
        """Test that error messages provide helpful configuration hints"""
        import active_interview_app.openai_utils as openai_utils
        openai_utils._openai_client = None

        with self.assertRaises(ValueError) as exc_info:
            get_openai_client()

        self.assertIn('.env file', str(exc_info.exception))
        self.assertIn('environment variables', str(exc_info.exception))

        # Cleanup
        openai_utils._openai_client = None


class APIKeyPoolIntegrationTest(TestCase):
    """Test OpenAI utils integration with API key pool (Issue #13)"""

    def setUp(self):
        """Create test user and reset OpenAI client"""
        import active_interview_app.openai_utils as openai_utils
        openai_utils._openai_client = None
        openai_utils._current_api_key = None

        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )

    def tearDown(self):
        """Reset OpenAI client after tests"""
        import active_interview_app.openai_utils as openai_utils
        openai_utils._openai_client = None
        openai_utils._current_api_key = None

    @override_settings(OPENAI_API_KEY='sk-fallback-key')
    def test_get_api_key_from_pool_with_active_key(self):
        """Test that get_api_key_from_pool returns active key from pool"""
        from active_interview_app.api_key_rotation_models import APIKeyPool

        # Create active key in pool
        key = APIKeyPool.objects.create(
            provider='openai',
            key_name='Pool Key',
            status=APIKeyPool.ACTIVE,
            added_by=self.admin_user
        )
        key.set_key('sk-pool-key-123')
        key.save()

        # Should return pool key, not fallback
        api_key = get_api_key_from_pool()
        self.assertEqual(api_key, 'sk-pool-key-123')

        # Should increment usage
        key.refresh_from_db()
        self.assertEqual(key.usage_count, 1)
        self.assertIsNotNone(key.last_used_at)

    @override_settings(OPENAI_API_KEY='sk-fallback-key')
    def test_get_api_key_from_pool_fallback_to_settings(self):
        """Test fallback to settings when no pool key available"""
        # No active keys in pool
        api_key = get_api_key_from_pool()
        self.assertEqual(api_key, 'sk-fallback-key')

    @override_settings(OPENAI_API_KEY='')
    def test_get_api_key_from_pool_no_key_available(self):
        """Test error when no key available anywhere"""
        # No pool key, no fallback
        with self.assertRaises(ValueError) as context:
            get_api_key_from_pool()

        self.assertIn('No OpenAI API key available', str(context.exception))
        self.assertIn('Add a key to the API Key Pool', str(context.exception))

    @override_settings(OPENAI_API_KEY='sk-fallback')
    def test_get_api_key_from_pool_increments_usage(self):
        """Test that using a key increments its usage count"""
        from active_interview_app.api_key_rotation_models import APIKeyPool

        key = APIKeyPool.objects.create(
            provider='openai',
            key_name='Usage Test Key',
            status=APIKeyPool.ACTIVE,
            added_by=self.admin_user
        )
        key.set_key('sk-usage-test')
        key.save()

        # Use key multiple times
        for i in range(5):
            get_api_key_from_pool()

        # Verify usage count
        key.refresh_from_db()
        self.assertEqual(key.usage_count, 5)

    @override_settings(OPENAI_API_KEY='sk-fallback')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_get_openai_client_refreshes_on_key_change(self, mock_openai):
        """Test that client refreshes when active key changes"""
        from active_interview_app.api_key_rotation_models import APIKeyPool

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Create first active key
        key1 = APIKeyPool.objects.create(
            provider='openai',
            key_name='Key 1',
            status=APIKeyPool.ACTIVE,
            added_by=self.admin_user
        )
        key1.set_key('sk-key1')
        key1.save()

        # Get client (should use key1)
        client1 = get_openai_client()  # noqa: F841
        self.assertEqual(mock_openai.call_count, 1)
        mock_openai.assert_called_with(api_key='sk-key1')

        # Create second key and activate (simulating rotation)
        key2 = APIKeyPool.objects.create(
            provider='openai',
            key_name='Key 2',
            status=APIKeyPool.PENDING,
            added_by=self.admin_user
        )
        key2.set_key('sk-key2')
        key2.save()
        key2.activate()

        # Get client again (should refresh with key2)
        client2 = get_openai_client()  # noqa: F841
        self.assertEqual(mock_openai.call_count, 2)
        mock_openai.assert_called_with(api_key='sk-key2')

    @override_settings(OPENAI_API_KEY='sk-fallback')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_get_openai_client_force_refresh(self, mock_openai):
        """Test that force_refresh parameter forces client recreation"""
        from active_interview_app.api_key_rotation_models import APIKeyPool

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        key = APIKeyPool.objects.create(
            provider='openai',
            key_name='Test Key',
            status=APIKeyPool.ACTIVE,
            added_by=self.admin_user
        )
        key.set_key('sk-test')
        key.save()

        # Get client normally
        client1 = get_openai_client()  # noqa: F841
        self.assertEqual(mock_openai.call_count, 1)

        # Get client again (should use cached)
        client2 = get_openai_client()  # noqa: F841
        self.assertEqual(mock_openai.call_count, 1)  # Still 1, used cache

        # Force refresh
        _client3 = get_openai_client(force_refresh=True)  # noqa: F841
        self.assertEqual(mock_openai.call_count, 2)  # Created new client

    @override_settings(OPENAI_API_KEY='sk-fallback')
    def test_get_current_api_key_info_from_pool(self):
        """Test get_current_api_key_info returns pool key info"""
        from active_interview_app.api_key_rotation_models import APIKeyPool

        # Create active key
        key = APIKeyPool.objects.create(
            provider='openai',
            key_name='Info Test Key',
            status=APIKeyPool.ACTIVE,
            added_by=self.admin_user
        )
        key.set_key('sk-info-test-123456')
        key.usage_count = 42
        key.save()

        info = get_current_api_key_info()

        self.assertIsNotNone(info)
        self.assertEqual(info['key_name'], 'Info Test Key')
        self.assertIn('sk-', info['masked_key'])
        self.assertEqual(info['usage_count'], 42)
        self.assertEqual(info['source'], 'key_pool')
        self.assertIn('last_used_at', info)
        self.assertIn('activated_at', info)

    @override_settings(OPENAI_API_KEY='sk-fallback-key-12345')
    def test_get_current_api_key_info_from_environment(self):
        """Test get_current_api_key_info returns fallback key info"""
        # No pool keys
        info = get_current_api_key_info()

        self.assertIsNotNone(info)
        self.assertEqual(info['key_name'], 'Primary Environment Variable')
        self.assertIn('sk-', info['masked_key'])
        self.assertIsNone(info['usage_count'])
        self.assertIsNone(info['last_used_at'])
        self.assertEqual(info['source'], 'environment')

    @override_settings(OPENAI_API_KEY='')
    def test_get_current_api_key_info_no_key_available(self):
        """Test get_current_api_key_info returns None when no key available"""
        info = get_current_api_key_info()
        self.assertIsNone(info)

    @override_settings(OPENAI_API_KEY='sk-fallback')
    def test_key_pool_takes_precedence_over_environment(self):
        """Test that key pool is used when available, not environment variable"""
        from active_interview_app.api_key_rotation_models import APIKeyPool

        # Create active key in pool
        key = APIKeyPool.objects.create(
            provider='openai',
            key_name='Pool Key',
            status=APIKeyPool.ACTIVE,
            added_by=self.admin_user
        )
        key.set_key('sk-pool-key')
        key.save()

        # Should use pool key, not environment variable
        api_key = get_api_key_from_pool()
        self.assertEqual(api_key, 'sk-pool-key')
        self.assertNotEqual(api_key, 'sk-fallback')

        # Verify info shows pool source
        info = get_current_api_key_info()
        self.assertEqual(info['source'], 'key_pool')

    @override_settings(OPENAI_API_KEY='sk-fallback')
    def test_get_api_key_from_pool_handles_inactive_keys(self):
        """Test that only active keys are used from pool"""
        from active_interview_app.api_key_rotation_models import APIKeyPool

        # Create inactive key (should be ignored)
        inactive_key = APIKeyPool.objects.create(
            provider='openai',
            key_name='Inactive Key',
            status=APIKeyPool.INACTIVE,
            added_by=self.admin_user
        )
        inactive_key.set_key('sk-inactive')
        inactive_key.save()

        # Should fall back to environment since no active key
        api_key = get_api_key_from_pool()
        self.assertEqual(api_key, 'sk-fallback')

    @override_settings(OPENAI_API_KEY='sk-fallback')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_client_uses_same_key_when_no_rotation(self, mock_openai):
        """Test that client doesn't refresh when key hasn't changed"""
        from active_interview_app.api_key_rotation_models import APIKeyPool

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        key = APIKeyPool.objects.create(
            provider='openai',
            key_name='Stable Key',
            status=APIKeyPool.ACTIVE,
            added_by=self.admin_user
        )
        key.set_key('sk-stable')
        key.save()

        # Get client multiple times
        for i in range(5):
            get_openai_client()

        # Should only initialize once
        self.assertEqual(mock_openai.call_count, 1)

    @override_settings(OPENAI_API_KEY='sk-fallback')
    def test_masked_key_in_info(self):
        """Test that masked key properly hides the full key"""
        from active_interview_app.api_key_rotation_models import APIKeyPool

        full_key = 'sk-proj-1234567890abcdefghijklmnop'

        key = APIKeyPool.objects.create(
            provider='openai',
            key_name='Masked Test',
            status=APIKeyPool.ACTIVE,
            added_by=self.admin_user
        )
        key.set_key(full_key)
        key.save()

        info = get_current_api_key_info()

        # Masked key should not be the full key
        self.assertNotEqual(info['masked_key'], full_key)
        # Should contain ellipsis
        self.assertIn('...', info['masked_key'])
        # Should start with prefix
        self.assertTrue(info['masked_key'].startswith('sk-'))


@pytest.mark.django_db
class TestAPIKeyPoolPytest:
    """Pytest tests for API key pool integration"""

    def test_get_api_key_from_pool_with_pool_key(self, settings):
        """Test getting API key from pool using pytest"""
        import active_interview_app.openai_utils as openai_utils
        from active_interview_app.api_key_rotation_models import APIKeyPool

        openai_utils._openai_client = None
        openai_utils._current_api_key = None

        settings.OPENAI_API_KEY = 'sk-fallback'

        # Create user and key
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            is_staff=True
        )

        key = APIKeyPool.objects.create(
            provider='openai',
            key_name='Pytest Key',
            status=APIKeyPool.ACTIVE,
            added_by=admin_user
        )
        key.set_key('sk-pytest-key')
        key.save()

        # Get key from pool
        api_key = get_api_key_from_pool()
        assert api_key == 'sk-pytest-key'

        # Cleanup
        openai_utils._openai_client = None
        openai_utils._current_api_key = None

    def test_get_current_api_key_info_structure(self, settings):
        """Test that get_current_api_key_info returns correct structure"""
        import active_interview_app.openai_utils as openai_utils
        from active_interview_app.api_key_rotation_models import APIKeyPool

        openai_utils._openai_client = None
        openai_utils._current_api_key = None

        settings.OPENAI_API_KEY = 'sk-fallback'

        admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            is_staff=True
        )

        key = APIKeyPool.objects.create(
            provider='openai',
            key_name='Structure Test',
            status=APIKeyPool.ACTIVE,
            added_by=admin_user
        )
        key.set_key('sk-structure-test')
        key.save()

        info = get_current_api_key_info()

        # Verify structure
        assert 'key_name' in info
        assert 'masked_key' in info
        assert 'usage_count' in info
        assert 'last_used_at' in info
        assert 'activated_at' in info
        assert 'source' in info

        # Verify values
        assert info['key_name'] == 'Structure Test'
        assert info['source'] == 'key_pool'
        assert isinstance(info['usage_count'], int)

        # Cleanup
        openai_utils._openai_client = None
        openai_utils._current_api_key = None

    def test_error_message_mentions_key_pool(self, settings):
        """Test that error message mentions key pool option"""
        import active_interview_app.openai_utils as openai_utils

        openai_utils._openai_client = None
        openai_utils._current_api_key = None

        settings.OPENAI_API_KEY = ''

        with pytest.raises(ValueError) as exc_info:
            get_api_key_from_pool()

        error_message = str(exc_info.value)
        assert 'API Key Pool' in error_message
        assert 'OPENAI_API_KEY' in error_message

        # Cleanup
        openai_utils._openai_client = None
        openai_utils._current_api_key = None
