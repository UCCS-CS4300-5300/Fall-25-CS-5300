# Import Guide for Token Metrics

## Original Locations

The token metrics files have been reorganized but are still imported from their original locations in the Django app.

## Imports in Django App

### Models
```python
from active_interview_app.token_usage_models import TokenUsage
from active_interview_app.merge_stats_models import MergeTokenStats
```

### Utils
```python
from active_interview_app.token_tracker import track_openai_tokens, track_claude_tokens
from active_interview_app.openai_utils import get_openai_client, create_chat_completion
```

## Files Organization

This folder is a **copy** of token tracking files for organization purposes.
The actual files used by Django remain in `active_interview_backend/active_interview_app/`.

To fully migrate, you would need to:
1. Update all imports across the codebase
2. Update Django settings to recognize new app structure
3. Run migrations

For now, this serves as documentation and reference.
