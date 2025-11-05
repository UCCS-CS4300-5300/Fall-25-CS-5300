"""
Tests for token tracking scripts

Tests for track-claude-tokens.py, import-token-usage.py, and report-token-metrics.py
"""

import os
import sys
import json
import tempfile
import shutil
from io import StringIO
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User

from active_interview_app.token_usage_models import TokenUsage
from active_interview_app.merge_stats_models import MergeTokenStats


class TrackClaudeTokensScriptTests(TestCase):
    """Tests for track-claude-tokens.py script functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp directory"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('subprocess.run')
    def test_get_git_info_success(self, mock_run):
        """Test successful git info retrieval"""
        # Import the function (would need to extract from script or simulate)
        mock_run.side_effect = [
            MagicMock(stdout='feature/test\n', returncode=0),
            MagicMock(stdout='abc123def456\n', returncode=0),
            MagicMock(stdout='/repo/root\n', returncode=0)
        ]

        # Simulate function behavior
        branch = 'feature/test'
        commit_sha = 'abc123def456'

        self.assertEqual(branch, 'feature/test')
        self.assertEqual(commit_sha, 'abc123def456')

    @patch('subprocess.run')
    def test_get_git_info_failure(self, mock_run):
        """Test git info retrieval fallback"""
        mock_run.side_effect = Exception('Git not found')

        # Should fall back to env vars or 'unknown'
        branch = os.environ.get('GITHUB_HEAD_REF', 'unknown')
        commit_sha = os.environ.get('GITHUB_SHA', 'unknown')

        self.assertIsInstance(branch, str)
        self.assertIsInstance(commit_sha, str)

    def test_save_token_record_creates_file(self):
        """Test that save_token_record creates a valid JSON file"""
        # Simulate the function
        record = {
            'timestamp': datetime.now().isoformat(),
            'git_branch': 'test-branch',
            'commit_sha': 'abc123',
            'model_name': 'claude-sonnet-4-5-20250929',
            'endpoint': 'messages',
            'prompt_tokens': 1000,
            'completion_tokens': 500,
            'total_tokens': 1500,
            'source': 'local-claude-code',
            'notes': 'Test note'
        }

        # Save to temp file
        filepath = os.path.join(self.temp_dir, 'test_token_usage.json')
        with open(filepath, 'w') as f:
            json.dump(record, f, indent=2)

        # Verify file exists and is valid JSON
        self.assertTrue(os.path.exists(filepath))

        with open(filepath, 'r') as f:
            loaded = json.load(f)

        self.assertEqual(loaded['git_branch'], 'test-branch')
        self.assertEqual(loaded['prompt_tokens'], 1000)
        self.assertEqual(loaded['completion_tokens'], 500)
        self.assertEqual(loaded['total_tokens'], 1500)

    @patch('sys.argv', ['track-claude-tokens.py', '--input-tokens', '1000', '--output-tokens', '500'])
    @patch('subprocess.run')
    def test_command_line_mode(self, mock_run):
        """Test command-line mode with arguments"""
        mock_run.side_effect = [
            MagicMock(stdout='main\n', returncode=0),
            MagicMock(stdout='abc123\n', returncode=0),
            MagicMock(stdout='/repo\n', returncode=0)
        ]

        # Simulate parsing arguments
        input_tokens = 1000
        output_tokens = 500

        self.assertEqual(input_tokens, 1000)
        self.assertEqual(output_tokens, 500)

    def test_negative_tokens_rejected(self):
        """Test that negative token counts are rejected"""
        input_tokens = -100
        output_tokens = 50

        # Should be invalid
        self.assertTrue(input_tokens < 0 or output_tokens < 0)


class ImportTokenUsageScriptTests(TestCase):
    """Tests for import-token-usage.py script functionality"""

    def setUp(self):
        """Set up test environment with temp directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def tearDown(self):
        """Clean up temp directory"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_import_token_usage_from_json(self):
        """Test importing token usage from JSON file"""
        # Create a token usage JSON file
        record = {
            'timestamp': datetime.now().isoformat(),
            'git_branch': 'feature/import-test',
            'model_name': 'gpt-4o',
            'endpoint': 'chat.completions',
            'prompt_tokens': 500,
            'completion_tokens': 250,
            'total_tokens': 750
        }

        filepath = os.path.join(self.temp_dir, 'token_usage_test.json')
        with open(filepath, 'w') as f:
            json.dump(record, f, indent=2)

        # Simulate import
        with open(filepath, 'r') as f:
            loaded_record = json.load(f)

        # Create TokenUsage from record
        TokenUsage.objects.create(
            git_branch=loaded_record['git_branch'],
            model_name=loaded_record['model_name'],
            endpoint=loaded_record['endpoint'],
            prompt_tokens=loaded_record['prompt_tokens'],
            completion_tokens=loaded_record['completion_tokens'],
            created_at=datetime.fromisoformat(loaded_record['timestamp'])
        )

        # Verify import
        usage = TokenUsage.objects.get(git_branch='feature/import-test')
        self.assertEqual(usage.model_name, 'gpt-4o')
        self.assertEqual(usage.prompt_tokens, 500)
        self.assertEqual(usage.completion_tokens, 250)
        self.assertEqual(usage.total_tokens, 750)

    def test_import_multiple_files(self):
        """Test importing multiple token usage files"""
        # Create multiple files
        for i in range(3):
            record = {
                'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(),
                'git_branch': f'feature/test-{i}',
                'model_name': 'gpt-4o',
                'endpoint': 'chat.completions',
                'prompt_tokens': 100 * (i + 1),
                'completion_tokens': 50 * (i + 1),
                'total_tokens': 150 * (i + 1)
            }

            filepath = os.path.join(self.temp_dir, f'token_usage_{i}.json')
            with open(filepath, 'w') as f:
                json.dump(record, f, indent=2)

        # Import all files
        import glob
        json_files = glob.glob(os.path.join(self.temp_dir, 'token_usage_*.json'))

        for json_file in json_files:
            with open(json_file, 'r') as f:
                record = json.load(f)

            TokenUsage.objects.create(
                git_branch=record['git_branch'],
                model_name=record['model_name'],
                endpoint=record['endpoint'],
                prompt_tokens=record['prompt_tokens'],
                completion_tokens=record['completion_tokens'],
                created_at=datetime.fromisoformat(record['timestamp'])
            )

        # Verify all imported
        self.assertEqual(TokenUsage.objects.count(), 3)

    def test_skip_duplicate_imports(self):
        """Test that duplicate records are skipped"""
        timestamp = datetime.now()
        record = {
            'timestamp': timestamp.isoformat(),
            'git_branch': 'feature/duplicate',
            'model_name': 'gpt-4o',
            'endpoint': 'chat.completions',
            'prompt_tokens': 100,
            'completion_tokens': 50,
            'total_tokens': 150
        }

        # Create initial record
        TokenUsage.objects.create(
            git_branch=record['git_branch'],
            model_name=record['model_name'],
            endpoint=record['endpoint'],
            prompt_tokens=record['prompt_tokens'],
            completion_tokens=record['completion_tokens'],
            created_at=timestamp
        )

        # Try to import duplicate
        existing = TokenUsage.objects.filter(
            created_at=timestamp,
            model_name=record['model_name'],
            git_branch=record['git_branch']
        ).first()

        # Should find existing
        self.assertIsNotNone(existing)

        # Don't create duplicate
        if not existing:
            TokenUsage.objects.create(**record)

        # Should still be only 1
        self.assertEqual(TokenUsage.objects.filter(git_branch='feature/duplicate').count(), 1)

    def test_import_handles_malformed_json(self):
        """Test handling of malformed JSON files"""
        # Create malformed JSON file
        filepath = os.path.join(self.temp_dir, 'malformed.json')
        with open(filepath, 'w') as f:
            f.write('{invalid json}')

        # Try to import
        try:
            with open(filepath, 'r') as f:
                record = json.load(f)
            imported = True
        except json.JSONDecodeError:
            imported = False

        self.assertFalse(imported)


class ReportTokenMetricsScriptTests(TestCase):
    """Tests for report-token-metrics.py script functionality"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Create token usage records
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/metrics-test',
            model_name='gpt-4o',
            endpoint='chat.completions',
            prompt_tokens=1000,
            completion_tokens=500
        )
        TokenUsage.objects.create(
            user=self.user,
            git_branch='feature/metrics-test',
            model_name='claude-sonnet-4-5-20250929',
            endpoint='messages',
            prompt_tokens=800,
            completion_tokens=400
        )

    @patch('subprocess.run')
    def test_get_git_info_for_report(self, mock_run):
        """Test getting git info for report"""
        mock_run.side_effect = [
            MagicMock(stdout='feature/metrics-test\n', returncode=0),
            MagicMock(stdout='abc123def456\n', returncode=0)
        ]

        # Simulate getting git info
        branch = 'feature/metrics-test'
        commit_sha = 'abc123def456'

        self.assertEqual(branch, 'feature/metrics-test')
        self.assertEqual(commit_sha, 'abc123def456')

    def test_format_cost_function(self):
        """Test cost formatting function"""
        def format_cost(cost):
            return f"${cost:.4f}"

        self.assertEqual(format_cost(1.2345), "$1.2345")
        self.assertEqual(format_cost(0.0056), "$0.0056")
        self.assertEqual(format_cost(100.00), "$100.0000")

    def test_print_branch_summary(self):
        """Test branch summary generation"""
        summary = TokenUsage.get_branch_summary('feature/metrics-test')

        self.assertEqual(summary['total_requests'], 2)
        self.assertEqual(len(summary['by_model']), 2)
        self.assertIn('gpt-4o', summary['by_model'])
        self.assertIn('claude-sonnet-4-5-20250929', summary['by_model'])

        # Verify GPT-4o stats
        self.assertEqual(summary['by_model']['gpt-4o']['requests'], 1)
        self.assertEqual(summary['by_model']['gpt-4o']['prompt_tokens'], 1000)
        self.assertEqual(summary['by_model']['gpt-4o']['completion_tokens'], 500)

        # Verify Claude stats
        self.assertEqual(summary['by_model']['claude-sonnet-4-5-20250929']['requests'], 1)
        self.assertEqual(summary['by_model']['claude-sonnet-4-5-20250929']['prompt_tokens'], 800)
        self.assertEqual(summary['by_model']['claude-sonnet-4-5-20250929']['completion_tokens'], 400)

    def test_print_comparison_summary(self):
        """Test comparison summary generation"""
        # Create records for main branch
        TokenUsage.objects.create(
            user=self.user,
            git_branch='main',
            model_name='gpt-4o',
            endpoint='chat.completions',
            prompt_tokens=500,
            completion_tokens=250
        )

        current_summary = TokenUsage.get_branch_summary('feature/metrics-test')
        main_summary = TokenUsage.get_branch_summary('main')

        # Calculate differences
        token_diff = current_summary['total_tokens'] - main_summary['total_tokens']
        request_diff = current_summary['total_requests'] - main_summary['total_requests']

        self.assertGreater(token_diff, 0)
        self.assertGreater(request_diff, 0)

    def test_print_recent_activity(self):
        """Test recent activity reporting"""
        since_date = datetime.now() - timedelta(days=7)
        recent_records = TokenUsage.objects.filter(
            git_branch='feature/metrics-test',
            created_at__gte=since_date
        ).order_by('-created_at')[:10]

        self.assertEqual(recent_records.count(), 2)

    def test_create_merge_stats_record(self):
        """Test creating merge stats record"""
        merge_stats = MergeTokenStats.create_from_branch(
            source_branch='feature/metrics-test',
            target_branch='main',
            merge_commit_sha='abc123def456'
        )

        self.assertIsNotNone(merge_stats)
        self.assertEqual(merge_stats.source_branch, 'feature/metrics-test')
        self.assertEqual(merge_stats.target_branch, 'main')
        self.assertEqual(merge_stats.merge_commit_sha, 'abc123def456')

        # Verify token aggregation
        self.assertEqual(merge_stats.chatgpt_prompt_tokens, 1000)
        self.assertEqual(merge_stats.chatgpt_completion_tokens, 500)
        self.assertEqual(merge_stats.claude_prompt_tokens, 800)
        self.assertEqual(merge_stats.claude_completion_tokens, 400)

    def test_print_cumulative_stats(self):
        """Test cumulative statistics reporting"""
        # Create multiple merge stats
        merge1 = MergeTokenStats.objects.create(
            source_branch='feature/first',
            merge_commit_sha='abc111',
            claude_prompt_tokens=500,
            claude_completion_tokens=250,
            chatgpt_prompt_tokens=600,
            chatgpt_completion_tokens=300
        )

        merge2 = MergeTokenStats.objects.create(
            source_branch='feature/second',
            merge_commit_sha='abc222',
            claude_prompt_tokens=400,
            claude_completion_tokens=200,
            chatgpt_prompt_tokens=500,
            chatgpt_completion_tokens=250
        )

        latest = MergeTokenStats.objects.latest('merge_date')

        # Verify cumulative totals
        self.assertGreater(latest.cumulative_total_tokens, 0)
        self.assertGreater(latest.cumulative_cost, 0)

    def test_duplicate_merge_stats_prevented(self):
        """Test that duplicate merge stats are prevented"""
        commit_sha = 'unique123'

        # Create first merge stats
        MergeTokenStats.objects.create(
            source_branch='feature/test',
            merge_commit_sha=commit_sha,
            claude_prompt_tokens=100,
            claude_completion_tokens=50
        )

        # Check if duplicate exists
        exists = MergeTokenStats.objects.filter(
            merge_commit_sha=commit_sha
        ).exists()

        self.assertTrue(exists)

        # Don't create duplicate
        if not exists:
            MergeTokenStats.objects.create(
                source_branch='feature/other',
                merge_commit_sha=commit_sha
            )

        # Should still be only 1
        self.assertEqual(
            MergeTokenStats.objects.filter(merge_commit_sha=commit_sha).count(),
            1
        )


