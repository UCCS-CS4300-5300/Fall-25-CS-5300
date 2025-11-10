"""
Comprehensive tests for import-token-usage.py
Tests the enhanced token import with granular metadata capture
"""

import os
import sys
import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, call
from io import StringIO

# Add scripts to path
scripts_path = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_path))


class TestImportTokenUsageFromJsonFiles:
    """Test import_token_usage_from_json_files function"""

    @patch('import_token_usage.TokenUsage')
    @patch('import_token_usage.os.path.exists', return_value=False)
    def test_no_temp_directory(self, mock_exists, mock_token_usage):
        """Test when no temp directory exists"""
        try:
            from import_token_usage import import_token_usage_from_json_files

            result = import_token_usage_from_json_files()
            assert result == 0
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")

    @patch('import_token_usage.TokenUsage')
    @patch('import_token_usage.glob.glob', return_value=[])
    @patch('import_token_usage.os.path.exists', return_value=True)
    @patch('import_token_usage.os.path.abspath', return_value='/fake/temp')
    def test_no_json_files(self, mock_abspath, mock_exists, mock_glob, mock_token_usage):
        """Test when temp directory exists but has no JSON files"""
        try:
            from import_token_usage import import_token_usage_from_json_files

            result = import_token_usage_from_json_files()
            assert result == 0
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")

    @patch('import_token_usage.TokenUsage')
    @patch('import_token_usage.os.remove')
    @patch('import_token_usage.os.path.exists', return_value=True)
    @patch('import_token_usage.os.path.abspath', return_value='/fake/temp')
    def test_import_claude_local_format(self, mock_abspath, mock_exists, mock_remove, mock_token_usage):
        """Test importing Claude local tracking format"""
        try:
            from import_token_usage import import_token_usage_from_json_files

            # Mock JSON file
            json_file_path = '/fake/temp/claude_local_20250109_143045.json'
            json_content = json.dumps({
                'timestamp': '2025-01-09T14:30:45.000000',
                'git_branch': 'feature/test',
                'commit_sha': 'abc123def456',
                'model_name': 'claude-sonnet-4-5-20250929',
                'endpoint': 'messages',
                'prompt_tokens': 12000,
                'completion_tokens': 3000,
                'total_tokens': 15000,
                'source': 'local-claude-code',
                'notes': 'Test session'
            })

            with patch('import_token_usage.glob.glob', return_value=[json_file_path]):
                with patch('builtins.open', mock_open(read_data=json_content)):
                    # Mock TokenUsage query to simulate no duplicate
                    mock_token_usage.objects.filter.return_value.first.return_value = None
                    mock_token_usage.objects.create.return_value = MagicMock()

                    result = import_token_usage_from_json_files()

                    assert result == 1  # One record imported
                    mock_token_usage.objects.create.assert_called_once()
                    mock_remove.assert_called_once_with(json_file_path)
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")

    @patch('import_token_usage.TokenUsage')
    @patch('import_token_usage.os.remove')
    @patch('import_token_usage.os.path.exists', return_value=True)
    @patch('import_token_usage.os.path.abspath', return_value='/fake/temp')
    def test_import_ai_review_format(self, mock_abspath, mock_exists, mock_remove, mock_token_usage):
        """Test importing AI review token format"""
        try:
            from import_token_usage import import_token_usage_from_json_files

            json_file_path = '/fake/temp/token_usage_20250109.json'
            json_content = json.dumps({
                'timestamp': '2025-01-09T10:15:00.000000',
                'git_branch': 'main',
                'model_name': 'gpt-4-turbo',
                'endpoint': 'chat.completions',
                'prompt_tokens': 5000,
                'completion_tokens': 1500,
                'total_tokens': 6500
            })

            with patch('import_token_usage.glob.glob', return_value=[json_file_path]):
                with patch('builtins.open', mock_open(read_data=json_content)):
                    mock_token_usage.objects.filter.return_value.first.return_value = None
                    mock_token_usage.objects.create.return_value = MagicMock()

                    result = import_token_usage_from_json_files()

                    assert result == 1
                    mock_token_usage.objects.create.assert_called_once()
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")

    @patch('import_token_usage.TokenUsage')
    @patch('import_token_usage.os.path.exists', return_value=True)
    @patch('import_token_usage.os.path.abspath', return_value='/fake/temp')
    def test_skip_duplicate_records(self, mock_abspath, mock_exists, mock_token_usage):
        """Test skipping duplicate records"""
        try:
            from import_token_usage import import_token_usage_from_json_files

            json_file_path = '/fake/temp/duplicate.json'
            json_content = json.dumps({
                'timestamp': '2025-01-09T14:30:45.000000',
                'git_branch': 'feature/test',
                'model_name': 'claude-sonnet-4-5-20250929',
                'endpoint': 'messages',
                'prompt_tokens': 10000,
                'completion_tokens': 2500,
                'total_tokens': 12500
            })

            with patch('import_token_usage.glob.glob', return_value=[json_file_path]):
                with patch('builtins.open', mock_open(read_data=json_content)):
                    # Mock existing record (duplicate)
                    mock_token_usage.objects.filter.return_value.first.return_value = MagicMock()

                    result = import_token_usage_from_json_files()

                    assert result == 0  # No records imported (duplicate skipped)
                    mock_token_usage.objects.create.assert_not_called()
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")

    @patch('import_token_usage.TokenUsage')
    @patch('import_token_usage.os.path.exists', return_value=True)
    @patch('import_token_usage.os.path.abspath', return_value='/fake/temp')
    @patch('sys.stdout', new_callable=StringIO)
    def test_import_displays_metadata(self, mock_stdout, mock_abspath, mock_exists, mock_token_usage):
        """Test that import displays detailed metadata"""
        try:
            from import_token_usage import import_token_usage_from_json_files

            json_file_path = '/fake/temp/with_metadata.json'
            json_content = json.dumps({
                'timestamp': '2025-01-09T14:30:45.000000',
                'git_branch': 'feature/metadata',
                'commit_sha': 'def789ghi',
                'model_name': 'claude-sonnet-4-5-20250929',
                'endpoint': 'messages',
                'prompt_tokens': 10000,
                'completion_tokens': 2500,
                'total_tokens': 12500,
                'source': 'auto-tracked',
                'notes': 'Feature implementation'
            })

            with patch('import_token_usage.glob.glob', return_value=[json_file_path]):
                with patch('builtins.open', mock_open(read_data=json_content)):
                    with patch('import_token_usage.os.remove'):
                        mock_token_usage.objects.filter.return_value.first.return_value = None
                        mock_token_usage.objects.create.return_value = MagicMock()

                        import_token_usage_from_json_files()

                        output = mock_stdout.getvalue()
                        assert "Branch:" in output
                        assert "feature/metadata" in output
                        assert "Model:" in output
                        assert "Endpoint:" in output
                        assert "Tokens:" in output
                        assert "Cost:" in output
                        assert "Source:" in output
                        assert "auto-tracked" in output
                        assert "Notes:" in output
                        assert "Feature implementation" in output
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")

    @patch('import_token_usage.TokenUsage')
    @patch('import_token_usage.os.path.exists', return_value=True)
    @patch('import_token_usage.os.path.abspath', return_value='/fake/temp')
    def test_import_calculates_claude_cost(self, mock_abspath, mock_exists, mock_token_usage):
        """Test cost calculation for Claude model"""
        try:
            from import_token_usage import import_token_usage_from_json_files

            json_file_path = '/fake/temp/claude_cost.json'
            # 10K input + 5K output = (10 * 0.003) + (5 * 0.015) = $0.105
            json_content = json.dumps({
                'timestamp': '2025-01-09T14:30:45.000000',
                'git_branch': 'feature/test',
                'model_name': 'claude-sonnet-4-5-20250929',
                'endpoint': 'messages',
                'prompt_tokens': 10000,
                'completion_tokens': 5000,
                'total_tokens': 15000
            })

            with patch('import_token_usage.glob.glob', return_value=[json_file_path]):
                with patch('builtins.open', mock_open(read_data=json_content)):
                    with patch('import_token_usage.os.remove'):
                        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                            mock_token_usage.objects.filter.return_value.first.return_value = None
                            mock_token_usage.objects.create.return_value = MagicMock()

                            import_token_usage_from_json_files()

                            output = mock_stdout.getvalue()
                            assert "$0.105" in output or "$0.1050" in output
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")

    @patch('import_token_usage.TokenUsage')
    @patch('import_token_usage.os.path.exists', return_value=True)
    @patch('import_token_usage.os.path.abspath', return_value='/fake/temp')
    def test_import_calculates_gpt4_cost(self, mock_abspath, mock_exists, mock_token_usage):
        """Test cost calculation for GPT-4 model"""
        try:
            from import_token_usage import import_token_usage_from_json_files

            json_file_path = '/fake/temp/gpt4_cost.json'
            # 10K input + 5K output = (10 * 0.0025) + (5 * 0.01) = $0.075
            json_content = json.dumps({
                'timestamp': '2025-01-09T14:30:45.000000',
                'git_branch': 'feature/test',
                'model_name': 'gpt-4-turbo',
                'endpoint': 'chat.completions',
                'prompt_tokens': 10000,
                'completion_tokens': 5000,
                'total_tokens': 15000
            })

            with patch('import_token_usage.glob.glob', return_value=[json_file_path]):
                with patch('builtins.open', mock_open(read_data=json_content)):
                    with patch('import_token_usage.os.remove'):
                        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                            mock_token_usage.objects.filter.return_value.first.return_value = None
                            mock_token_usage.objects.create.return_value = MagicMock()

                            import_token_usage_from_json_files()

                            output = mock_stdout.getvalue()
                            assert "$0.075" in output or "$0.0750" in output
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")

    @patch('import_token_usage.TokenUsage')
    @patch('import_token_usage.os.remove')
    @patch('import_token_usage.os.path.exists', return_value=True)
    @patch('import_token_usage.os.path.abspath', return_value='/fake/temp')
    def test_import_export_format(self, mock_abspath, mock_exists, mock_remove, mock_token_usage):
        """Test importing exported token format"""
        try:
            from import_token_usage import import_token_usage_from_json_files

            json_file_path = '/fake/temp/exported_tokens.json'
            json_content = json.dumps({
                'token_data': {
                    'branch': 'feature/export-test',
                    'total_tokens': 50000,
                    'sessions': [
                        {
                            'timestamp': '2025-01-09T10:00:00',
                            'tokens': 25000,
                            'notes': 'Session 1'
                        },
                        {
                            'timestamp': '2025-01-09T11:00:00',
                            'tokens': 25000,
                            'notes': 'Session 2'
                        }
                    ],
                    'last_updated': '2025-01-09T11:00:00'
                }
            })

            with patch('import_token_usage.glob.glob', return_value=[json_file_path]):
                with patch('builtins.open', mock_open(read_data=json_content)):
                    mock_token_usage.objects.filter.return_value.first.return_value = None
                    mock_token_usage.objects.create.return_value = MagicMock()

                    result = import_token_usage_from_json_files()

                    assert result == 1  # Exported format imported as single record
                    mock_token_usage.objects.create.assert_called_once()
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")

    @patch('import_token_usage.TokenUsage')
    @patch('import_token_usage.os.path.exists', return_value=True)
    @patch('import_token_usage.os.path.abspath', return_value='/fake/temp')
    def test_import_handles_invalid_json(self, mock_abspath, mock_exists, mock_token_usage):
        """Test handling of invalid JSON files"""
        try:
            from import_token_usage import import_token_usage_from_json_files

            json_file_path = '/fake/temp/invalid.json'
            invalid_json = "{ invalid json content"

            with patch('import_token_usage.glob.glob', return_value=[json_file_path]):
                with patch('builtins.open', mock_open(read_data=invalid_json)):
                    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                        result = import_token_usage_from_json_files()

                        # Should handle error gracefully
                        assert result == 0
                        output = mock_stdout.getvalue()
                        assert "Error" in output or "failed" in output.lower()
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")

    @patch('import_token_usage.TokenUsage')
    @patch('import_token_usage.os.path.exists', return_value=True)
    @patch('import_token_usage.os.path.abspath', return_value='/fake/temp')
    def test_import_handles_unknown_format(self, mock_abspath, mock_exists, mock_token_usage):
        """Test handling of unknown file format"""
        try:
            from import_token_usage import import_token_usage_from_json_files

            json_file_path = '/fake/temp/unknown_format.json'
            json_content = json.dumps({
                'unknown': 'format',
                'missing': 'required_fields'
            })

            with patch('import_token_usage.glob.glob', return_value=[json_file_path]):
                with patch('builtins.open', mock_open(read_data=json_content)):
                    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                        result = import_token_usage_from_json_files()

                        # Should skip unknown format
                        assert result == 0
                        output = mock_stdout.getvalue()
                        assert "Unknown format" in output or "Skipped" in output
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")

    @patch('import_token_usage.TokenUsage')
    @patch('import_token_usage.os.remove')
    @patch('import_token_usage.os.path.exists', return_value=True)
    @patch('import_token_usage.os.path.abspath', return_value='/fake/temp')
    def test_import_multiple_files(self, mock_abspath, mock_exists, mock_remove, mock_token_usage):
        """Test importing multiple JSON files"""
        try:
            from import_token_usage import import_token_usage_from_json_files

            files = [
                '/fake/temp/file1.json',
                '/fake/temp/file2.json',
                '/fake/temp/file3.json'
            ]

            json_template = {
                'timestamp': '2025-01-09T14:30:45.000000',
                'git_branch': 'feature/multi',
                'model_name': 'claude-sonnet-4-5-20250929',
                'endpoint': 'messages',
                'prompt_tokens': 10000,
                'completion_tokens': 2500,
                'total_tokens': 12500
            }

            # Mock different file contents
            file_contents = {}
            for i, file_path in enumerate(files):
                json_data = json_template.copy()
                json_data['total_tokens'] = 10000 + (i * 1000)
                file_contents[file_path] = json.dumps(json_data)

            def open_side_effect(file, *args, **kwargs):
                return mock_open(read_data=file_contents.get(file, '{}'))()

            with patch('import_token_usage.glob.glob', return_value=files):
                with patch('builtins.open', side_effect=open_side_effect):
                    mock_token_usage.objects.filter.return_value.first.return_value = None
                    mock_token_usage.objects.create.return_value = MagicMock()

                    result = import_token_usage_from_json_files()

                    assert result == 3  # All three files imported
                    assert mock_token_usage.objects.create.call_count == 3
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")

    @patch('import_token_usage.TokenUsage')
    @patch('import_token_usage.os.path.exists', return_value=True)
    @patch('import_token_usage.os.path.abspath', return_value='/fake/temp')
    @patch('sys.stdout', new_callable=StringIO)
    def test_import_summary_output(self, mock_stdout, mock_abspath, mock_exists, mock_token_usage):
        """Test that import displays summary"""
        try:
            from import_token_usage import import_token_usage_from_json_files

            json_file_path = '/fake/temp/test.json'
            json_content = json.dumps({
                'timestamp': '2025-01-09T14:30:45.000000',
                'git_branch': 'feature/test',
                'model_name': 'claude-sonnet-4-5-20250929',
                'endpoint': 'messages',
                'prompt_tokens': 10000,
                'completion_tokens': 2500,
                'total_tokens': 12500
            })

            with patch('import_token_usage.glob.glob', return_value=[json_file_path]):
                with patch('builtins.open', mock_open(read_data=json_content)):
                    with patch('import_token_usage.os.remove'):
                        mock_token_usage.objects.filter.return_value.first.return_value = None
                        mock_token_usage.objects.create.return_value = MagicMock()

                        import_token_usage_from_json_files()

                        output = mock_stdout.getvalue()
                        assert "Import Summary" in output
                        assert "Imported:" in output
                        assert "Skipped:" in output
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")


class TestMainFunction:
    """Test main function execution"""

    @patch('import_token_usage.import_token_usage_from_json_files', return_value=5)
    @patch('sys.exit')
    def test_main_success(self, mock_exit, mock_import):
        """Test main function executes successfully"""
        try:
            from import_token_usage import main

            main()

            mock_import.assert_called_once()
            mock_exit.assert_called_once_with(0)
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")

    @patch('import_token_usage.import_token_usage_from_json_files', side_effect=Exception("Test error"))
    @patch('sys.exit')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_handles_exception(self, mock_stderr, mock_exit, mock_import):
        """Test main function handles exceptions"""
        try:
            from import_token_usage import main

            main()

            mock_exit.assert_called_once_with(1)
            assert "Error during import" in mock_stderr.getvalue()
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")


def test_module_importable():
    """Test that import_token_usage module can be imported"""
    try:
        import import_token_usage
        assert hasattr(import_token_usage, 'import_token_usage_from_json_files')
    except ImportError:
        pytest.skip("import_token_usage requires Django environment")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=import_token_usage', '--cov-report=term-missing'])
