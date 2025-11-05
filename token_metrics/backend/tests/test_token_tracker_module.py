"""
Comprehensive tests for token_tracker module

Tests the new token tracking decorators and utilities.
"""

import os
import subprocess
from unittest.mock import patch, Mock, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User

from active_interview_app.token_tracker import (
    get_current_git_branch,
    track_openai_tokens,
    track_claude_tokens,
    manual_track_tokens
)
from active_interview_app.token_usage_models import TokenUsage


class GetCurrentGitBranchTests(TestCase):
    """Tests for get_current_git_branch function"""

    @patch('subprocess.run')
    def test_successful_branch_detection(self, mock_run):
        """Test successful git branch detection"""
        mock_run.return_value = MagicMock(
            stdout='feature/test-branch\n',
            returncode=0
        )

        branch = get_current_git_branch()

        self.assertEqual(branch, 'feature/test-branch')
        mock_run.assert_called_once_with(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        )

    @patch('subprocess.run')
    def test_main_branch_detection(self, mock_run):
        """Test detection of main branch"""
        mock_run.return_value = MagicMock(
            stdout='main\n',
            returncode=0
        )

        branch = get_current_git_branch()
        self.assertEqual(branch, 'main')

    @patch('subprocess.run')
    def test_branch_with_whitespace(self, mock_run):
        """Test branch name is trimmed"""
        mock_run.return_value = MagicMock(
            stdout='  develop  \n',
            returncode=0
        )

        branch = get_current_git_branch()
        self.assertEqual(branch, 'develop')

    @patch('subprocess.run', side_effect=subprocess.TimeoutExpired('git', 5))
    def test_timeout_fallback_to_env(self, mock_run):
        """Test fallback to environment variable on timeout"""
        with patch.dict(os.environ, {'GITHUB_HEAD_REF': 'env-branch'}):
            branch = get_current_git_branch()
            self.assertEqual(branch, 'env-branch')

    @patch('subprocess.run', side_effect=FileNotFoundError())
    def test_git_not_found_fallback(self, mock_run):
        """Test fallback when git not installed"""
        with patch.dict(os.environ, {'GITHUB_REF_NAME': 'ref-branch'}):
            branch = get_current_git_branch()
            self.assertEqual(branch, 'ref-branch')

    @patch('subprocess.run', side_effect=Exception('Generic error'))
    def test_exception_returns_unknown(self, mock_run):
        """Test generic exception returns 'unknown'"""
        with patch.dict(os.environ, {}, clear=True):
            branch = get_current_git_branch()
            self.assertEqual(branch, 'unknown')


class TrackOpenAITokensDecoratorTests(TestCase):
    """Tests for track_openai_tokens decorator"""

    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_decorator_tracks_tokens(self, mock_branch):
        """Test decorator successfully tracks OpenAI tokens"""
        mock_branch.return_value = 'test-branch'

        @track_openai_tokens(endpoint="chat.completions")
        def mock_api_call():
            response = Mock()
            response.usage = Mock()
            response.usage.prompt_tokens = 100
            response.usage.completion_tokens = 50
            response.usage.total_tokens = 150
            response.model = 'gpt-4o'
            return response

        # Call the decorated function
        result = mock_api_call()

        # Verify token record was created
        self.assertEqual(TokenUsage.objects.count(), 1)

        usage = TokenUsage.objects.first()
        self.assertEqual(usage.git_branch, 'test-branch')
        self.assertEqual(usage.model_name, 'gpt-4o')
        self.assertEqual(usage.endpoint, 'chat.completions')
        self.assertEqual(usage.prompt_tokens, 100)
        self.assertEqual(usage.completion_tokens, 50)
        self.assertEqual(usage.total_tokens, 150)

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_decorator_with_user_kwarg(self, mock_branch):
        """Test decorator captures user from kwargs"""
        mock_branch.return_value = 'main'

        @track_openai_tokens(endpoint="chat.completions")
        def mock_api_call(user=None):
            response = Mock()
            response.usage = Mock()
            response.usage.prompt_tokens = 200
            response.usage.completion_tokens = 100
            response.usage.total_tokens = 300
            response.model = 'gpt-4o'
            return response

        # Call with user
        mock_api_call(user=self.user)

        usage = TokenUsage.objects.first()
        self.assertEqual(usage.user, self.user)

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_decorator_without_usage_data(self, mock_branch):
        """Test decorator handles response without usage data"""
        mock_branch.return_value = 'main'

        @track_openai_tokens(endpoint="chat.completions")
        def mock_api_call():
            response = Mock()
            # No usage attribute
            return response

        # Should not raise exception
        mock_api_call()

        # No usage should be tracked
        self.assertEqual(TokenUsage.objects.count(), 0)

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_decorator_with_none_response(self, mock_branch):
        """Test decorator handles None response"""
        mock_branch.return_value = 'main'

        @track_openai_tokens(endpoint="chat.completions")
        def mock_api_call():
            return None

        # Should not raise exception
        mock_api_call()

        self.assertEqual(TokenUsage.objects.count(), 0)

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    @patch('active_interview_app.token_tracker.logger')
    def test_decorator_logs_on_success(self, mock_logger, mock_branch):
        """Test decorator logs successful tracking"""
        mock_branch.return_value = 'main'

        @track_openai_tokens(endpoint="chat.completions")
        def mock_api_call():
            response = Mock()
            response.usage = Mock()
            response.usage.prompt_tokens = 100
            response.usage.completion_tokens = 50
            response.usage.total_tokens = 150
            response.model = 'gpt-4o'
            return response

        mock_api_call()

        # Check that info log was called
        mock_logger.info.assert_called_once()

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    @patch('active_interview_app.token_tracker.logger')
    def test_decorator_handles_db_error(self, mock_logger, mock_branch):
        """Test decorator handles database errors gracefully"""
        mock_branch.return_value = 'main'

        @track_openai_tokens(endpoint="chat.completions")
        def mock_api_call():
            response = Mock()
            response.usage = Mock()
            response.usage.prompt_tokens = 100
            response.usage.completion_tokens = 50
            response.usage.total_tokens = 150
            response.model = 'gpt-4o'
            return response

        # Mock TokenUsage.objects.create to raise exception
        with patch('active_interview_app.token_tracker.TokenUsage.objects.create',
                   side_effect=Exception('DB Error')):
            result = mock_api_call()

            # Function should still return result
            self.assertIsNotNone(result)

            # Error should be logged
            mock_logger.error.assert_called_once()

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_decorator_with_invalid_user(self, mock_branch):
        """Test decorator handles invalid user object"""
        mock_branch.return_value = 'main'

        @track_openai_tokens(endpoint="chat.completions")
        def mock_api_call(user=None):
            response = Mock()
            response.usage = Mock()
            response.usage.prompt_tokens = 100
            response.usage.completion_tokens = 50
            response.usage.total_tokens = 150
            response.model = 'gpt-4o'
            return response

        # Call with invalid user (not a User instance)
        mock_api_call(user="invalid")

        usage = TokenUsage.objects.first()
        # Should store None for invalid user
        self.assertIsNone(usage.user)


