"""
Comprehensive tests for report-token-metrics.py
Tests the enhanced granular statistics reporting functionality
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
from datetime import datetime, timedelta
from io import StringIO

# Add scripts to path
scripts_path = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_path))


class TestGetCurrentBranch:
    """Test get_current_branch function"""

    @patch('os.environ.get')
    def test_get_branch_from_github_head_ref(self, mock_env_get):
        """Test getting branch from GITHUB_HEAD_REF environment variable"""
        try:
            from report_token_metrics import get_current_branch

            mock_env_get.side_effect = lambda key: 'feature/test' if key == 'GITHUB_HEAD_REF' else None

            branch = get_current_branch()
            assert branch == 'feature/test'
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    @patch('os.environ.get')
    def test_get_branch_from_github_ref_name(self, mock_env_get):
        """Test getting branch from GITHUB_REF_NAME environment variable"""
        try:
            from report_token_metrics import get_current_branch

            mock_env_get.side_effect = lambda key: 'main' if key == 'GITHUB_REF_NAME' else None

            branch = get_current_branch()
            assert branch == 'main'
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    @patch('subprocess.run')
    @patch('os.environ.get', return_value=None)
    def test_get_branch_from_git_command(self, mock_env, mock_run):
        """Test getting branch from git command"""
        try:
            from report_token_metrics import get_current_branch

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = 'feature/api\n'
            mock_run.return_value = mock_result

            branch = get_current_branch()
            assert branch == 'feature/api'
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    @patch('subprocess.run', side_effect=Exception("Git not found"))
    @patch('os.environ.get', return_value=None)
    def test_get_branch_fallback_to_unknown(self, mock_env, mock_run):
        """Test fallback to 'unknown' when git fails"""
        try:
            from report_token_metrics import get_current_branch

            branch = get_current_branch()
            assert branch == 'unknown'
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")


class TestFormatNumber:
    """Test format_number function"""

    def test_format_zero(self):
        """Test formatting zero"""
        try:
            from report_token_metrics import format_number
            assert format_number(0) == "0"
        except ImportError:
            pytest.skip("report_token_metrics not importable")

    def test_format_none(self):
        """Test formatting None"""
        try:
            from report_token_metrics import format_number
            assert format_number(None) == "0"
        except ImportError:
            pytest.skip("report_token_metrics not importable")

    def test_format_small_number(self):
        """Test formatting small numbers"""
        try:
            from report_token_metrics import format_number
            assert format_number(999) == "999"
        except ImportError:
            pytest.skip("report_token_metrics not importable")

    def test_format_thousands(self):
        """Test formatting thousands with comma"""
        try:
            from report_token_metrics import format_number
            assert format_number(1234) == "1,234"
        except ImportError:
            pytest.skip("report_token_metrics not importable")

    def test_format_millions(self):
        """Test formatting millions"""
        try:
            from report_token_metrics import format_number
            assert format_number(1234567) == "1,234,567"
        except ImportError:
            pytest.skip("report_token_metrics not importable")


class TestCalculateCost:
    """Test calculate_cost function"""

    def test_calculate_claude_sonnet_45_cost(self):
        """Test cost calculation for Claude Sonnet 4.5"""
        try:
            from report_token_metrics import calculate_cost

            # 10K input + 5K output = (10 * 3) + (5 * 15) = $0.105
            cost = calculate_cost(10000, 5000, 'claude-sonnet-4-5-20250929')
            assert abs(cost - 0.105) < 0.001
        except ImportError:
            pytest.skip("report_token_metrics not importable")

    def test_calculate_claude_sonnet_35_cost(self):
        """Test cost calculation for Claude Sonnet 3.5"""
        try:
            from report_token_metrics import calculate_cost

            cost = calculate_cost(10000, 5000, 'claude-sonnet-3-5-20241022')
            assert abs(cost - 0.105) < 0.001
        except ImportError:
            pytest.skip("report_token_metrics not importable")

    def test_calculate_gpt4_cost(self):
        """Test cost calculation for GPT-4"""
        try:
            from report_token_metrics import calculate_cost

            # 10K input + 5K output = (10 * 2.5) + (5 * 10) = $0.075
            cost = calculate_cost(10000, 5000, 'gpt-4-turbo')
            assert abs(cost - 0.075) < 0.001
        except ImportError:
            pytest.skip("report_token_metrics not importable")

    def test_calculate_gpt35_cost(self):
        """Test cost calculation for GPT-3.5"""
        try:
            from report_token_metrics import calculate_cost

            # 10K input + 5K output = (10 * 0.5) + (5 * 1.5) = $0.0125
            cost = calculate_cost(10000, 5000, 'gpt-3.5-turbo')
            assert abs(cost - 0.0125) < 0.001
        except ImportError:
            pytest.skip("report_token_metrics not importable")

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens"""
        try:
            from report_token_metrics import calculate_cost

            cost = calculate_cost(0, 0, 'claude-sonnet-4-5-20250929')
            assert cost == 0.0
        except ImportError:
            pytest.skip("report_token_metrics not importable")

    def test_calculate_cost_none_tokens(self):
        """Test cost calculation with None tokens"""
        try:
            from report_token_metrics import calculate_cost

            cost = calculate_cost(None, None, 'claude-sonnet-4-5-20250929')
            assert cost == 0.0
        except ImportError:
            pytest.skip("report_token_metrics not importable")

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation for unknown model uses default pricing"""
        try:
            from report_token_metrics import calculate_cost

            # Should use Claude pricing as default
            cost = calculate_cost(10000, 5000, 'unknown-model')
            assert abs(cost - 0.105) < 0.001
        except ImportError:
            pytest.skip("report_token_metrics not importable")


class TestGenerateReportNoData:
    """Test generate_report function with no data"""

    @patch('report_token_metrics.TokenUsage')
    @patch('report_token_metrics.get_current_branch', return_value='test-branch')
    @patch('sys.stdout', new_callable=StringIO)
    def test_report_with_no_records(self, mock_stdout, mock_get_branch, mock_token_usage):
        """Test report displays appropriate message when no data exists"""
        try:
            from report_token_metrics import generate_report

            mock_token_usage.objects.count.return_value = 0

            generate_report()

            output = mock_stdout.getvalue()
            assert "No token usage data found" in output
            assert "Quick Start" in output
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")


class TestGenerateReportWithData:
    """Test generate_report function with data"""

    def setup_method(self):
        """Setup mock data for tests"""
        self.mock_total_stats = {
            'total_tokens': 542680,
            'total_prompt': 434144,
            'total_completion': 108536,
            'avg_tokens': 4272,
            'max_tokens': 67450,
            'min_tokens': 1240,
            'count': 127
        }

        self.mock_branch_stats = {
            'total_tokens': 67450,
            'total_prompt': 53960,
            'total_completion': 13490,
            'avg_tokens': 4497,
            'count': 15,
            'first_use': datetime(2025, 1, 7, 10, 30, 15),
            'last_use': datetime(2025, 1, 9, 16, 45, 30)
        }

    @patch('report_token_metrics.TokenUsage')
    @patch('report_token_metrics.get_current_branch', return_value='feature/test')
    @patch('report_token_metrics.timezone')
    @patch('sys.stdout', new_callable=StringIO)
    def test_report_overall_statistics(self, mock_stdout, mock_timezone, mock_get_branch, mock_token_usage):
        """Test report displays overall statistics section"""
        try:
            from report_token_metrics import generate_report

            mock_token_usage.objects.count.return_value = 127
            mock_token_usage.objects.aggregate.return_value = self.mock_total_stats
            mock_token_usage.objects.filter.return_value.aggregate.return_value = {'count': 0}
            mock_token_usage.objects.filter.return_value.extra.return_value.values.return_value.annotate.return_value.order_by.return_value = []
            mock_token_usage.objects.values.return_value.annotate.return_value.order_by.return_value = []
            mock_token_usage.objects.select_related.return_value.order_by.return_value = []

            mock_timezone.now.return_value = datetime(2025, 1, 9, 16, 0, 0)

            generate_report()

            output = mock_stdout.getvalue()
            assert "OVERALL STATISTICS" in output
            assert "542,680" in output  # Total tokens formatted
            assert "434,144" in output  # Prompt tokens
            assert "108,536" in output  # Completion tokens
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    @patch('report_token_metrics.TokenUsage')
    @patch('report_token_metrics.get_current_branch', return_value='feature/test')
    @patch('report_token_metrics.timezone')
    @patch('sys.stdout', new_callable=StringIO)
    def test_report_current_branch_section(self, mock_stdout, mock_timezone, mock_get_branch, mock_token_usage):
        """Test report displays current branch statistics"""
        try:
            from report_token_metrics import generate_report

            mock_token_usage.objects.count.return_value = 127
            mock_token_usage.objects.aggregate.return_value = self.mock_total_stats

            # Mock branch records
            mock_branch_records = MagicMock()
            mock_branch_records.aggregate.return_value = self.mock_branch_stats
            mock_branch_records.extra.return_value.values.return_value.annotate.return_value.order_by.return_value = [
                {'day': '2025-01-09', 'tokens': 22100, 'count': 5}
            ]
            mock_token_usage.objects.filter.return_value = mock_branch_records

            mock_token_usage.objects.values.return_value.annotate.return_value.order_by.return_value = []
            mock_token_usage.objects.select_related.return_value.order_by.return_value = []

            mock_timezone.now.return_value = datetime(2025, 1, 9, 16, 0, 0)

            generate_report()

            output = mock_stdout.getvalue()
            assert "CURRENT BRANCH: feature/test" in output
            assert "67,450" in output  # Branch total tokens
            assert "Daily Activity on This Branch" in output
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    @patch('report_token_metrics.TokenUsage')
    @patch('report_token_metrics.get_current_branch', return_value='feature/test')
    @patch('report_token_metrics.timezone')
    @patch('sys.stdout', new_callable=StringIO)
    def test_report_time_based_analysis(self, mock_stdout, mock_timezone, mock_get_branch, mock_token_usage):
        """Test report displays time-based analysis"""
        try:
            from report_token_metrics import generate_report

            now = datetime(2025, 1, 9, 16, 0, 0)
            mock_timezone.now.return_value = now

            mock_token_usage.objects.count.return_value = 127
            mock_token_usage.objects.aggregate.return_value = self.mock_total_stats

            # Mock different time period queries
            def filter_side_effect(*args, **kwargs):
                mock_result = MagicMock()
                if 'created_at__gte' in kwargs:
                    # Last 24 hours, 7 days, 30 days queries
                    mock_result.aggregate.return_value = {
                        'total_tokens': 32100,
                        'total_prompt': 25680,
                        'total_completion': 6420,
                        'count': 7
                    }
                else:
                    mock_result.aggregate.return_value = {'count': 0}
                mock_result.extra.return_value.values.return_value.annotate.return_value.order_by.return_value = []
                return mock_result

            mock_token_usage.objects.filter.side_effect = filter_side_effect
            mock_token_usage.objects.values.return_value.annotate.return_value.order_by.return_value = []
            mock_token_usage.objects.select_related.return_value.order_by.return_value = []

            generate_report()

            output = mock_stdout.getvalue()
            assert "TIME-BASED ANALYSIS" in output
            assert "Last 24 Hours" in output
            assert "Last 7 Days" in output
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    @patch('report_token_metrics.TokenUsage')
    @patch('report_token_metrics.get_current_branch', return_value='main')
    @patch('report_token_metrics.timezone')
    @patch('sys.stdout', new_callable=StringIO)
    def test_report_branch_breakdown(self, mock_stdout, mock_timezone, mock_get_branch, mock_token_usage):
        """Test report displays branch breakdown"""
        try:
            from report_token_metrics import generate_report

            mock_token_usage.objects.count.return_value = 127
            mock_token_usage.objects.aggregate.return_value = self.mock_total_stats
            mock_token_usage.objects.filter.return_value.aggregate.return_value = {'count': 0}
            mock_token_usage.objects.filter.return_value.extra.return_value.values.return_value.annotate.return_value.order_by.return_value = []

            # Mock branch breakdown
            mock_token_usage.objects.values.return_value.annotate.return_value.order_by.return_value = [
                {
                    'git_branch': 'feature/scoring',
                    'total_tokens': 67450,
                    'prompt_tokens': 53960,
                    'completion_tokens': 13490,
                    'count': 15,
                    'last_used': datetime(2025, 1, 9)
                },
                {
                    'git_branch': 'main',
                    'total_tokens': 38100,
                    'prompt_tokens': 30480,
                    'completion_tokens': 7620,
                    'count': 18,
                    'last_used': datetime(2025, 1, 8)
                }
            ]

            mock_token_usage.objects.select_related.return_value.order_by.return_value = []
            mock_timezone.now.return_value = datetime(2025, 1, 9, 16, 0, 0)

            generate_report()

            output = mock_stdout.getvalue()
            assert "BRANCH BREAKDOWN" in output
            assert "feature/scoring" in output
            assert "67,450" in output
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    @patch('report_token_metrics.TokenUsage')
    @patch('report_token_metrics.get_current_branch', return_value='main')
    @patch('report_token_metrics.timezone')
    @patch('sys.stdout', new_callable=StringIO)
    def test_report_model_analysis(self, mock_stdout, mock_timezone, mock_get_branch, mock_token_usage):
        """Test report displays model and endpoint analysis"""
        try:
            from report_token_metrics import generate_report

            mock_token_usage.objects.count.return_value = 127
            mock_token_usage.objects.aggregate.return_value = self.mock_total_stats
            mock_token_usage.objects.filter.return_value.aggregate.return_value = {'count': 0}
            mock_token_usage.objects.filter.return_value.extra.return_value.values.return_value.annotate.return_value.order_by.return_value = []

            # Mock values() to return different results based on the field
            def values_side_effect(*args):
                mock_result = MagicMock()
                annotate_result = MagicMock()

                if 'git_branch' in args:
                    # Branch breakdown
                    annotate_result.order_by.return_value = []
                elif 'model_name' in args:
                    # Model breakdown
                    annotate_result.order_by.return_value = [
                        {
                            'model_name': 'claude-sonnet-4-5-20250929',
                            'total_tokens': 485120,
                            'prompt_tokens': 388096,
                            'completion_tokens': 97024,
                            'count': 110
                        }
                    ]
                elif 'endpoint' in args:
                    # Endpoint breakdown
                    annotate_result.order_by.return_value = [
                        {
                            'endpoint': 'messages',
                            'total_tokens': 425680,
                            'count': 95,
                            'avg_tokens': 4481
                        }
                    ]

                mock_result.annotate.return_value = annotate_result
                return mock_result

            mock_token_usage.objects.values.side_effect = values_side_effect
            mock_token_usage.objects.select_related.return_value.order_by.return_value = []
            mock_timezone.now.return_value = datetime(2025, 1, 9, 16, 0, 0)

            generate_report()

            output = mock_stdout.getvalue()
            assert "MODEL & ENDPOINT ANALYSIS" in output
            assert "claude-sonnet-4-5" in output
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    @patch('report_token_metrics.TokenUsage')
    @patch('report_token_metrics.get_current_branch', return_value='main')
    @patch('report_token_metrics.timezone')
    @patch('sys.stdout', new_callable=StringIO)
    def test_report_recent_activity(self, mock_stdout, mock_timezone, mock_get_branch, mock_token_usage):
        """Test report displays recent activity"""
        try:
            from report_token_metrics import generate_report

            mock_token_usage.objects.count.return_value = 127
            mock_token_usage.objects.aggregate.return_value = self.mock_total_stats
            mock_token_usage.objects.filter.return_value.aggregate.return_value = {'count': 0}
            mock_token_usage.objects.filter.return_value.extra.return_value.values.return_value.annotate.return_value.order_by.return_value = []
            mock_token_usage.objects.values.return_value.annotate.return_value.order_by.return_value = []

            # Mock recent records
            mock_record = MagicMock()
            mock_record.created_at = datetime(2025, 1, 9, 16, 45, 30)
            mock_record.git_branch = 'feature/scoring'
            mock_record.model_name = 'claude-sonnet-4-5-20250929'
            mock_record.endpoint = 'messages'
            mock_record.total_tokens = 22100
            mock_record.prompt_tokens = 17680
            mock_record.completion_tokens = 4420

            mock_token_usage.objects.select_related.return_value.order_by.return_value = [mock_record]
            mock_timezone.now.return_value = datetime(2025, 1, 9, 16, 0, 0)

            generate_report()

            output = mock_stdout.getvalue()
            assert "RECENT ACTIVITY" in output
            assert "feature/scoring" in output
            assert "22,100" in output
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    @patch('report_token_metrics.TokenUsage')
    @patch('report_token_metrics.get_current_branch', return_value='main')
    @patch('report_token_metrics.timezone')
    @patch('sys.stdout', new_callable=StringIO)
    def test_report_cost_analysis(self, mock_stdout, mock_timezone, mock_get_branch, mock_token_usage):
        """Test report displays detailed cost analysis"""
        try:
            from report_token_metrics import generate_report

            mock_token_usage.objects.count.return_value = 127
            mock_token_usage.objects.aggregate.return_value = self.mock_total_stats
            mock_token_usage.objects.filter.return_value.aggregate.return_value = {'count': 0}
            mock_token_usage.objects.filter.return_value.extra.return_value.values.return_value.annotate.return_value.order_by.return_value = []
            mock_token_usage.objects.select_related.return_value.order_by.return_value = []

            # Mock for values() to return model breakdown
            def values_side_effect(*args):
                mock_result = MagicMock()
                annotate_result = MagicMock()

                if 'model_name' in args:
                    annotate_result.order_by.return_value = [
                        {
                            'model_name': 'claude-sonnet-4-5-20250929',
                            'total_tokens': 485120,
                            'prompt_tokens': 388096,
                            'completion_tokens': 97024,
                            'count': 110
                        }
                    ]
                else:
                    annotate_result.order_by.return_value = []

                mock_result.annotate.return_value = annotate_result
                return mock_result

            mock_token_usage.objects.values.side_effect = values_side_effect
            mock_timezone.now.return_value = datetime(2025, 1, 9, 16, 0, 0)

            generate_report()

            output = mock_stdout.getvalue()
            assert "DETAILED COST ANALYSIS" in output
            assert "Prompt:" in output
            assert "Completion:" in output
            assert "TOTAL ESTIMATED COST" in output
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    @patch('report_token_metrics.TokenUsage')
    @patch('report_token_metrics.get_current_branch', return_value='main')
    @patch('report_token_metrics.timezone')
    @patch('sys.stdout', new_callable=StringIO)
    def test_report_insights_section(self, mock_stdout, mock_timezone, mock_get_branch, mock_token_usage):
        """Test report displays insights and recommendations"""
        try:
            from report_token_metrics import generate_report

            now = datetime(2025, 1, 9, 16, 0, 0)
            mock_timezone.now.return_value = now

            mock_token_usage.objects.count.return_value = 127
            mock_token_usage.objects.aggregate.return_value = self.mock_total_stats
            mock_token_usage.objects.filter.return_value.aggregate.return_value = {'count': 0}
            mock_token_usage.objects.filter.return_value.extra.return_value.values.return_value.annotate.return_value.order_by.return_value = []
            mock_token_usage.objects.select_related.return_value.order_by.return_value = []

            # Mock branch breakdown for insights
            def values_side_effect(*args):
                mock_result = MagicMock()
                annotate_result = MagicMock()

                if 'git_branch' in args:
                    annotate_result.order_by.return_value = [
                        {
                            'git_branch': 'feature/expensive',
                            'total_tokens': 100000,
                            'prompt_tokens': 80000,
                            'completion_tokens': 20000,
                            'count': 20,
                            'last_used': now
                        }
                    ]
                else:
                    annotate_result.order_by.return_value = []

                mock_result.annotate.return_value = annotate_result
                return mock_result

            mock_token_usage.objects.values.side_effect = values_side_effect

            generate_report()

            output = mock_stdout.getvalue()
            assert "INSIGHTS & RECOMMENDATIONS" in output
            assert "Most Active Branch" in output
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")


class TestMainFunction:
    """Test main function execution"""

    @patch('report_token_metrics.generate_report')
    @patch('sys.exit')
    def test_main_success(self, mock_exit, mock_generate):
        """Test main function executes successfully"""
        try:
            from report_token_metrics import main

            mock_generate.return_value = None
            main()

            mock_generate.assert_called_once()
            mock_exit.assert_called_once_with(0)
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")

    @patch('report_token_metrics.generate_report', side_effect=Exception("Test error"))
    @patch('sys.exit')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_handles_exception(self, mock_stderr, mock_exit, mock_generate):
        """Test main function handles exceptions"""
        try:
            from report_token_metrics import main

            main()

            mock_exit.assert_called_once_with(1)
            assert "Error generating report" in mock_stderr.getvalue()
        except ImportError:
            pytest.skip("report_token_metrics not importable without Django")


def test_module_importable():
    """Test that report_token_metrics module can be imported"""
    try:
        import report_token_metrics
        assert hasattr(report_token_metrics, 'get_current_branch')
        assert hasattr(report_token_metrics, 'format_number')
        assert hasattr(report_token_metrics, 'calculate_cost')
        assert hasattr(report_token_metrics, 'generate_report')
    except ImportError:
        pytest.skip("report_token_metrics requires Django environment")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=report_token_metrics', '--cov-report=term-missing'])
