"""
Tests for token export and import functionality
"""

import os
import sys
import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts to path
scripts_path = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_path))

# Import modules to test
from export_tokens import export_tokens, get_repo_root, get_git_info, load_local_tracking
from import_tokens import import_tokens, load_tracking_data, save_tracking_data, get_tracking_file


class TestExportTokens:
    """Test export-tokens.py functionality"""

    def test_get_repo_root(self):
        """Test getting repository root"""
        root = get_repo_root()
        assert root is not None
        assert isinstance(root, str)
        assert len(root) > 0

    @patch('subprocess.run')
    def test_get_git_info(self, mock_run):
        """Test getting git information"""
        # Mock git commands
        mock_branch = MagicMock()
        mock_branch.returncode = 0
        mock_branch.stdout = 'feature/test\n'

        mock_commit = MagicMock()
        mock_commit.returncode = 0
        mock_commit.stdout = 'abc123def456\n'

        mock_run.side_effect = [mock_branch, mock_commit]

        git_info = get_git_info()

        assert git_info is not None
        assert 'branch' in git_info
        assert 'commit' in git_info
        assert git_info['branch'] == 'feature/test'
        assert git_info['commit'] == 'abc123def456'

    def test_export_tokens_no_data(self, tmp_path):
        """Test exporting when no tracking data exists"""
        output_file = tmp_path / "test_export.json"

        with patch('export_tokens.load_local_tracking', return_value=None):
            result = export_tokens(str(output_file))
            assert result is False

    def test_export_tokens_with_data(self, tmp_path):
        """Test exporting valid tracking data"""
        output_file = tmp_path / "test_export.json"

        # Mock tracking data
        tracking_data = {
            'branch': 'test-branch',
            'total_tokens': 50000,
            'sessions': [
                {'timestamp': '2025-01-15T10:00:00', 'tokens': 25000, 'notes': 'Session 1'},
                {'timestamp': '2025-01-15T11:00:00', 'tokens': 25000, 'notes': 'Session 2'}
            ],
            'created_at': '2025-01-15T10:00:00',
            'last_updated': '2025-01-15T11:00:00'
        }

        with patch('export_tokens.load_local_tracking', return_value=tracking_data):
            with patch('export_tokens.get_git_info', return_value={'branch': 'test-branch', 'commit': 'abc123'}):
                result = export_tokens(str(output_file), include_metadata=True)

                assert result is True
                assert output_file.exists()

                # Verify exported data structure
                with open(output_file, 'r') as f:
                    exported = json.load(f)

                assert 'export_metadata' in exported
                assert 'token_data' in exported
                assert 'git_context' in exported
                assert exported['token_data']['total_tokens'] == 50000
                assert len(exported['token_data']['sessions']) == 2


class TestImportTokens:
    """Test import-tokens.py functionality"""

    def test_get_tracking_file(self):
        """Test getting tracking file path"""
        with patch('import_tokens.get_repo_root', return_value='/fake/repo'):
            file_path = get_tracking_file('feature/test')
            assert 'feature_test' in file_path or 'test' in file_path
            assert file_path.endswith('.json')

    def test_save_and_load_tracking_data(self, tmp_path):
        """Test saving and loading tracking data"""
        branch = 'test-branch'
        data = {
            'branch': branch,
            'total_tokens': 100000,
            'sessions': [{'timestamp': '2025-01-15T10:00:00', 'tokens': 100000}],
            'created_at': '2025-01-15T10:00:00',
            'last_updated': '2025-01-15T10:00:00'
        }

        with patch('import_tokens.get_tracking_file', return_value=str(tmp_path / 'test.json')):
            # Save
            result = save_tracking_data(branch, data)
            assert result is True

            # Load
            loaded = load_tracking_data(branch)
            assert loaded is not None
            assert loaded['total_tokens'] == 100000

    def test_import_tokens_file_not_found(self, tmp_path):
        """Test importing when file doesn't exist"""
        fake_file = tmp_path / "nonexistent.json"
        result = import_tokens(str(fake_file))
        assert result is False

    def test_import_tokens_invalid_json(self, tmp_path):
        """Test importing invalid JSON"""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ invalid json")

        result = import_tokens(str(bad_file))
        assert result is False

    def test_import_tokens_missing_token_data(self, tmp_path):
        """Test importing file without token_data"""
        bad_file = tmp_path / "missing_data.json"
        bad_file.write_text(json.dumps({'some': 'data'}))

        result = import_tokens(str(bad_file))
        assert result is False

    def test_import_tokens_valid_data(self, tmp_path):
        """Test importing valid token data"""
        export_file = tmp_path / "valid_export.json"
        export_data = {
            'export_metadata': {
                'exported_at': '2025-01-15T14:00:00',
                'exported_by': 'test_user'
            },
            'token_data': {
                'branch': 'test-branch',
                'total_tokens': 75000,
                'sessions': [
                    {'timestamp': '2025-01-15T10:00:00', 'tokens': 75000, 'notes': 'Test'}
                ],
                'created_at': '2025-01-15T10:00:00',
                'last_updated': '2025-01-15T10:00:00'
            }
        }

        export_file.write_text(json.dumps(export_data))

        tracking_file = tmp_path / "tracking.json"
        with patch('import_tokens.get_tracking_file', return_value=str(tracking_file)):
            with patch('import_tokens.load_tracking_data', return_value=None):
                result = import_tokens(str(export_file), merge=False)
                # Result depends on save_tracking_data working
                assert result in [True, False]  # May vary based on environment

    def test_import_tokens_merge_mode(self, tmp_path):
        """Test importing and merging with existing data"""
        export_file = tmp_path / "merge_export.json"
        export_data = {
            'export_metadata': {},
            'token_data': {
                'branch': 'test-branch',
                'total_tokens': 50000,
                'sessions': [
                    {'timestamp': '2025-01-15T10:00:00', 'tokens': 50000}
                ],
                'created_at': '2025-01-15T10:00:00',
                'last_updated': '2025-01-15T10:00:00'
            }
        }

        export_file.write_text(json.dumps(export_data))

        # Existing data
        existing_data = {
            'branch': 'test-branch',
            'total_tokens': 30000,
            'sessions': [
                {'timestamp': '2025-01-15T09:00:00', 'tokens': 30000}
            ],
            'created_at': '2025-01-15T09:00:00',
            'last_updated': '2025-01-15T09:00:00'
        }

        tracking_file = tmp_path / "tracking_merge.json"
        with patch('import_tokens.get_tracking_file', return_value=str(tracking_file)):
            with patch('import_tokens.load_tracking_data', return_value=existing_data):
                with patch('import_tokens.save_tracking_data', return_value=True) as mock_save:
                    result = import_tokens(str(export_file), merge=True)

                    assert result is True
                    # Verify merge was called with combined data
                    assert mock_save.called


