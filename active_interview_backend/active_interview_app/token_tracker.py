"""
Token Tracker - Compatibility Import
ECHO is off.
This file provides backward compatibility for imports.
The actual module has moved to token_metrics/backend/utils/
"""

import sys
from pathlib import Path

# Add token_metrics to path
token_metrics_path = Path(__file__).parent.parent.parent / 'token_metrics' / 'backend' / 'utils'
sys.path.insert(0, str(token_metrics_path))

# Import from new location
try:
    from token_tracker import *  # noqa
except ImportError:
    raise ImportError(
        "Token tracker has been moved to token_metrics/backend/utils/. "
        "Please update your imports to: from token_metrics.backend.utils import track_openai_tokens"
    )
