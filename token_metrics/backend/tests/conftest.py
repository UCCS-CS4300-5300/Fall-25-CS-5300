"""
Pytest configuration for token metrics tests
"""

import os
import sys
import pytest
from pathlib import Path

# Add necessary paths
repo_root = Path(__file__).parent.parent.parent.parent
scripts_path = Path(__file__).parent.parent.parent / 'scripts'
backend_path = Path(__file__).parent.parent.parent.parent / 'active_interview_backend'

sys.path.insert(0, str(scripts_path))
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(repo_root))


@pytest.fixture(scope="session")
def django_db_setup():
    """Setup Django database for tests"""
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'active_interview_project.settings')
        import django
        django.setup()
    except Exception as e:
        pytest.skip(f"Django setup failed: {e}")


@pytest.fixture
def mock_git_repo(tmp_path):
    """Create a mock git repository"""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()
    return repo_dir


@pytest.fixture
def sample_token_data():
    """Sample token tracking data"""
    return {
        'branch': 'test-branch',
        'total_tokens': 100000,
        'sessions': [
            {
                'timestamp': '2025-01-15T10:00:00',
                'tokens': 50000,
                'notes': 'Session 1'
            },
            {
                'timestamp': '2025-01-15T11:00:00',
                'tokens': 50000,
                'notes': 'Session 2'
            }
        ],
        'created_at': '2025-01-15T10:00:00',
        'last_updated': '2025-01-15T11:00:00'
    }


@pytest.fixture
def sample_export_data():
    """Sample exported token data"""
    return {
        'export_metadata': {
            'exported_at': '2025-01-15T14:00:00',
            'exported_by': 'test_user',
            'export_version': '1.0',
            'source_machine': 'TEST-MACHINE'
        },
        'token_data': {
            'branch': 'test-branch',
            'total_tokens': 125000,
            'sessions': [
                {
                    'timestamp': '2025-01-15T10:00:00',
                    'tokens': 75000,
                    'notes': 'Development'
                },
                {
                    'timestamp': '2025-01-15T12:00:00',
                    'tokens': 50000,
                    'notes': 'Testing'
                }
            ],
            'created_at': '2025-01-15T10:00:00',
            'last_updated': '2025-01-15T12:00:00'
        },
        'git_context': {
            'branch': 'test-branch',
            'commit': 'abc123def456'
        }
    }


@pytest.fixture
def sample_token_usage_record():
    """Sample token usage record for import"""
    return {
        'timestamp': '2025-01-15T10:00:00',
        'git_branch': 'test-branch',
        'model_name': 'gpt-4o',
        'endpoint': 'chat.completions',
        'prompt_tokens': 5000,
        'completion_tokens': 1500,
        'total_tokens': 6500
    }
