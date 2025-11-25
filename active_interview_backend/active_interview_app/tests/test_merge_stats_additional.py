"""
Additional tests for merge_stats_models to improve coverage
"""
from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal

from active_interview_app.token_usage_models import TokenUsage
from active_interview_app.merge_stats_models import MergeTokenStats


class MergeTokenStatsEdgeCasesTest(TestCase):
    """Test edge cases and specific scenarios for MergeTokenStats"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_save_updates_existing_record_no_cumulative_change(self):
        """Test that updating existing record doesn't recalculate cumulative"""
        # Create initial record
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/test',
            merge_commit_sha='abc123',
            claude_prompt_tokens=1000,
            claude_completion_tokens=500,
            chatgpt_prompt_tokens=800,
            chatgpt_completion_tokens=400
        )

        initial_cumulative = merge_stats.cumulative_total_tokens
        initial_cost = merge_stats.cumulative_cost

        # Update the record
        merge_stats.claude_prompt_tokens = 1200
        merge_stats.save()

        # Cumulative should not change on update (only on creation)
        # But the token totals should update
        self.assertEqual(merge_stats.cumulative_total_tokens,
                         initial_cumulative)
        self.assertEqual(merge_stats.cumulative_cost, initial_cost)
        # Individual totals should update
        self.assertEqual(merge_stats.claude_total_tokens, 1700)  # 1200 + 500

    def test_branch_cost_with_zero_tokens(self):
        """Test branch_cost calculation with zero tokens"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/empty',
            merge_commit_sha='abc123empty',
            claude_prompt_tokens=0,
            claude_completion_tokens=0,
            chatgpt_prompt_tokens=0,
            chatgpt_completion_tokens=0
        )

        self.assertEqual(merge_stats.branch_cost, 0.0)

    def test_branch_cost_only_claude_tokens(self):
        """Test branch_cost with only Claude tokens"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/claude-only',
            merge_commit_sha='abc123claude',
            claude_prompt_tokens=2000,
            claude_completion_tokens=1000,
            chatgpt_prompt_tokens=0,
            chatgpt_completion_tokens=0
        )

        # Claude: (2000/1000 * 0.003) + (1000/1000 * 0.015) = 0.006 + 0.015 =
        # 0.021
        expected_cost = 0.021
        self.assertAlmostEqual(merge_stats.branch_cost,
                               expected_cost, places=4)

    def test_branch_cost_only_chatgpt_tokens(self):
        """Test branch_cost with only ChatGPT tokens"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/gpt-only',
            merge_commit_sha='abc123gpt',
            claude_prompt_tokens=0,
            claude_completion_tokens=0,
            chatgpt_prompt_tokens=2000,
            chatgpt_completion_tokens=1000
        )

        # ChatGPT: (2000/1000 * 0.03) + (1000/1000 * 0.06) = 0.06 + 0.06 = 0.12
        expected_cost = 0.12
        self.assertAlmostEqual(merge_stats.branch_cost,
                               expected_cost, places=4)

    def test_cumulative_cost_decimal_conversion(self):
        """Test that cumulative_cost properly converts from float"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/test',
            merge_commit_sha='abc123',
            claude_prompt_tokens=1000,
            claude_completion_tokens=500,
            chatgpt_prompt_tokens=800,
            chatgpt_completion_tokens=400
        )

        # Ensure cumulative_cost is a Decimal
        self.assertIsInstance(merge_stats.cumulative_cost, Decimal)
        self.assertGreater(merge_stats.cumulative_cost, 0)

    def test_create_from_branch_with_only_claude(self):
        """Test create_from_branch with only Claude tokens"""
        # Create only Claude token usage records
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/claude-test',
            model_name='claude-sonnet-4-5-20250929',
            endpoint='/v1/messages',
            prompt_tokens=500,
            completion_tokens=250
        )
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/claude-test',
            model_name='claude-3-opus-20240229',
            endpoint='/v1/messages',
            prompt_tokens=300,
            completion_tokens=150
        )

        merge_stats = MergeTokenStats.create_from_branch(
            branch_name='feature/claude-test',
            commit_sha='abc123claude',
        )

        self.assertEqual(merge_stats.claude_prompt_tokens, 800)
        self.assertEqual(merge_stats.claude_completion_tokens, 400)
        self.assertEqual(merge_stats.claude_request_count, 2)
        self.assertEqual(merge_stats.chatgpt_prompt_tokens, 0)
        self.assertEqual(merge_stats.chatgpt_completion_tokens, 0)
        self.assertEqual(merge_stats.chatgpt_request_count, 0)

    def test_create_from_branch_with_only_chatgpt(self):
        """Test create_from_branch with only ChatGPT tokens"""
        # Create only ChatGPT token usage records
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/gpt-test',
            model_name='gpt-4o',
            endpoint='/v1/chat/completions',
            prompt_tokens=600,
            completion_tokens=300
        )
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/gpt-test',
            model_name='gpt-4o-mini',
            endpoint='/v1/chat/completions',
            prompt_tokens=400,
            completion_tokens=200
        )

        merge_stats = MergeTokenStats.create_from_branch(
            branch_name='feature/gpt-test',
            commit_sha='abc123gpt',
        )

        self.assertEqual(merge_stats.chatgpt_prompt_tokens, 1000)
        self.assertEqual(merge_stats.chatgpt_completion_tokens, 500)
        self.assertEqual(merge_stats.chatgpt_request_count, 2)
        self.assertEqual(merge_stats.claude_prompt_tokens, 0)
        self.assertEqual(merge_stats.claude_completion_tokens, 0)
        self.assertEqual(merge_stats.claude_request_count, 0)

    def test_create_from_branch_with_null_aggregates(self):
        """Test that None values from aggregation are handled as 0"""
        # This is already tested in test_create_from_branch_no_tokens,
        # but let's be explicit about the Sum returning None
        merge_stats = MergeTokenStats.create_from_branch(
            branch_name='feature/nonexistent',
            commit_sha='abc123none',
            merged_by=self.user,
            pr_number=123
        )

        # All values should be 0 when there are no tokens
        self.assertEqual(merge_stats.claude_prompt_tokens, 0)
        self.assertEqual(merge_stats.claude_completion_tokens, 0)
        self.assertEqual(merge_stats.claude_request_count, 0)
        self.assertEqual(merge_stats.chatgpt_prompt_tokens, 0)
        self.assertEqual(merge_stats.chatgpt_completion_tokens, 0)
        self.assertEqual(merge_stats.chatgpt_request_count, 0)

    def test_get_breakdown_summary_with_cumulative(self):
        """Test get_breakdown_summary includes cumulative data"""
        # Create first merge
        merge1 = MergeTokenStats.objects.create(
            source_branch='feature/first',
            merge_commit_sha='abc111',
            claude_prompt_tokens=500,
            claude_completion_tokens=250,
            chatgpt_prompt_tokens=400,
            chatgpt_completion_tokens=200
        )

        # Create second merge
        merge2 = MergeTokenStats.objects.create(
            source_branch='feature/second',
            merge_commit_sha='abc222',
            claude_prompt_tokens=1000,
            claude_completion_tokens=500,
            chatgpt_prompt_tokens=800,
            chatgpt_completion_tokens=400
        )

        breakdown = merge2.get_breakdown_summary()

        # Check cumulative section exists and has correct values
        self.assertIn('cumulative', breakdown)
        self.assertEqual(
            breakdown['cumulative']['claude_tokens'],
            merge1.cumulative_claude_tokens + merge2.claude_total_tokens
        )
        self.assertIn('$', breakdown['cumulative']['cost'])

    def test_meta_options(self):
        """Test Meta class options are correctly set"""
        # Create some records to test ordering
        merge1 = MergeTokenStats.objects.create(
            source_branch='feature/first',
            merge_commit_sha='first123'
        )
        merge2 = MergeTokenStats.objects.create(
            source_branch='feature/second',
            merge_commit_sha='second123'
        )

        # Test verbose names
        self.assertEqual(
            MergeTokenStats._meta.verbose_name,
            "Merge Token Statistics"
        )
        self.assertEqual(
            MergeTokenStats._meta.verbose_name_plural,
            "Merge Token Statistics"
        )

        # Test default ordering (should be -merge_date)
        records = list(MergeTokenStats.objects.all())
        self.assertEqual(records[0].id, merge2.id)
        self.assertEqual(records[1].id, merge1.id)

    def test_indexes_exist(self):
        """Test that database indexes are defined"""
        indexes = MergeTokenStats._meta.indexes
        self.assertGreater(len(indexes), 0)

        # Check that source_branch and merge_date are indexed
        index_fields = [idx.fields for idx in indexes]
        self.assertIn(['source_branch'], index_fields)
        self.assertIn(['merge_date'], index_fields)

    def test_help_text_on_fields(self):
        """Test that important fields have help text"""
        source_branch_field = MergeTokenStats._meta.get_field('source_branch')
        self.assertIsNotNone(source_branch_field.help_text)

        merge_commit_sha_field = MergeTokenStats._meta.get_field(
            'merge_commit_sha')
        self.assertIsNotNone(merge_commit_sha_field.help_text)

        cumulative_total_field = MergeTokenStats._meta.get_field(
            'cumulative_total_tokens')
        self.assertIsNotNone(cumulative_total_field.help_text)

    def test_cascade_deletion_behavior(self):
        """Test that merged_by uses SET_NULL on deletion"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/test',
            merge_commit_sha='abc123cascade',
            merged_by=self.user
        )
        merge_id = merge_stats.id

        _user_id = self.user.id  # noqa: F841

        # Delete the user
        self.user.delete()

        # Merge stats should still exist but merged_by should be NULL
        merge_stats = MergeTokenStats.objects.get(id=merge_id)
        self.assertIsNone(merge_stats.merged_by)

    def test_large_token_values(self):
        """Test handling of very large token values"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/large',
            merge_commit_sha='abc123large',
            claude_prompt_tokens=1000000,
            claude_completion_tokens=500000,
            chatgpt_prompt_tokens=800000,
            chatgpt_completion_tokens=400000
        )

        # Verify calculations work with large numbers
        self.assertEqual(merge_stats.claude_total_tokens, 1500000)
        self.assertEqual(merge_stats.chatgpt_total_tokens, 1200000)
        self.assertEqual(merge_stats.total_tokens, 2700000)

        # Verify cost calculation works
        self.assertGreater(merge_stats.branch_cost, 0)

    def test_pr_number_optional(self):
        """Test that pr_number can be null and blank"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/no-pr',
            merge_commit_sha='abc123nopr'
        )

        self.assertIsNone(merge_stats.pr_number)

        # Also test with explicit None
        merge_stats2 = MergeTokenStats.objects.create(
            source_branch='feature/no-pr2',
            merge_commit_sha='abc123nopr2',
            pr_number=None
        )

        self.assertIsNone(merge_stats2.pr_number)

    def test_notes_field_blank(self):
        """Test that notes field can be blank"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/no-notes',
            merge_commit_sha='abc123nonotes'
        )

        self.assertEqual(merge_stats.notes, '')

    def test_merge_date_auto_now_add(self):
        """Test that merge_date is automatically set"""
        from django.utils import timezone

        before = timezone.now()
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/auto-date',
            merge_commit_sha='abc123autodate'
        )
        after = timezone.now()

        self.assertIsNotNone(merge_stats.merge_date)
        self.assertGreaterEqual(merge_stats.merge_date, before)
        self.assertLessEqual(merge_stats.merge_date, after)

    def test_str_with_different_date_formats(self):
        """Test __str__ method formats date correctly"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/str-test',
            target_branch='develop',
            merge_commit_sha='abc123str',
            claude_prompt_tokens=1000,
            claude_completion_tokens=500
        )

        str_repr = str(merge_stats)

        # Should contain key information
        self.assertIn('feature/str-test', str_repr)
        self.assertIn('develop', str_repr)
        self.assertIn('tokens', str_repr)
        # Should contain formatted date
        date_str = merge_stats.merge_date.strftime('%Y-%m-%d')
        self.assertIn(date_str, str_repr)

    def test_cumulative_sequence_with_three_merges(self):
        """Test cumulative totals across three sequential merges"""
        # First merge
        merge1 = MergeTokenStats.objects.create(
            source_branch='feature/one',
            merge_commit_sha='one123',
            claude_prompt_tokens=100,
            claude_completion_tokens=50,
            chatgpt_prompt_tokens=80,
            chatgpt_completion_tokens=40
        )

        # Second merge
        merge2 = MergeTokenStats.objects.create(
            source_branch='feature/two',
            merge_commit_sha='two123',
            claude_prompt_tokens=200,
            claude_completion_tokens=100,
            chatgpt_prompt_tokens=160,
            chatgpt_completion_tokens=80
        )

        # Third merge
        merge3 = MergeTokenStats.objects.create(
            source_branch='feature/three',
            merge_commit_sha='three123',
            claude_prompt_tokens=300,
            claude_completion_tokens=150,
            chatgpt_prompt_tokens=240,
            chatgpt_completion_tokens=120
        )

        # Verify cumulative progression
        self.assertEqual(merge1.cumulative_total_tokens, 270)  # 150 + 120
        self.assertEqual(merge2.cumulative_total_tokens, 810)  # 270 + 540
        self.assertEqual(merge3.cumulative_total_tokens, 1620)  # 810 + 810

    def test_field_max_lengths(self):
        """Test that char fields have appropriate max lengths"""
        source_field = MergeTokenStats._meta.get_field('source_branch')
        self.assertEqual(source_field.max_length, 255)

        target_field = MergeTokenStats._meta.get_field('target_branch')
        self.assertEqual(target_field.max_length, 255)

        sha_field = MergeTokenStats._meta.get_field('merge_commit_sha')
        self.assertEqual(sha_field.max_length, 40)

    def test_cumulative_cost_decimal_places(self):
        """Test cumulative_cost has correct decimal configuration"""
        cost_field = MergeTokenStats._meta.get_field('cumulative_cost')
        self.assertEqual(cost_field.max_digits, 10)
        self.assertEqual(cost_field.decimal_places, 2)

    def test_create_from_branch_with_mixed_models(self):
        """Test create_from_branch aggregates Claude and ChatGPT tokens properly"""
        # Create mixed token usage records
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/mixed',
            model_name='claude-sonnet-4',
            endpoint='/v1/messages',
            prompt_tokens=100,
            completion_tokens=50
        )
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/mixed',
            model_name='gpt-4o',
            endpoint='/v1/chat/completions',
            prompt_tokens=200,
            completion_tokens=100
        )

        merge_stats = MergeTokenStats.create_from_branch(
            branch_name='feature/mixed',
            commit_sha='abc123mixed',
            merged_by=self.user,
            pr_number=456
        )

        # Check Claude tokens
        self.assertEqual(merge_stats.claude_prompt_tokens, 100)
        self.assertEqual(merge_stats.claude_completion_tokens, 50)
        self.assertEqual(merge_stats.claude_request_count, 1)

        # Check ChatGPT tokens
        self.assertEqual(merge_stats.chatgpt_prompt_tokens, 200)
        self.assertEqual(merge_stats.chatgpt_completion_tokens, 100)
        self.assertEqual(merge_stats.chatgpt_request_count, 1)

        # Check totals
        self.assertEqual(merge_stats.total_prompt_tokens, 300)
        self.assertEqual(merge_stats.total_completion_tokens, 150)
        self.assertEqual(merge_stats.total_tokens, 450)
        self.assertEqual(merge_stats.request_count, 2)

        # Check user and PR number were set
        self.assertEqual(merge_stats.merged_by, self.user)
        self.assertEqual(merge_stats.pr_number, 456)

    def test_get_breakdown_summary_structure(self):
        """Test that get_breakdown_summary returns all expected keys and structure"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/structure-test',
            merge_commit_sha='abc123structure',
            claude_prompt_tokens=100,
            claude_completion_tokens=50,
            claude_request_count=2,
            chatgpt_prompt_tokens=200,
            chatgpt_completion_tokens=100,
            chatgpt_request_count=3
        )

        breakdown = merge_stats.get_breakdown_summary()

        # Check top-level keys
        self.assertIn('branch', breakdown)
        self.assertIn('merge_date', breakdown)
        self.assertIn('claude', breakdown)
        self.assertIn('chatgpt', breakdown)
        self.assertIn('totals', breakdown)
        self.assertIn('cumulative', breakdown)

        # Check Claude section
        self.assertIn('prompt_tokens', breakdown['claude'])
        self.assertIn('completion_tokens', breakdown['claude'])
        self.assertIn('total_tokens', breakdown['claude'])
        self.assertIn('requests', breakdown['claude'])

        # Check ChatGPT section
        self.assertIn('prompt_tokens', breakdown['chatgpt'])
        self.assertIn('completion_tokens', breakdown['chatgpt'])
        self.assertIn('total_tokens', breakdown['chatgpt'])
        self.assertIn('requests', breakdown['chatgpt'])

        # Check totals section
        self.assertIn('prompt_tokens', breakdown['totals'])
        self.assertIn('completion_tokens', breakdown['totals'])
        self.assertIn('total_tokens', breakdown['totals'])
        self.assertIn('requests', breakdown['totals'])
        self.assertIn('cost', breakdown['totals'])

        # Check cumulative section
        self.assertIn('claude_tokens', breakdown['cumulative'])
        self.assertIn('chatgpt_tokens', breakdown['cumulative'])
        self.assertIn('total_tokens', breakdown['cumulative'])
        self.assertIn('cost', breakdown['cumulative'])

    def test_branch_cost_with_large_values(self):
        """Test branch_cost calculation with large token values"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/large-cost',
            merge_commit_sha='abc123largecost',
            claude_prompt_tokens=1000000,
            claude_completion_tokens=500000,
            chatgpt_prompt_tokens=1000000,
            chatgpt_completion_tokens=500000
        )

        # Claude: (1000000/1000 * 0.003) + (500000/1000 * 0.015) = 3 + 7.5 = 10.5
        # ChatGPT: (1000000/1000 * 0.03) + (500000/1000 * 0.06) = 30 + 30 = 60
        # Total: 70.5
        expected_cost = 70.5
        self.assertAlmostEqual(merge_stats.branch_cost,
                               expected_cost, places=2)

    def test_unique_constraint_on_merge_commit_sha(self):
        """Test that duplicate merge_commit_sha raises IntegrityError"""
        from django.db import IntegrityError

        MergeTokenStats.objects.create(
            source_branch='feature/unique1',
            merge_commit_sha='uniquesha123',
            claude_prompt_tokens=100,
            claude_completion_tokens=50
        )

        with self.assertRaises(IntegrityError):
            MergeTokenStats.objects.create(
                source_branch='feature/unique2',
                merge_commit_sha='uniquesha123',
                claude_prompt_tokens=200,
                claude_completion_tokens=100
            )

    def test_str_includes_arrow_between_branches(self):
        """Test that __str__ method includes arrow notation between branches"""
        merge_stats = MergeTokenStats.objects.create(
            source_branch='feature/arrow-test',
            target_branch='develop',
            merge_commit_sha='abc123arrow'
        )

        str_repr = str(merge_stats)
        self.assertIn('→', str_repr)
        self.assertIn('feature/arrow-test', str_repr)
        self.assertIn('develop', str_repr)
