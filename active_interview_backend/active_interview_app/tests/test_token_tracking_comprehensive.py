"""
Comprehensive tests for token tracking functionality

This module provides extensive coverage of token tracking utilities.
"""

import subprocess
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock, Mock
from active_interview_app.token_tracking import (
    get_current_git_branch,
    record_token_usage,
    record_claude_usage,
    record_openai_usage
)
from active_interview_app.token_usage_models import TokenUsage


class GetCurrentGitBranchTest(TestCase):
    """Test get_current_git_branch function"""

    @patch('subprocess.run')
    def test_get_current_git_branch_success(self, mock_run):
        """Test successful git branch retrieval"""
        mock_run.return_value = MagicMock(
            stdout='main\n',
            returncode=0
        )

        branch = get_current_git_branch()

        self.assertEqual(branch, 'main')
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_get_current_git_branch_feature_branch(self, mock_run):
        """Test git branch retrieval for feature branch"""
        mock_run.return_value = MagicMock(
            stdout='feature/oauth-integration\n',
            returncode=0
        )

        branch = get_current_git_branch()

        self.assertEqual(branch, 'feature/oauth-integration')

    @patch('subprocess.run')
    def test_get_current_git_branch_with_whitespace(self, mock_run):
        """Test git branch retrieval strips whitespace"""
        mock_run.return_value = MagicMock(
            stdout='  develop  \n',
            returncode=0
        )

        branch = get_current_git_branch()

        self.assertEqual(branch, 'develop')

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(128, 'git'))
    def test_get_current_git_branch_not_git_repo(self, mock_run):
        """Test git branch when not in a git repository"""
        branch = get_current_git_branch()

        self.assertEqual(branch, 'unknown')

    @patch('subprocess.run', side_effect=subprocess.TimeoutExpired('git', 5))
    def test_get_current_git_branch_timeout(self, mock_run):
        """Test git branch with timeout"""
        branch = get_current_git_branch()

        self.assertEqual(branch, 'unknown')

    @patch('subprocess.run', side_effect=FileNotFoundError)
    def test_get_current_git_branch_git_not_installed(self, mock_run):
        """Test git branch when git is not installed"""
        branch = get_current_git_branch()

        self.assertEqual(branch, 'unknown')

    @patch('subprocess.run')
    def test_get_current_git_branch_detached_head(self, mock_run):
        """Test git branch in detached HEAD state"""
        mock_run.return_value = MagicMock(
            stdout='HEAD\n',
            returncode=0
        )

        branch = get_current_git_branch()

        self.assertEqual(branch, 'HEAD')

    @patch('subprocess.run')
    def test_get_current_git_branch_special_characters(self, mock_run):
        """Test git branch with special characters"""
        mock_run.return_value = MagicMock(
            stdout='fix/issue-#123\n',
            returncode=0
        )

        branch = get_current_git_branch()

        self.assertEqual(branch, 'fix/issue-#123')


