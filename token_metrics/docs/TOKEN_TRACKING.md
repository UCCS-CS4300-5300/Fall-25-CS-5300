# Token Usage Tracking System

This document explains how to use and maintain the token usage tracking system for Claude and OpenAI API calls.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Components](#components)
4. [Usage Guide](#usage-guide)
5. [CI/CD Integration](#cicd-integration)
6. [Database Models](#database-models)
7. [Cost Tracking](#cost-tracking)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The token tracking system automatically monitors and reports API usage from:
- **Claude API** (used via Claude Code locally)
- **OpenAI API** (used in application and CI/CD)

### Key Features

✅ Automatic token tracking for API calls
✅ Git branch attribution
✅ Cost estimation
✅ Merge-time reporting in CI/CD
✅ Local usage tracking via git hooks
✅ Historical trend analysis

---

## Quick Start

### 1. Install Git Hooks (for Local Claude Code Tracking)

**On Windows:**
```bash
cd scripts
.\install-git-hooks.bat
```

**On macOS/Linux:**
```bash
cd scripts
chmod +x install-git-hooks.sh
./install-git-hooks.sh
```

### 2. Track Claude Code Usage

After making a commit with Claude Code:

1. You'll be prompted: `Track tokens? (y/N)`
2. Check the Claude Code UI (bottom right) for token counts
3. Enter the input and output token counts
4. The usage is saved automatically

**Manual Tracking:**
```bash
python scripts/track-claude-tokens.py --interactive
```

Or with specific counts:
```bash
python scripts/track-claude-tokens.py --input-tokens 5000 --output-tokens 2000
```

### 3. View Token Reports

Reports are automatically generated when merging to `main` in the CI/CD pipeline. You can also generate reports manually:

```bash
cd scripts
python report-token-metrics.py
```

---

## Components

### 1. Database Models

#### `TokenUsage` Model
Located in: `active_interview_app/token_usage_models.py`

Tracks individual API calls with:
- `created_at`: Timestamp
- `user`: Django user (if available)
- `git_branch`: Git branch name
- `model_name`: AI model (e.g., `gpt-4o`, `claude-sonnet-4-5-20250929`)
- `endpoint`: API endpoint called
- `prompt_tokens`: Input tokens
- `completion_tokens`: Output tokens
- `total_tokens`: Total tokens (auto-calculated)
- `estimated_cost`: Calculated cost in USD

#### `MergeTokenStats` Model
Located in: `active_interview_app/merge_stats_models.py`

Aggregates token usage per merge:
- `merge_date`: When merged
- `source_branch`: Branch being merged
- `target_branch`: Target branch (usually `main`)
- `merge_commit_sha`: Git commit SHA
- `merged_by`: User who merged
- Per-model token counts and costs
- Cumulative all-time totals

### 2. Tracking Infrastructure

#### Token Tracker Module
File: `active_interview_app/token_tracker.py`

Provides decorators and utilities:

**Decorators:**
```python
from active_interview_app.token_tracker import track_openai_tokens, track_claude_tokens

@track_openai_tokens(endpoint="chat.completions")
def my_openai_call():
    response = client.chat.completions.create(...)
    return response

@track_claude_tokens(endpoint="messages")
def my_claude_call():
    response = anthropic_client.messages.create(...)
    return response
```

**Manual Tracking:**
```python
from active_interview_app.token_tracker import manual_track_tokens

manual_track_tokens(
    model_name="gpt-4o",
    endpoint="chat.completions",
    prompt_tokens=1000,
    completion_tokens=500,
    user=request.user  # Optional
)
```

#### OpenAI Wrapper
File: `active_interview_app/openai_utils.py`

Provides a wrapped API call with automatic tracking:

```python
from active_interview_app.openai_utils import create_chat_completion, get_openai_client

response = create_chat_completion(
    client=get_openai_client(),
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    user=request.user  # Optional: for user attribution
)
```

### 3. Scripts

#### `track-claude-tokens.py`
Manually track Claude Code usage from local sessions.

**Usage:**
```bash
# Interactive mode
python scripts/track-claude-tokens.py --interactive

# Command-line mode
python scripts/track-claude-tokens.py --input-tokens 1000 --output-tokens 500

# With notes
python scripts/track-claude-tokens.py --input-tokens 1000 --output-tokens 500 --notes "Implemented feature X"
```

#### `import-token-usage.py`
Imports token usage from temporary JSON files into the database.

**Usage:**
```bash
python scripts/import-token-usage.py
```

This runs automatically in the CI/CD pipeline.

#### `report-token-metrics.py`
Generates comprehensive token usage reports.

**Usage:**
```bash
python scripts/report-token-metrics.py
```

**Output includes:**
- Branch-specific usage
- Recent activity (last 7 days)
- Branch comparison
- Merge statistics (if merging to main)
- Cumulative all-time stats

### 4. Git Hooks

#### `post-commit` Hook
Located in: `.githooks/post-commit`

After each commit, prompts you to track Claude Code usage. Automatically:
- Detects git branch
- Captures commit SHA
- Saves token records to `temp/` directory
- Shows friendly prompts

**Disable temporarily:**
```bash
git commit --no-verify -m "message"
```

---

## Usage Guide

### For Application Developers

#### Track OpenAI Calls in Views

**Before:**
```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}]
)
```

**After:**
```python
from active_interview_app.openai_utils import create_chat_completion, get_openai_client

response = create_chat_completion(
    client=get_openai_client(),
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    user=request.user  # Optional
)
```

#### Track in Resume Parser

The resume parser in `resume_parser.py` should use the wrapper:

```python
from .openai_utils import create_chat_completion, get_openai_client

response = create_chat_completion(
    client=get_openai_client(),
    model="gpt-4o",
    messages=messages,
    response_format={"type": "json_object"}
)
```

### For CI/CD Scripts

Scripts that use OpenAI (like `ai-review.py`) should track tokens:

```python
# Import tracking function
from datetime import datetime
import os
import json

def track_token_usage_standalone(model_name, prompt_tokens, completion_tokens):
    """Track tokens in CI/CD scripts."""
    record = {
        'timestamp': datetime.now().isoformat(),
        'git_branch': os.environ.get('GITHUB_HEAD_REF', 'main'),
        'model_name': model_name,
        'endpoint': 'chat.completions',
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
        'total_tokens': prompt_tokens + completion_tokens
    }

    os.makedirs('temp', exist_ok=True)
    filename = f"token_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(f'temp/{filename}', 'w') as f:
        json.dump(record, f, indent=2)

# After API call
if hasattr(completion, 'usage'):
    track_token_usage_standalone(
        completion.model,
        completion.usage.prompt_tokens,
        completion.usage.completion_tokens
    )
```

### For Local Development with Claude Code

1. **Enable Git Hooks**
   ```bash
   scripts/install-git-hooks.sh  # or .bat on Windows
   ```

2. **Use Claude Code normally**

3. **After committing:**
   - You'll see a prompt asking if you used Claude Code
   - Check the Claude Code UI for token counts (bottom right corner)
   - Enter the counts when prompted
   - Token usage is saved automatically

4. **Manual tracking (if you forgot):**
   ```bash
   python scripts/track-claude-tokens.py --interactive
   ```

---

## CI/CD Integration

### Pipeline Workflow

The CI/CD pipeline (`CI.yml`) includes a `token-metrics` job that:

1. **Triggers:** Only on push to `main` branch
2. **Runs after:** Tests, AI review, and LOC metrics
3. **Steps:**
   - Sets up Python environment
   - Runs database migrations
   - Imports token usage from temp files
   - Generates comprehensive report
   - Adds report to GitHub Actions summary
   - Uploads report as artifact

### Viewing Reports

**In GitHub Actions:**
1. Go to the Actions tab
2. Click on a workflow run
3. Scroll to the bottom for the "Token Usage Metrics" summary

**Download Artifact:**
1. Go to workflow run
2. Scroll to "Artifacts" section
3. Download `token-metrics-report`

### Example Output

```
======================================================================
TOKEN USAGE REPORT - Branch: feature/new-ui
======================================================================

📊 Total API Requests: 15
🔢 Total Tokens Used: 45,230
💰 Estimated Cost: $2.1570

📈 Breakdown by Model:
----------------------------------------------------------------------

  Model: gpt-4o
  ├─ Requests: 10
  ├─ Prompt Tokens: 25,000
  ├─ Completion Tokens: 12,000
  ├─ Total Tokens: 37,000
  └─ Cost: $1.9200

  Model: claude-sonnet-4-5-20250929
  ├─ Requests: 5
  ├─ Prompt Tokens: 5,230
  ├─ Completion Tokens: 3,000
  ├─ Total Tokens: 8,230
  └─ Cost: $0.2370

======================================================================
CUMULATIVE STATISTICS (All Time)
======================================================================

📊 Total Merges Tracked: 23
🔢 Total Tokens Used: 1,250,000
💰 Total Cost: $67.45

📈 Breakdown by Provider:
   Claude: 350,000 tokens (28.0%)
   ChatGPT: 900,000 tokens (72.0%)
======================================================================
```

---

## Database Models

### Accessing in Django Admin

1. Add to `admin.py`:
```python
from django.contrib import admin
from .token_usage_models import TokenUsage
from .merge_stats_models import MergeTokenStats

@admin.register(TokenUsage)
class TokenUsageAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'model_name', 'git_branch', 'total_tokens', 'estimated_cost']
    list_filter = ['model_name', 'git_branch', 'created_at']
    search_fields = ['git_branch', 'model_name']
    date_hierarchy = 'created_at'

@admin.register(MergeTokenStats)
class MergeTokenStatsAdmin(admin.ModelAdmin):
    list_display = ['merge_date', 'source_branch', 'merge_commit_sha', 'cumulative_cost']
    list_filter = ['source_branch', 'target_branch', 'merge_date']
```

### Querying Token Usage

```python
from active_interview_app.token_usage_models import TokenUsage
from active_interview_app.merge_stats_models import MergeTokenStats

# Get all usage for a branch
summary = TokenUsage.get_branch_summary('feature/new-ui')

# Get recent usage
recent = TokenUsage.objects.filter(
    created_at__gte=datetime.now() - timedelta(days=7)
).order_by('-created_at')

# Get merge stats
latest_merge = MergeTokenStats.objects.latest('merge_date')
breakdown = latest_merge.get_breakdown_summary()
```

---

## Cost Tracking

### Current Pricing (as of January 2025)

#### OpenAI GPT-4o
- **Input:** $0.03 per 1K tokens
- **Output:** $0.06 per 1K tokens

#### Claude Sonnet 4.5
- **Input:** $0.003 per 1K tokens
- **Output:** $0.015 per 1K tokens

### Cost Calculation

Costs are automatically calculated via the `estimated_cost` property:

```python
token_record = TokenUsage.objects.get(id=123)
cost = token_record.estimated_cost  # Returns USD amount
```

### Updating Pricing

Edit `token_usage_models.py` line 75-95 to update pricing:

```python
costs = {
    'gpt-4o': {
        'prompt': 0.03,      # Update these values
        'completion': 0.06
    },
    'claude-sonnet-4-5-20250929': {
        'prompt': 0.003,
        'completion': 0.015
    }
}
```

---

## Troubleshooting

### Git Hook Not Running

**Problem:** Post-commit hook doesn't prompt after commits

**Solutions:**
1. Re-install hooks:
   ```bash
   scripts/install-git-hooks.sh  # or .bat
   ```

2. Check hook is executable:
   ```bash
   chmod +x .git/hooks/post-commit
   ```

3. Check you're in a terminal (hooks don't run in GUI tools)

4. Bypass if needed:
   ```bash
   git commit --no-verify -m "message"
   ```

### Token Records Not Appearing in Reports

**Problem:** Tracked tokens don't show in merge reports

**Solutions:**
1. Check temp files exist:
   ```bash
   ls temp/
   ```

2. Manually import:
   ```bash
   python scripts/import-token-usage.py
   ```

3. Check database migrations:
   ```bash
   python manage.py showmigrations
   ```

### CI/CD Pipeline Errors

**Problem:** Token metrics job fails in GitHub Actions

**Solutions:**
1. Check database migrations ran successfully
2. Verify `DJANGO_SECRET_KEY` is set in secrets
3. Check Python dependencies installed correctly
4. View detailed logs in GitHub Actions

### Incorrect Cost Calculations

**Problem:** Costs seem wrong

**Solutions:**
1. Verify pricing in `token_usage_models.py` is current
2. Check model name matches exactly
3. Ensure token counts are accurate
4. Check for duplicate records

---

## Best Practices

### 1. Regular Monitoring
- Review token metrics on each merge to main
- Set up alerts for unusual usage spikes
- Monitor cost trends over time

### 2. Branch Naming
- Use descriptive branch names
- Token usage is attributed to branches
- Easier to track feature costs

### 3. Manual Tracking
- Track Claude Code usage promptly after commits
- Add notes for context
- Review temp files before merging

### 4. Cost Optimization
- Monitor which operations use the most tokens
- Optimize prompts to reduce token usage
- Consider caching responses where appropriate

### 5. Data Retention
- Archive old token records periodically
- Keep merge stats for historical analysis
- Export reports for accounting purposes

---

## Support

For issues or questions:
1. Check this documentation
2. Review code comments in source files
3. Check GitHub Issues
4. Contact the development team

---

**Last Updated:** January 2025
**Version:** 1.0
