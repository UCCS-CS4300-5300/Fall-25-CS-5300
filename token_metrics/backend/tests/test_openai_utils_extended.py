"""
Extended tests for openai_utils module

Tests the updated openai_utils with token tracking integration.
"""

from unittest.mock import patch, Mock, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth.models import User

from active_interview_app.openai_utils import (
    get_openai_client,
    _ai_available,
    create_chat_completion,
    MAX_TOKENS
)
from active_interview_app.token_usage_models import TokenUsage


class GetOpenAIClientTests(TestCase):
    """Tests for get_openai_client function"""

    @override_settings(OPENAI_API_KEY='test-key-12345')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_client_initialization_success(self, mock_openai):
        """Test successful OpenAI client initialization"""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # Reset global client
        import active_interview_app.openai_utils as utils
        utils._openai_client = None

        client = get_openai_client()

        self.assertIsNotNone(client)
        mock_openai.assert_called_once_with(api_key='test-key-12345')

    @override_settings(OPENAI_API_KEY='test-key-12345')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_client_singleton_pattern(self, mock_openai):
        """Test that client uses singleton pattern"""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # Reset global client
        import active_interview_app.openai_utils as utils
        utils._openai_client = None

        # Call twice
        client1 = get_openai_client()
        client2 = get_openai_client()

        # Should only initialize once
        mock_openai.assert_called_once()
        self.assertIs(client1, client2)

    @override_settings(OPENAI_API_KEY=None)
    def test_client_initialization_no_api_key(self):
        """Test client initialization fails without API key"""
        # Reset global client
        import active_interview_app.openai_utils as utils
        utils._openai_client = None

        with self.assertRaises(ValueError) as context:
            get_openai_client()

        self.assertIn('OPENAI_API_KEY is not set', str(context.exception))

    @override_settings(OPENAI_API_KEY='')
    def test_client_initialization_empty_api_key(self):
        """Test client initialization fails with empty API key"""
        # Reset global client
        import active_interview_app.openai_utils as utils
        utils._openai_client = None

        with self.assertRaises(ValueError) as context:
            get_openai_client()

        self.assertIn('OPENAI_API_KEY is not set', str(context.exception))

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_client_initialization_failure(self, mock_openai):
        """Test handling of OpenAI client initialization failure"""
        mock_openai.side_effect = Exception('API Error')

        # Reset global client
        import active_interview_app.openai_utils as utils
        utils._openai_client = None

        with self.assertRaises(ValueError) as context:
            get_openai_client()

        self.assertIn('Failed to initialize OpenAI client', str(context.exception))


class AIAvailableTests(TestCase):
    """Tests for _ai_available function"""

    @override_settings(OPENAI_API_KEY='test-key-12345')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_ai_available_returns_true(self, mock_openai):
        """Test _ai_available returns True when client initializes"""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # Reset global client
        import active_interview_app.openai_utils as utils
        utils._openai_client = None

        result = _ai_available()

        self.assertTrue(result)

    @override_settings(OPENAI_API_KEY=None)
    def test_ai_available_returns_false_no_key(self):
        """Test _ai_available returns False without API key"""
        # Reset global client
        import active_interview_app.openai_utils as utils
        utils._openai_client = None

        result = _ai_available()

        self.assertFalse(result)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_ai_available_returns_false_on_error(self, mock_openai):
        """Test _ai_available returns False on initialization error"""
        mock_openai.side_effect = Exception('Connection error')

        # Reset global client
        import active_interview_app.openai_utils as utils
        utils._openai_client = None

        result = _ai_available()

        self.assertFalse(result)