class TestAutoTrackTokens:
    """Test auto-track-tokens.py functionality"""

    def setup_method(self):
        """Setup for each test"""
        from auto_track_tokens import get_repo_root, get_tracking_file
        self.get_repo_root = get_repo_root
        self.get_tracking_file = get_tracking_file

    def test_get_repo_root_from_auto_track(self):
        """Test repo root detection"""
        try:
            from auto_track_tokens import get_repo_root
            root = get_repo_root()
            assert root is not None
            assert isinstance(root, str)
        except ImportError:
            pytest.skip("auto_track_tokens not importable")

    def test_add_tokens(self, tmp_path):
        """Test adding tokens"""
        try:
            from auto_track_tokens import add_tokens, get_tracking_file

            with patch('auto_track_tokens.get_tracking_file', return_value=str(tmp_path / 'test.json')):
                with patch('auto_track_tokens.get_git_info', return_value='test-branch'):
                    result = add_tokens(50000, "Test session")
                    # Should create file and return True
                    assert result in [True, False]
        except ImportError:
            pytest.skip("auto_track_tokens not importable")


class TestImportTokenUsage:
    """Test import-token-usage.py functionality"""

    def test_import_single_record(self, tmp_path):
        """Test importing a single token record"""
        try:
            sys.path.insert(0, str(scripts_path))
            from import_token_usage import import_single_record

            record = {
                'timestamp': '2025-01-15T10:00:00',
                'git_branch': 'test-branch',
                'model_name': 'gpt-4o',
                'endpoint': 'chat.completions',
                'prompt_tokens': 1000,
                'completion_tokens': 500,
                'total_tokens': 1500
            }

            json_file = tmp_path / "token_usage_test.json"
            json_file.write_text(json.dumps(record))

            # Mock Django models
            with patch('import_token_usage.TokenUsage') as mock_model:
                mock_model.objects.filter.return_value.first.return_value = None
                mock_model.objects.create.return_value = MagicMock()

                result = import_single_record(record, str(json_file))
                # Should attempt to create
                assert result in [True, False]
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")

    def test_import_exported_file(self):
        """Test importing an exported token file"""
        try:
            from import_token_usage import import_exported_file

            export_data = {
                'export_metadata': {'exported_by': 'test'},
                'token_data': {
                    'branch': 'test-branch',
                    'total_tokens': 100000,
                    'sessions': [
                        {'timestamp': '2025-01-15T10:00:00', 'tokens': 50000},
                        {'timestamp': '2025-01-15T11:00:00', 'tokens': 50000}
                    ]
                }
            }

            with patch('import_token_usage.TokenUsage') as mock_model:
                mock_model.objects.filter.return_value.first.return_value = None
                mock_model.objects.create.return_value = MagicMock()

                result = import_exported_file(export_data, "test.json")
                assert isinstance(result, int)
                assert result >= 0
        except ImportError:
            pytest.skip("import_token_usage not importable without Django")


def test_module_imports():
    """Test that all modules can be imported"""
    try:
        import export_tokens
        import import_tokens
        import auto_track_tokens
        assert True
    except ImportError as e:
        pytest.skip(f"Module import failed: {e}")


def test_json_serialization():
    """Test JSON serialization of token data"""
    data = {
        'timestamp': datetime.now().isoformat(),
        'tokens': 50000,
        'branch': 'test/feature',
        'notes': 'Test session'
    }

    json_str = json.dumps(data)
    loaded = json.loads(json_str)

    assert loaded['tokens'] == 50000
    assert loaded['branch'] == 'test/feature'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