class TrackClaudeTokensDecoratorTests(TestCase):
    """Tests for track_claude_tokens decorator"""

    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_decorator_tracks_claude_tokens(self, mock_branch):
        """Test decorator successfully tracks Claude tokens"""
        mock_branch.return_value = 'feature/claude'

        @track_claude_tokens(endpoint="messages")
        def mock_claude_call():
            response = Mock()
            response.usage = Mock()
            response.usage.input_tokens = 200
            response.usage.output_tokens = 100
            response.model = 'claude-sonnet-4-5-20250929'
            return response

        # Call the decorated function
        result = mock_claude_call()

        # Verify token record was created
        self.assertEqual(TokenUsage.objects.count(), 1)

        usage = TokenUsage.objects.first()
        self.assertEqual(usage.git_branch, 'feature/claude')
        self.assertEqual(usage.model_name, 'claude-sonnet-4-5-20250929')
        self.assertEqual(usage.endpoint, 'messages')
        self.assertEqual(usage.prompt_tokens, 200)
        self.assertEqual(usage.completion_tokens, 100)
        self.assertEqual(usage.total_tokens, 300)

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_decorator_with_user_parameter(self, mock_branch):
        """Test decorator with user parameter"""
        mock_branch.return_value = 'main'

        @track_claude_tokens(endpoint="messages", user=self.user)
        def mock_claude_call():
            response = Mock()
            response.usage = Mock()
            response.usage.input_tokens = 150
            response.usage.output_tokens = 75
            response.model = 'claude-sonnet-4-5-20250929'
            return response

        mock_claude_call()

        usage = TokenUsage.objects.first()
        self.assertEqual(usage.user, self.user)

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_decorator_default_model_name(self, mock_branch):
        """Test decorator uses default model name if not provided"""
        mock_branch.return_value = 'main'

        @track_claude_tokens(endpoint="messages")
        def mock_claude_call():
            response = Mock()
            response.usage = Mock()
            response.usage.input_tokens = 100
            response.usage.output_tokens = 50
            # No model attribute
            return response

        mock_claude_call()

        usage = TokenUsage.objects.first()
        self.assertEqual(usage.model_name, 'claude-sonnet-4-5-20250929')

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_decorator_without_usage(self, mock_branch):
        """Test decorator handles response without usage"""
        mock_branch.return_value = 'main'

        @track_claude_tokens(endpoint="messages")
        def mock_claude_call():
            response = Mock()
            # No usage attribute
            return response

        mock_claude_call()

        self.assertEqual(TokenUsage.objects.count(), 0)


