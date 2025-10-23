"""
Comprehensive tests for token tracking models
"""
from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from active_interview_app.token_usage_models import TokenUsage
from active_interview_app.merge_stats_models import MergeTokenStats


class TokenUsageModelTest(TestCase):
    """Test cases for TokenUsage model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_token_usage(self):
        """Test creating a token usage record"""
        token_usage = TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='gpt-4o',
            endpoint='/v1/chat/completions',
            prompt_tokens=100,
            completion_tokens=50
        )
        self.assertEqual(token_usage.user, self.user)
        self.assertEqual(token_usage.git_branch, 'feature/test')
        self.assertEqual(token_usage.model_name, 'gpt-4o')
        self.assertEqual(token_usage.prompt_tokens, 100)
        self.assertEqual(token_usage.completion_tokens, 50)

    def test_total_tokens_auto_calculated(self):
        """Test that total_tokens is automatically calculated on save"""
        token_usage = TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='gpt-4o',
            endpoint='/v1/chat/completions',
            prompt_tokens=100,
            completion_tokens=50
        )
        self.assertEqual(token_usage.total_tokens, 150)

    def test_str_method(self):
        """Test the __str__ method"""
        token_usage = TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='gpt-4o',
            endpoint='/v1/chat/completions',
            prompt_tokens=100,
            completion_tokens=50
        )
        str_repr = str(token_usage)
        self.assertIn('gpt-4o', str_repr)
        self.assertIn('feature/test', str_repr)
        self.assertIn('150', str_repr)

    def test_estimated_cost_gpt4o(self):
        """Test cost estimation for GPT-4o"""
        token_usage = TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='gpt-4o',
            endpoint='/v1/chat/completions',
            prompt_tokens=1000,
            completion_tokens=1000
        )
        # GPT-4o: $0.03 per 1k prompt, $0.06 per 1k completion
        # (1000/1000 * 0.03) + (1000/1000 * 0.06) = 0.09
        expected_cost = 0.09
        self.assertAlmostEqual(token_usage.estimated_cost, expected_cost, places=2)

    def test_estimated_cost_claude(self):
        """Test cost estimation for Claude Sonnet 4.5"""
        token_usage = TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='claude-sonnet-4-5-20250929',
            endpoint='/v1/messages',
            prompt_tokens=1000,
            completion_tokens=1000
        )
        # Claude: $0.003 per 1k prompt, $0.015 per 1k completion
        # (1000/1000 * 0.003) + (1000/1000 * 0.015) = 0.018
        expected_cost = 0.018
        self.assertAlmostEqual(token_usage.estimated_cost, expected_cost, places=3)

    def test_estimated_cost_unknown_model(self):
        """Test cost estimation for unknown model uses default"""
        token_usage = TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='unknown-model',
            endpoint='/v1/completions',
            prompt_tokens=1000,
            completion_tokens=1000
        )
        # Should use default GPT-4o pricing
        expected_cost = 0.09
        self.assertAlmostEqual(token_usage.estimated_cost, expected_cost, places=2)

    def test_get_branch_summary(self):
        """Test getting summary for a branch"""
        # Create multiple token usage records
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='gpt-4o',
            endpoint='/v1/chat/completions',
            prompt_tokens=100,
            completion_tokens=50
        )
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='gpt-4o',
            endpoint='/v1/chat/completions',
            prompt_tokens=200,
            completion_tokens=100
        )
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='claude-sonnet-4-5-20250929',
            endpoint='/v1/messages',
            prompt_tokens=150,
            completion_tokens=75
        )

        summary = TokenUsage.get_branch_summary('feature/test')

        self.assertEqual(summary['total_requests'], 3)
        self.assertIn('gpt-4o', summary['by_model'])
        self.assertIn('claude-sonnet-4-5-20250929', summary['by_model'])
        self.assertEqual(summary['by_model']['gpt-4o']['requests'], 2)
        self.assertEqual(summary['by_model']['gpt-4o']['prompt_tokens'], 300)
        self.assertEqual(summary['by_model']['gpt-4o']['completion_tokens'], 150)
        self.assertEqual(summary['by_model']['claude-sonnet-4-5-20250929']['requests'], 1)
        self.assertEqual(summary['total_tokens'], 675)

    def test_get_branch_summary_empty(self):
        """Test getting summary for branch with no records"""
        summary = TokenUsage.get_branch_summary('nonexistent-branch')
        self.assertEqual(summary['total_requests'], 0)
        self.assertEqual(summary['total_tokens'], 0)
        self.assertEqual(summary['total_cost'], 0.0)
        self.assertEqual(len(summary['by_model']), 0)

    def test_user_set_null_on_deletion(self):
        """Test that user is set to NULL when user is deleted"""
        token_usage = TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='gpt-4o',
            endpoint='/v1/chat/completions',
            prompt_tokens=100,
            completion_tokens=50
        )
        token_id = token_usage.id
        self.user.delete()

        token_usage.refresh_from_db()
        self.assertIsNone(token_usage.user)

    def test_ordering(self):
        """Test that records are ordered by created_at descending"""
        usage1 = TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='gpt-4o',
            endpoint='/v1/chat/completions',
            prompt_tokens=100,
            completion_tokens=50
        )
        usage2 = TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='gpt-4o',
            endpoint='/v1/chat/completions',
            prompt_tokens=200,
            completion_tokens=100
        )

        records = list(TokenUsage.objects.all())
        self.assertEqual(records[0].id, usage2.id)
        self.assertEqual(records[1].id, usage1.id)


class MergeTokenStatsModelTest(TestCase):
    """Test cases for MergeTokenStats model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_merge_stats(self):
        """Test creating merge token statistics"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/test',
            target_branch='main',
            merge_commit_sha='abc123def456',
            merged_by=self.user,
            pr_number=42,
            claude_prompt_tokens=1000,
            claude_completion_tokens=500,
            chatgpt_prompt_tokens=800,
            chatgpt_completion_tokens=400
        )
        self.assertEqual(merge_stats.source_branch, 'feature/test')
        self.assertEqual(merge_stats.target_branch, 'main')
        self.assertEqual(merge_stats.merge_commit_sha, 'abc123def456')
        self.assertEqual(merge_stats.merged_by, self.user)
        self.assertEqual(merge_stats.pr_number, 42)

    def test_auto_calculate_totals_on_save(self):
        """Test that totals are automatically calculated on save"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/test',
            merge_commit_sha='abc123',
            claude_prompt_tokens=1000,
            claude_completion_tokens=500,
            chatgpt_prompt_tokens=800,
            chatgpt_completion_tokens=400
        )

        self.assertEqual(merge_stats.claude_total_tokens, 1500)
        self.assertEqual(merge_stats.chatgpt_total_tokens, 1200)
        self.assertEqual(merge_stats.total_prompt_tokens, 1800)
        self.assertEqual(merge_stats.total_completion_tokens, 900)
        self.assertEqual(merge_stats.total_tokens, 2700)

    def test_request_count_calculation(self):
        """Test that request count is sum of claude and chatgpt requests"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/test',
            merge_commit_sha='abc123',
            claude_request_count=5,
            chatgpt_request_count=3
        )
        self.assertEqual(merge_stats.request_count, 8)

    def test_branch_cost_property(self):
        """Test branch_cost property calculation"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/test',
            merge_commit_sha='abc123',
            claude_prompt_tokens=1000,
            claude_completion_tokens=1000,
            chatgpt_prompt_tokens=1000,
            chatgpt_completion_tokens=1000
        )

        # Claude: (1000/1000 * 0.003) + (1000/1000 * 0.015) = 0.018
        # ChatGPT: (1000/1000 * 0.03) + (1000/1000 * 0.06) = 0.09
        # Total: 0.108
        expected_cost = 0.108
        self.assertAlmostEqual(merge_stats.branch_cost, expected_cost, places=3)

    def test_cumulative_first_record(self):
        """Test cumulative values for first record"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/test',
            merge_commit_sha='abc123',
            claude_prompt_tokens=1000,
            claude_completion_tokens=500,
            chatgpt_prompt_tokens=800,
            chatgpt_completion_tokens=400
        )

        self.assertEqual(merge_stats.cumulative_claude_tokens, 1500)
        self.assertEqual(merge_stats.cumulative_chatgpt_tokens, 1200)
        self.assertEqual(merge_stats.cumulative_total_tokens, 2700)
        self.assertGreater(merge_stats.cumulative_cost, 0)

    def test_cumulative_multiple_records(self):
        """Test cumulative values accumulate across records"""
        # First merge
        merge1 = MergeTokenStats.objects.create(
            source_branch='feature/first',
            merge_commit_sha='abc111',
            claude_prompt_tokens=1000,
            claude_completion_tokens=500,
            chatgpt_prompt_tokens=800,
            chatgpt_completion_tokens=400
        )

        # Second merge
        merge2 = MergeTokenStats.objects.create(
            source_branch='feature/second',
            merge_commit_sha='abc222',
            claude_prompt_tokens=500,
            claude_completion_tokens=250,
            chatgpt_prompt_tokens=400,
            chatgpt_completion_tokens=200
        )

        # Check that merge2 cumulative includes merge1
        self.assertEqual(
            merge2.cumulative_claude_tokens,
            merge1.cumulative_claude_tokens + 750
        )
        self.assertEqual(
            merge2.cumulative_chatgpt_tokens,
            merge1.cumulative_chatgpt_tokens + 600
        )
        self.assertEqual(
            merge2.cumulative_total_tokens,
            merge1.cumulative_total_tokens + 1350
        )
        self.assertGreater(merge2.cumulative_cost, merge1.cumulative_cost)

    def test_str_method(self):
        """Test the __str__ method"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/test',
            target_branch='main',
            merge_commit_sha='abc123',
            claude_prompt_tokens=1000,
            claude_completion_tokens=500
        )
        str_repr = str(merge_stats)
        self.assertIn('feature/test', str_repr)
        self.assertIn('main', str_repr)
        self.assertIn('tokens', str_repr)

    def test_unique_commit_sha(self):
        """Test that merge_commit_sha must be unique"""
        MergeTokenStats.objects.create(
            source_branch='feature/test',
            merge_commit_sha='abc123unique',
            claude_prompt_tokens=1000,
            claude_completion_tokens=500
        )

        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            MergeTokenStats.objects.create(
                source_branch='feature/other',
                merge_commit_sha='abc123unique',
                claude_prompt_tokens=500,
                claude_completion_tokens=250
            )

    def test_default_target_branch(self):
        """Test that target_branch defaults to 'main'"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/test',
            merge_commit_sha='abc123'
        )
        self.assertEqual(merge_stats.target_branch, 'main')

    def test_merged_by_set_null(self):
        """Test that merged_by is set to NULL when user is deleted"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/test',
            merge_commit_sha='abc123',
            merged_by=self.user
        )
        merge_id = merge_stats.id
        self.user.delete()

        merge_stats.refresh_from_db()
        self.assertIsNone(merge_stats.merged_by)

    def test_create_from_branch_with_tokens(self):
        """Test create_from_branch classmethod with token usage"""
        # Create token usage records
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='gpt-4o',
            endpoint='/v1/chat/completions',
            prompt_tokens=100,
            completion_tokens=50
        )
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='gpt-4o',
            endpoint='/v1/chat/completions',
            prompt_tokens=200,
            completion_tokens=100
        )
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/test',
            model_name='claude-sonnet-4-5-20250929',
            endpoint='/v1/messages',
            prompt_tokens=150,
            completion_tokens=75
        )

        # Create merge stats from branch
        merge_stats = MergeTokenStats.create_from_branch(
            branch_name='feature/test',
            commit_sha='abc123frommethod',
            merged_by=self.user,
            pr_number=99
        )

        self.assertEqual(merge_stats.source_branch, 'feature/test')
        self.assertEqual(merge_stats.merge_commit_sha, 'abc123frommethod')
        self.assertEqual(merge_stats.merged_by, self.user)
        self.assertEqual(merge_stats.pr_number, 99)
        self.assertEqual(merge_stats.chatgpt_prompt_tokens, 300)
        self.assertEqual(merge_stats.chatgpt_completion_tokens, 150)
        self.assertEqual(merge_stats.chatgpt_request_count, 2)
        self.assertEqual(merge_stats.claude_prompt_tokens, 150)
        self.assertEqual(merge_stats.claude_completion_tokens, 75)
        self.assertEqual(merge_stats.claude_request_count, 1)

    def test_create_from_branch_no_tokens(self):
        """Test create_from_branch with no token usage"""
        merge_stats = MergeTokenStats.create_from_branch(
            branch_name='feature/empty',
            commit_sha='abc123empty'
        )

        self.assertEqual(merge_stats.source_branch, 'feature/empty')
        self.assertEqual(merge_stats.claude_prompt_tokens, 0)
        self.assertEqual(merge_stats.claude_completion_tokens, 0)
        self.assertEqual(merge_stats.chatgpt_prompt_tokens, 0)
        self.assertEqual(merge_stats.chatgpt_completion_tokens, 0)

    def test_get_breakdown_summary(self):
        """Test get_breakdown_summary method"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/test',
            merge_commit_sha='abc123',
            claude_prompt_tokens=1000,
            claude_completion_tokens=500,
            claude_request_count=5,
            chatgpt_prompt_tokens=800,
            chatgpt_completion_tokens=400,
            chatgpt_request_count=3
        )

        breakdown = merge_stats.get_breakdown_summary()

        self.assertEqual(breakdown['branch'], 'feature/test')
        self.assertIsNotNone(breakdown['merge_date'])
        self.assertEqual(breakdown['claude']['prompt_tokens'], 1000)
        self.assertEqual(breakdown['claude']['completion_tokens'], 500)
        self.assertEqual(breakdown['claude']['total_tokens'], 1500)
        self.assertEqual(breakdown['claude']['requests'], 5)
        self.assertEqual(breakdown['chatgpt']['prompt_tokens'], 800)
        self.assertEqual(breakdown['chatgpt']['completion_tokens'], 400)
        self.assertEqual(breakdown['chatgpt']['total_tokens'], 1200)
        self.assertEqual(breakdown['chatgpt']['requests'], 3)
        self.assertEqual(breakdown['totals']['prompt_tokens'], 1800)
        self.assertEqual(breakdown['totals']['completion_tokens'], 900)
        self.assertEqual(breakdown['totals']['total_tokens'], 2700)
        self.assertEqual(breakdown['totals']['requests'], 8)
        self.assertIn('$', breakdown['totals']['cost'])
        self.assertIn('cumulative', breakdown)

    def test_ordering(self):
        """Test that records are ordered by merge_date descending"""
        merge1 = MergeTokenStats.objects.create(
            source_branch='feature/first',
            merge_commit_sha='abc111'
        )
        merge2 = MergeTokenStats.objects.create(
            source_branch='feature/second',
            merge_commit_sha='abc222'
        )

        records = list(MergeTokenStats.objects.all())
        self.assertEqual(records[0].id, merge2.id)
        self.assertEqual(records[1].id, merge1.id)

    def test_notes_field(self):
        """Test notes field can store additional metadata"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/test',
            merge_commit_sha='abc123',
            notes='This is a test merge with some notes'
        )
        self.assertEqual(merge_stats.notes,
                         'This is a test merge with some notes')

    def test_optional_pr_number(self):
        """Test that pr_number is optional"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/test',
            merge_commit_sha='abc123'
        )
        self.assertIsNone(merge_stats.pr_number)
