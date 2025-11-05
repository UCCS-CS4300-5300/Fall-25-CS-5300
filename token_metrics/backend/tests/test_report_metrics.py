"""
Tests for report-token-metrics.py
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta

# Add scripts to path
scripts_path = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_path))


class TestReportTokenMetrics:
    """Test report-token-metrics.py functionality"""

    @patch('subprocess.run')
    def test_get_git_info(self, mock_run):
        """Test getting git information for report"""
        try:
            from report_token_metrics import get_git_info

            # Mock git commands
            mock_branch = MagicMock()
            mock_branch.returncode = 0
            mock_branch.stdout = 'feature/api\n'

            mock_commit = MagicMock()
            mock_commit.returncode = 0
            mock_commit.stdout = 'abc123def456\n'

            mock_run.side_effect = [mock_branch, mock_commit]

            git_info = get_git_info()

            assert git_info is not None
            assert 'source_branch' in git_info
            assert 'commit_sha' in git_info
            assert git_info['source_branch'] == 'feature/api'
            assert git_info['commit_sha'] == 'abc123def456'

        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    def test_format_cost(self):
        """Test cost formatting"""
        try:
            from report_token_metrics import format_cost

            assert format_cost(0.1234) == "$0.1234"
            assert format_cost(1.5) == "$1.5000"
            assert format_cost(0) == "$0.0000"
            assert format_cost(100.9999) == "$100.9999"

        except ImportError:
            pytest.skip("report_token_metrics not importable")

    @patch('report_token_metrics.TokenUsage')
    def test_print_branch_summary(self, mock_token_usage):
        """Test printing branch summary"""
        try:
            from report_token_metrics import print_branch_summary

            # Mock branch summary data
            mock_summary = {
                'total_requests': 50,
                'total_tokens': 125000,
                'total_cost': 0.375,
                'by_model': {
                    'claude-sonnet-4-5': {
                        'requests': 30,
                        'prompt_tokens': 80000,
                        'completion_tokens': 20000,
                        'total_tokens': 100000,
                        'cost': 0.300
                    },
                    'gpt-4o': {
                        'requests': 20,
                        'prompt_tokens': 20000,
                        'completion_tokens': 5000,
                        'total_tokens': 25000,
                        'cost': 0.075
                    }
                }
            }

            mock_token_usage.get_branch_summary.return_value = mock_summary

            result = print_branch_summary('test-branch')

            assert result is not None
            assert result['total_requests'] == 50
            assert result['total_tokens'] == 125000

        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    @patch('report_token_metrics.TokenUsage')
    def test_print_all_branches_breakdown(self, mock_token_usage):
        """Test printing breakdown by all branches"""
        try:
            from report_token_metrics import print_all_branches_breakdown

            # Mock branches
            mock_token_usage.objects.values_list.return_value.distinct.return_value.order_by.return_value = [
                'main',
                'feature/api',
                'bugfix/auth'
            ]

            # Mock summaries for each branch
            def get_summary_side_effect(branch):
                summaries = {
                    'main': {'total_requests': 50, 'total_tokens': 100000, 'total_cost': 0.30},
                    'feature/api': {'total_requests': 30, 'total_tokens': 75000, 'total_cost': 0.22},
                    'bugfix/auth': {'total_requests': 20, 'total_tokens': 50000, 'total_cost': 0.15}
                }
                return summaries.get(branch, {'total_requests': 0, 'total_tokens': 0, 'total_cost': 0})

            mock_token_usage.get_branch_summary.side_effect = get_summary_side_effect

            # Should not raise exception
            print_all_branches_breakdown()

        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    @patch('report_token_metrics.TokenUsage')
    def test_print_recent_activity(self, mock_token_usage):
        """Test printing recent activity"""
        try:
            from report_token_metrics import print_recent_activity

            # Mock recent records
            mock_record = MagicMock()
            mock_record.created_at = datetime.now()
            mock_record.model_name = 'gpt-4o'
            mock_record.total_tokens = 5000
            mock_record.estimated_cost = 0.015

            mock_token_usage.objects.filter.return_value.order_by.return_value.__getitem__.return_value = [
                mock_record
            ]

            # Should not raise exception
            print_recent_activity('test-branch', days=7)

        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    @patch('report_token_metrics.MergeTokenStats')
    def test_print_cumulative_stats(self, mock_merge_stats):
        """Test printing cumulative statistics"""
        try:
            from report_token_metrics import print_cumulative_stats

            # Mock merge stats
            mock_latest = MagicMock()
            mock_latest.cumulative_total_tokens = 500000
            mock_latest.cumulative_cost = 1.50
            mock_latest.cumulative_claude_tokens = 400000
            mock_latest.cumulative_chatgpt_tokens = 100000

            mock_merge_stats.objects.all.return_value.order_by.return_value.exists.return_value = True
            mock_merge_stats.objects.all.return_value.order_by.return_value.first.return_value = mock_latest
            mock_merge_stats.objects.all.return_value.order_by.return_value.count.return_value = 25

            # Should not raise exception
            print_cumulative_stats()

        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    def test_print_comparison_summary(self):
        """Test branch comparison"""
        try:
            from report_token_metrics import print_comparison_summary
            from report_token_metrics import TokenUsage

            with patch.object(TokenUsage, 'get_branch_summary') as mock_summary:
                mock_summary.side_effect = [
                    {'total_requests': 50, 'total_tokens': 100000, 'total_cost': 0.30},
                    {'total_requests': 40, 'total_tokens': 80000, 'total_cost': 0.24}
                ]

                # Should not raise exception
                print_comparison_summary('feature/test', 'main')

        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")


class TestReportIntegration:
    """Integration tests for the report system"""

    def test_report_handles_no_data(self):
        """Test report gracefully handles no data"""
        try:
            from report_token_metrics import print_branch_summary
            from report_token_metrics import TokenUsage

            with patch.object(TokenUsage, 'get_branch_summary') as mock_summary:
                mock_summary.return_value = {
                    'total_requests': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0,
                    'by_model': {}
                }

                result = print_branch_summary('empty-branch')
                assert result['total_requests'] == 0

        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    def test_report_handles_large_numbers(self):
        """Test report handles large token counts"""
        try:
            from report_token_metrics import format_cost

            # Test with large numbers
            cost = 1234.5678
            formatted = format_cost(cost)
            assert "$" in formatted
            assert "1234.5678" in formatted

        except ImportError:
            pytest.skip("report_token_metrics not importable")

    @patch('report_token_metrics.get_git_info')
    @patch('report_token_metrics.TokenUsage')
    def test_main_report_execution(self, mock_token_usage, mock_git_info):
        """Test main report function executes"""
        try:
            from report_token_metrics import main

            # Mock git info
            mock_git_info.return_value = {
                'source_branch': 'test-branch',
                'target_branch': 'main',
                'commit_sha': 'abc123'
            }

            # Mock summary
            mock_token_usage.get_branch_summary.return_value = {
                'total_requests': 10,
                'total_tokens': 50000,
                'total_cost': 0.15,
                'by_model': {}
            }

            # Mock branches
            mock_token_usage.objects.values_list.return_value.distinct.return_value.order_by.return_value = []

            # Should execute without error
            # Note: May raise SystemExit, so we catch it
            try:
                main()
            except SystemExit:
                pass

        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")


def test_module_import():
    """Test that report module can be imported"""
    try:
        import report_token_metrics
        assert hasattr(report_token_metrics, 'format_cost')
        assert hasattr(report_token_metrics, 'get_git_info')
    except ImportError:
        pytest.skip("report_token_metrics requires Django")


def test_cost_calculation_precision():
    """Test cost calculations maintain precision"""
    try:
        from report_token_metrics import format_cost

        test_cases = [
            (0.0001, "$0.0001"),
            (0.9999, "$0.9999"),
            (10.5555, "$10.5555"),
            (99.9999, "$99.9999")
        ]

        for input_cost, expected in test_cases:
            result = format_cost(input_cost)
            assert result == expected

    except ImportError:
        pytest.skip("report_token_metrics not importable")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
