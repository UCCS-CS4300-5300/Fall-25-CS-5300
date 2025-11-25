"""
Tests for OpenAI utility functions

This module tests the centralized OpenAI client management and graceful degradation.
"""

from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from active_interview_app.openai_utils import get_openai_client, ai_available


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
        client1 = get_openai_client()
        client2 = get_openai_client()

        # Should only initialize once
        mock_openai.assert_called_once()
        self.assertEqual(client1, client2)

    @override_settings(OPENAI_API_KEY='')
    def test_get_openai_client_missing_api_key(self):
        """Test that ValueError is raised when API key is missing"""
        with self.assertRaises(ValueError) as context:
            get_openai_client()

        self.assertIn('OPENAI_API_KEY is not set', str(context.exception))

    @override_settings(OPENAI_API_KEY=None)
    def test_get_openai_client_none_api_key(self):
        """Test that ValueError is raised when API key is None"""
        with self.assertRaises(ValueError) as context:
            get_openai_client()

        self.assertIn('OPENAI_API_KEY is not set', str(context.exception))

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