class RecordTokenUsageTest(TestCase):
    """Test record_token_usage function"""

    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_token_usage_success(self, mock_branch):
        """Test successful token usage recording"""
        mock_branch.return_value = 'main'

        # Create mock response
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        record_token_usage(
            user=self.user,
            endpoint='create_chat',
            model_name='gpt-4o',
            response=mock_response
        )

        # Verify TokenUsage was created
        usage = TokenUsage.objects.get(user=self.user)
        self.assertEqual(usage.endpoint, 'create_chat')
        self.assertEqual(usage.model_name, 'gpt-4o')
        self.assertEqual(usage.prompt_tokens, 100)
        self.assertEqual(usage.completion_tokens, 50)
        self.assertEqual(usage.total_tokens, 150)
        self.assertEqual(usage.git_branch, 'main')

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_token_usage_anonymous_user(self, mock_branch):
        """Test recording token usage for anonymous user"""
        mock_branch.return_value = 'main'

        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 25

        record_token_usage(
            user=None,
            endpoint='anonymous_chat',
            model_name='gpt-4o',
            response=mock_response
        )

        # Verify TokenUsage was created with None user
        usage = TokenUsage.objects.get(endpoint='anonymous_chat')
        self.assertIsNone(usage.user)
        self.assertEqual(usage.prompt_tokens, 50)

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_token_usage_different_models(self, mock_branch):
        """Test recording usage for different models"""
        mock_branch.return_value = 'develop'

        models = ['gpt-4o', 'gpt-3.5-turbo', 'claude-sonnet-4-5-20250929']

        for model in models:
            mock_response = Mock()
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50

            record_token_usage(
                user=self.user,
                endpoint=f'test_{model}',
                model_name=model,
                response=mock_response
            )

        # Verify all models were recorded
        self.assertEqual(TokenUsage.objects.filter(user=self.user).count(), 3)
        recorded_models = set(
            TokenUsage.objects.values_list('model_name', flat=True))
        self.assertEqual(recorded_models, set(models))

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_token_usage_zero_tokens(self, mock_branch):
        """Test recording usage with zero tokens"""
        mock_branch.return_value = 'main'

        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 0
        mock_response.usage.completion_tokens = 0

        record_token_usage(
            user=self.user,
            endpoint='zero_tokens',
            model_name='gpt-4o',
            response=mock_response
        )

        usage = TokenUsage.objects.get(endpoint='zero_tokens')
        self.assertEqual(usage.prompt_tokens, 0)
        self.assertEqual(usage.completion_tokens, 0)
        self.assertEqual(usage.total_tokens, 0)

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_token_usage_none_values(self, mock_branch):
        """Test recording usage when token values are None"""
        mock_branch.return_value = 'main'

        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = None
        mock_response.usage.completion_tokens = None

        record_token_usage(
            user=self.user,
            endpoint='none_tokens',
            model_name='gpt-4o',
            response=mock_response
        )

        # Should default to 0
        usage = TokenUsage.objects.get(endpoint='none_tokens')
        self.assertEqual(usage.prompt_tokens, 0)
        self.assertEqual(usage.completion_tokens, 0)

    @override_settings(DISABLE_TOKEN_TRACKING=True)
    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_token_usage_disabled(self, mock_branch):
        """Test that token tracking can be disabled"""
        mock_branch.return_value = 'main'

        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        record_token_usage(
            user=self.user,
            endpoint='disabled_endpoint',
            model_name='gpt-4o',
            response=mock_response
        )

        # No usage should be recorded
        self.assertEqual(TokenUsage.objects.filter(
            endpoint='disabled_endpoint').count(), 0)

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_token_usage_missing_usage_attribute(self, mock_branch):
        """Test handling response without usage attribute"""
        mock_branch.return_value = 'main'

        mock_response = Mock(spec=[])  # No usage attribute

        # Should not raise exception
        record_token_usage(
            user=self.user,
            endpoint='no_usage',
            model_name='gpt-4o',
            response=mock_response
        )

        # No usage should be recorded
        self.assertEqual(TokenUsage.objects.filter(
            endpoint='no_usage').count(), 0)

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    @patch('builtins.print')
    def test_record_token_usage_handles_exception(self, mock_print, mock_branch):
        """Test that exceptions are caught and logged"""
        mock_branch.return_value = 'main'

        mock_response = Mock()
        mock_response.usage = Mock()
        # Raise exception when accessing prompt_tokens
        type(mock_response.usage).prompt_tokens = property(
            lambda self: 1 / 0  # ZeroDivisionError
        )

        # Should not raise exception
        record_token_usage(
            user=self.user,
            endpoint='exception_test',
            model_name='gpt-4o',
            response=mock_response
        )

        # Should have printed error
        mock_print.assert_called()

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_token_usage_large_values(self, mock_branch):
        """Test recording very large token counts"""
        mock_branch.return_value = 'main'

        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 1000000
        mock_response.usage.completion_tokens = 500000

        record_token_usage(
            user=self.user,
            endpoint='large_tokens',
            model_name='gpt-4o',
            response=mock_response
        )

        usage = TokenUsage.objects.get(endpoint='large_tokens')
        self.assertEqual(usage.prompt_tokens, 1000000)
        self.assertEqual(usage.completion_tokens, 500000)
        self.assertEqual(usage.total_tokens, 1500000)


class RecordClaudeUsageTest(TestCase):
    """Test record_claude_usage function"""

    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_claude_usage_with_model(self, mock_branch):
        """Test recording Claude usage with model attribute"""
        mock_branch.return_value = 'main'

        mock_response = Mock()
        mock_response.model = 'claude-sonnet-4-5-20250929'
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 200
        mock_response.usage.completion_tokens = 100

        record_claude_usage(
            user=self.user,
            endpoint='claude_test',
            response=mock_response
        )

        usage = TokenUsage.objects.get(endpoint='claude_test')
        self.assertEqual(usage.model_name, 'claude-sonnet-4-5-20250929')
        self.assertEqual(usage.prompt_tokens, 200)

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_claude_usage_without_model(self, mock_branch):
        """Test recording Claude usage without model attribute"""
        mock_branch.return_value = 'main'

        mock_response = Mock(spec=['usage'])
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 150
        mock_response.usage.completion_tokens = 75

        record_claude_usage(
            user=self.user,
            endpoint='claude_no_model',
            response=mock_response
        )

        usage = TokenUsage.objects.get(endpoint='claude_no_model')
        self.assertEqual(usage.model_name, 'claude-unknown')

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_claude_usage_haiku_model(self, mock_branch):
        """Test recording Claude Haiku usage"""
        mock_branch.return_value = 'main'

        mock_response = Mock()
        mock_response.model = 'claude-haiku-3-5-20241022'
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 25

        record_claude_usage(
            user=self.user,
            endpoint='claude_haiku',
            response=mock_response
        )

        usage = TokenUsage.objects.get(endpoint='claude_haiku')
        self.assertEqual(usage.model_name, 'claude-haiku-3-5-20241022')