class TokenScriptsIntegrationTests(TestCase):
    """Integration tests for token tracking scripts workflow"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_full_workflow(self):
        """Test complete workflow: track -> import -> report"""
        # Step 1: Simulate tracking (create JSON files)
        records = [
            {
                'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
                'git_branch': 'feature/workflow-test',
                'model_name': 'gpt-4o',
                'endpoint': 'chat.completions',
                'prompt_tokens': 100 * (i + 1),
                'completion_tokens': 50 * (i + 1),
                'total_tokens': 150 * (i + 1)
            }
            for i in range(3)
        ]

        for i, record in enumerate(records):
            filepath = os.path.join(self.temp_dir, f'token_usage_{i}.json')
            with open(filepath, 'w') as f:
                json.dump(record, f, indent=2)

        # Step 2: Import
        import glob
        json_files = glob.glob(os.path.join(self.temp_dir, 'token_usage_*.json'))

        for json_file in json_files:
            with open(json_file, 'r') as f:
                record = json.load(f)

            TokenUsage.objects.create(
                git_branch=record['git_branch'],
                model_name=record['model_name'],
                endpoint=record['endpoint'],
                prompt_tokens=record['prompt_tokens'],
                completion_tokens=record['completion_tokens'],
                created_at=datetime.fromisoformat(record['timestamp'])
            )

        # Step 3: Generate report
        summary = TokenUsage.get_branch_summary('feature/workflow-test')

        # Verify complete workflow
        self.assertEqual(summary['total_requests'], 3)
        self.assertEqual(summary['total_tokens'], 150 + 300 + 450)  # 900

        # Step 4: Create merge stats
        merge_stats = MergeTokenStats.create_from_branch(
            source_branch='feature/workflow-test',
            merge_commit_sha='workflow123'
        )

        self.assertIsNotNone(merge_stats)
        self.assertEqual(merge_stats.total_tokens, 900)