class ManualTrackTokensTests(TestCase):
    """Tests for manual_track_tokens function"""

    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    @patch('active_interview_app.token_tracker.logger')
    def test_manual_tracking_success(self, mock_logger, mock_branch):
        """Test successful manual token tracking"""
        mock_branch.return_value = 'main'

        manual_track_tokens(
            model_name='gpt-4o',
            endpoint='manual-test',
            prompt_tokens=500,
            completion_tokens=250,
            user=self.user
        )

        # Verify record created
        self.assertEqual(TokenUsage.objects.count(), 1)

        usage = TokenUsage.objects.first()
        self.assertEqual(usage.model_name, 'gpt-4o')
        self.assertEqual(usage.endpoint, 'manual-test')
        self.assertEqual(usage.prompt_tokens, 500)
        self.assertEqual(usage.completion_tokens, 250)
        self.assertEqual(usage.total_tokens, 750)
        self.assertEqual(usage.user, self.user)
        self.assertEqual(usage.git_branch, 'main')

        # Check logging
        mock_logger.info.assert_called_once()

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_manual_tracking_without_user(self, mock_branch):
        """Test manual tracking without user"""
        mock_branch.return_value = 'develop'

        manual_track_tokens(
            model_name='claude-sonnet-4-5-20250929',
            endpoint='anonymous-test',
            prompt_tokens=300,
            completion_tokens=150
        )

        usage = TokenUsage.objects.first()
        self.assertIsNone(usage.user)
        self.assertEqual(usage.total_tokens, 450)

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    @patch('active_interview_app.token_tracker.logger')
    def test_manual_tracking_handles_error(self, mock_logger, mock_branch):
        """Test manual tracking handles errors gracefully"""
        mock_branch.return_value = 'main'

        # Mock TokenUsage.objects.create to raise exception
        with patch('active_interview_app.token_tracker.TokenUsage.objects.create',
                   side_effect=Exception('DB Error')):
            manual_track_tokens(
                model_name='gpt-4o',
                endpoint='error-test',
                prompt_tokens=100,
                completion_tokens=50
            )

            # Error should be logged
            mock_logger.error.assert_called_once()

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_manual_tracking_zero_tokens(self, mock_branch):
        """Test manual tracking with zero tokens"""
        mock_branch.return_value = 'main'

        manual_track_tokens(
            model_name='gpt-4o',
            endpoint='zero-test',
            prompt_tokens=0,
            completion_tokens=0
        )

        usage = TokenUsage.objects.first()
        self.assertEqual(usage.total_tokens, 0)


class TokenTrackerIntegrationTests(TestCase):
    """Integration tests for token tracker module"""

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

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_multiple_api_calls_tracked(self, mock_branch):
        """Test tracking multiple API calls"""
        mock_branch.return_value = 'main'

        @track_openai_tokens(endpoint="chat.completions")
        def openai_call():
            response = Mock()
            response.usage = Mock()
            response.usage.prompt_tokens = 100
            response.usage.completion_tokens = 50
            response.usage.total_tokens = 150
            response.model = 'gpt-4o'
            return response

        @track_claude_tokens(endpoint="messages")
        def claude_call():
            response = Mock()
            response.usage = Mock()
            response.usage.input_tokens = 200
            response.usage.output_tokens = 100
            response.model = 'claude-sonnet-4-5-20250929'
            return response

        # Make multiple calls
        openai_call()
        openai_call()
        claude_call()

        # Verify all tracked
        self.assertEqual(TokenUsage.objects.count(), 3)

        # Verify correct models
        gpt_count = TokenUsage.objects.filter(model_name='gpt-4o').count()
        claude_count = TokenUsage.objects.filter(
            model_name='claude-sonnet-4-5-20250929'
        ).count()

        self.assertEqual(gpt_count, 2)
        self.assertEqual(claude_count, 1)

    @patch('active_interview_app.token_tracker.get_current_git_branch')
    def test_mixed_tracking_methods(self, mock_branch):
        """Test using both decorators and manual tracking"""
        branches = ['main', 'develop', 'feature/test']

        for i, branch in enumerate(branches):
            mock_branch.return_value = branch

            @track_openai_tokens(endpoint="chat")
            def api_call():
                response = Mock()
                response.usage = Mock()
                response.usage.prompt_tokens = 100
                response.usage.completion_tokens = 50
                response.usage.total_tokens = 150
                response.model = 'gpt-4o'
                return response

            api_call()

            manual_track_tokens(
                model_name='claude-sonnet-4-5-20250929',
                endpoint='manual',
                prompt_tokens=200,
                completion_tokens=100
            )

        # Should have 6 total records (3 decorated + 3 manual)
        self.assertEqual(TokenUsage.objects.count(), 6)

        # Check all branches tracked
        tracked_branches = set(
            TokenUsage.objects.values_list('git_branch', flat=True)
        )
        self.assertEqual(tracked_branches, set(branches))