class RecordOpenAIUsageTest(TestCase):
    """Test record_openai_usage function"""

    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_openai_usage_with_model(self, mock_branch):
        """Test recording OpenAI usage with model attribute"""
        mock_branch.return_value = 'main'

        mock_response = Mock()
        mock_response.model = 'gpt-4o'
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 300
        mock_response.usage.completion_tokens = 150

        record_openai_usage(
            user=self.user,
            endpoint='openai_test',
            response=mock_response
        )

        usage = TokenUsage.objects.get(endpoint='openai_test')
        self.assertEqual(usage.model_name, 'gpt-4o')
        self.assertEqual(usage.prompt_tokens, 300)

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_openai_usage_without_model(self, mock_branch):
        """Test recording OpenAI usage without model attribute"""
        mock_branch.return_value = 'main'

        mock_response = Mock(spec=['usage'])
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        record_openai_usage(
            user=self.user,
            endpoint='openai_no_model',
            response=mock_response
        )

        usage = TokenUsage.objects.get(endpoint='openai_no_model')
        self.assertEqual(usage.model_name, 'gpt-unknown')

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_openai_usage_gpt35_turbo(self, mock_branch):
        """Test recording GPT-3.5-turbo usage"""
        mock_branch.return_value = 'main'

        mock_response = Mock()
        mock_response.model = 'gpt-3.5-turbo'
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 80
        mock_response.usage.completion_tokens = 40

        record_openai_usage(
            user=self.user,
            endpoint='gpt35_test',
            response=mock_response
        )

        usage = TokenUsage.objects.get(endpoint='gpt35_test')
        self.assertEqual(usage.model_name, 'gpt-3.5-turbo')

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_record_openai_usage_gpt4_turbo(self, mock_branch):
        """Test recording GPT-4-turbo usage"""
        mock_branch.return_value = 'main'

        mock_response = Mock()
        mock_response.model = 'gpt-4-turbo-preview'
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 500
        mock_response.usage.completion_tokens = 250

        record_openai_usage(
            user=self.user,
            endpoint='gpt4_turbo_test',
            response=mock_response
        )

        usage = TokenUsage.objects.get(endpoint='gpt4_turbo_test')
        self.assertEqual(usage.model_name, 'gpt-4-turbo-preview')


class TokenTrackingIntegrationTest(TestCase):
    """Integration tests for token tracking"""

    def setUp(self):
        """Set up test users"""
        self.user1 = User.objects.create_user(
            username='user1', password='pass1')
        self.user2 = User.objects.create_user(
            username='user2', password='pass2')

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_multiple_users_token_tracking(self, mock_branch):
        """Test token tracking for multiple users"""
        mock_branch.return_value = 'main'

        # User 1 makes API calls
        for i in range(3):
            mock_response = Mock()
            mock_response.model = 'gpt-4o'
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 100 * (i + 1)
            mock_response.usage.completion_tokens = 50 * (i + 1)

            record_openai_usage(self.user1, f'endpoint_{i}', mock_response)

        # User 2 makes API calls
        for i in range(2):
            mock_response = Mock()
            mock_response.model = 'claude-sonnet-4-5-20250929'
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 200 * (i + 1)
            mock_response.usage.completion_tokens = 100 * (i + 1)

            record_claude_usage(self.user2, f'endpoint_{i}', mock_response)

        # Verify user1 has 3 usage records
        self.assertEqual(TokenUsage.objects.filter(user=self.user1).count(), 3)

        # Verify user2 has 2 usage records
        self.assertEqual(TokenUsage.objects.filter(user=self.user2).count(), 2)

        # Verify total tokens for user1
        user1_total = sum(TokenUsage.objects.filter(
            user=self.user1).values_list('total_tokens', flat=True))
        self.assertEqual(user1_total, 150 + 300 + 450)  # 900

    @patch('active_interview_app.token_tracking.get_current_git_branch')
    def test_different_branches_tracking(self, mock_branch):
        """Test token tracking across different git branches"""
        branches = ['main', 'develop', 'feature/new-feature']

        for branch in branches:
            mock_branch.return_value = branch

            mock_response = Mock()
            mock_response.model = 'gpt-4o'
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50

            record_openai_usage(
                self.user1, f'{branch}_endpoint', mock_response)

        # Verify all branches were recorded
        recorded_branches = set(
            TokenUsage.objects.values_list('git_branch', flat=True))
        self.assertEqual(recorded_branches, set(branches))