class CreateChatCompletionTests(TestCase):
    """Tests for create_chat_completion function"""

    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_create_chat_completion_success(self, mock_branch):
        """Test successful chat completion with token tracking"""
        mock_branch.return_value = 'main'

        # Create mock client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 150
        mock_response.usage.completion_tokens = 75
        mock_response.usage.total_tokens = 225
        mock_response.model = 'gpt-4o'
        mock_response.choices = [
            Mock(message=Mock(content='Test response'))
        ]

        mock_client.chat.completions.create.return_value = mock_response

        # Call function
        response = create_chat_completion(
            client=mock_client,
            model='gpt-4o',
            messages=[{'role': 'user', 'content': 'Hello'}],
            user=self.user
        )

        # Verify response returned
        self.assertEqual(response, mock_response)

        # Verify API was called with correct params
        mock_client.chat.completions.create.assert_called_once_with(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': 'Hello'}],
            user=self.user
        )

        # Verify token usage was tracked
        self.assertEqual(TokenUsage.objects.count(), 1)

        usage = TokenUsage.objects.first()
        self.assertEqual(usage.user, self.user)
        self.assertEqual(usage.model_name, 'gpt-4o')
        self.assertEqual(usage.endpoint, 'chat.completions')
        self.assertEqual(usage.prompt_tokens, 150)
        self.assertEqual(usage.completion_tokens, 75)
        self.assertEqual(usage.total_tokens, 225)

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_create_chat_completion_without_user(self, mock_branch):
        """Test chat completion without user"""
        mock_branch.return_value = 'develop'

        mock_client = Mock()
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        mock_response.model = 'gpt-4o'

        mock_client.chat.completions.create.return_value = mock_response

        response = create_chat_completion(
            client=mock_client,
            model='gpt-4o',
            messages=[{'role': 'user', 'content': 'Test'}]
        )

        # Verify token tracked without user
        usage = TokenUsage.objects.first()
        self.assertIsNone(usage.user)
        self.assertEqual(usage.prompt_tokens, 100)

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_create_chat_completion_with_max_tokens(self, mock_branch):
        """Test chat completion with max_tokens parameter"""
        mock_branch.return_value = 'main'

        mock_client = Mock()
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 200
        mock_response.usage.completion_tokens = 100
        mock_response.usage.total_tokens = 300
        mock_response.model = 'gpt-4o'

        mock_client.chat.completions.create.return_value = mock_response

        response = create_chat_completion(
            client=mock_client,
            model='gpt-4o',
            messages=[{'role': 'user', 'content': 'Long test'}],
            max_tokens=MAX_TOKENS
        )

        # Verify max_tokens was passed
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_kwargs['max_tokens'], MAX_TOKENS)

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_create_chat_completion_with_temperature(self, mock_branch):
        """Test chat completion with temperature parameter"""
        mock_branch.return_value = 'main'

        mock_client = Mock()
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 25
        mock_response.usage.total_tokens = 75
        mock_response.model = 'gpt-4o'

        mock_client.chat.completions.create.return_value = mock_response

        response = create_chat_completion(
            client=mock_client,
            model='gpt-4o',
            messages=[{'role': 'user', 'content': 'Creative test'}],
            temperature=0.7
        )

        # Verify temperature was passed
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_kwargs['temperature'], 0.7)

    def test_create_chat_completion_api_error(self):
        """Test handling of API errors"""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception('API Error')

        with self.assertRaises(Exception) as context:
            create_chat_completion(
                client=mock_client,
                model='gpt-4o',
                messages=[{'role': 'user', 'content': 'Error test'}]
            )

        self.assertIn('API Error', str(context.exception))

        # No token usage should be tracked on error
        self.assertEqual(TokenUsage.objects.count(), 0)

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_create_chat_completion_response_format(self, mock_branch):
        """Test chat completion with response_format parameter"""
        mock_branch.return_value = 'main'

        mock_client = Mock()
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 120
        mock_response.usage.completion_tokens = 60
        mock_response.usage.total_tokens = 180
        mock_response.model = 'gpt-4o'

        mock_client.chat.completions.create.return_value = mock_response

        response = create_chat_completion(
            client=mock_client,
            model='gpt-4o',
            messages=[{'role': 'user', 'content': 'JSON test'}],
            response_format={"type": "json_object"}
        )

        # Verify response_format was passed
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_kwargs['response_format'], {"type": "json_object"})


class MaxTokensConstantTests(TestCase):
    """Tests for MAX_TOKENS constant"""

    def test_max_tokens_value(self):
        """Test MAX_TOKENS constant has expected value"""
        self.assertEqual(MAX_TOKENS, 15000)
        self.assertIsInstance(MAX_TOKENS, int)


class OpenAIUtilsIntegrationTests(TestCase):
    """Integration tests for openai_utils module"""

    def setUp(self):
        """Set up test users"""
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass1'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass2'
        )

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.openai_utils.OpenAI')
    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_multiple_users_multiple_calls(self, mock_branch, mock_openai_class):
        """Test multiple API calls for multiple users"""
        mock_branch.return_value = 'main'

        # Setup mock client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Reset global client
        import active_interview_app.openai_utils as utils
        utils._openai_client = None

        # User 1 makes calls
        for i in range(2):
            mock_response = Mock()
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 100 * (i + 1)
            mock_response.usage.completion_tokens = 50 * (i + 1)
            mock_response.usage.total_tokens = 150 * (i + 1)
            mock_response.model = 'gpt-4o'

            mock_client.chat.completions.create.return_value = mock_response

            create_chat_completion(
                client=mock_client,
                model='gpt-4o',
                messages=[{'role': 'user', 'content': f'Test {i}'}],
                user=self.user1
            )

        # User 2 makes call
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 200
        mock_response.usage.completion_tokens = 100
        mock_response.usage.total_tokens = 300
        mock_response.model = 'gpt-4o'

        mock_client.chat.completions.create.return_value = mock_response

        create_chat_completion(
            client=mock_client,
            model='gpt-4o',
            messages=[{'role': 'user', 'content': 'Test'}],
            user=self.user2
        )

        # Verify all tracked
        self.assertEqual(TokenUsage.objects.count(), 3)
        self.assertEqual(TokenUsage.objects.filter(user=self.user1).count(), 2)
        self.assertEqual(TokenUsage.objects.filter(user=self.user2).count(), 1)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('active_interview_app.openai_utils.OpenAI')
    def test_ai_available_and_client_integration(self, mock_openai_class):
        """Test integration of _ai_available and get_openai_client"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Reset global client
        import active_interview_app.openai_utils as utils
        utils._openai_client = None

        # Check availability
        self.assertTrue(_ai_available())

        # Get client (should reuse existing)
        client = get_openai_client()
        self.assertIsNotNone(client)

        # Should only initialize once
        mock_openai_class.assert_called_once()
