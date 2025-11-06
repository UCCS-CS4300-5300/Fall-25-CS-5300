# Token Tracking System - Test Guide

## Overview
This guide helps you verify that the token tracking system properly saves branch names and handles merges to main.

## System Features

### 1. Automatic Branch Tracking
- ✅ Tokens are saved per branch
- ✅ Branch name is automatically captured from git
- ✅ Files stored in `token_metrics/local_tracking/tokens_{branch}.json`

### 2. Multiple Format Support
The system handles three JSON formats:
1. **AI Review tokens** (`token_usage_*.json`) - From OpenAI code reviews
2. **Local Claude tokens** (`claude_local_*.json`) - From Claude Code sessions
3. **Exported tokens** (`*_tokens.json`) - From export-tokens.bat

### 3. Merge Handling
When merging to main:
- ✅ Branch-specific token files remain in place
- ✅ Tokens are imported into database with correct branch attribution
- ✅ Each branch's contribution is tracked separately

## Testing Instructions

### Test 1: Local Token Tracking with Branch Name

```bash
# 1. Create a test branch
git checkout -b test-token-tracking

# 2. Add tokens (simulating Claude Code usage)
track-tokens.bat add 50000 "Testing branch tracking"

# 3. Verify the file was created with correct branch name
dir token_metrics\local_tracking\

# Expected: tokens_test-token-tracking.json exists

# 4. Check the content includes branch name
type token_metrics\local_tracking\tokens_test-token-tracking.json
```

**Expected Output:**
```json
{
  "branch": "test-token-tracking",
  "total_tokens": 50000,
  "sessions": [...],
  ...
}
```

### Test 2: Export and Verify Branch Preservation

```bash
# 1. Export tokens from your branch
cd token_metrics
export-tokens.bat test_export.json

# 2. Check the exported file
type temp\test_export.json

# Expected: Should see your branch name in the export
```

**Expected Output:**
```json
{
  "export_metadata": {
    "exported_at": "...",
    ...
  },
  "token_data": {
    "branch": "test-token-tracking",
    "total_tokens": 50000,
    ...
  }
}
```

### Test 3: Import and Database Verification

```bash
# 1. Submit tokens to database (simulates what CI/CD does)
cd ..
python token_metrics/scripts/import-token-usage.py

# 2. Generate report to verify branch attribution
python token_metrics/scripts/report-token-metrics.py

# Expected: Should show tokens under "test-token-tracking" branch
```

### Test 4: AI Review Token Tracking (CI/CD Simulation)

```bash
# 1. Make a change and commit
echo "# Test" > test_file.txt
git add test_file.txt
git commit -m "Test commit for token tracking"

# 2. Push and watch CI/CD
git push origin test-token-tracking

# 3. Check GitHub Actions
# - Go to Actions tab
# - Find "Report Token Usage Metrics" job
# - Verify it shows tokens for your branch
```

## Verification Checklist

- [ ] Local tracking file created with correct branch name
- [ ] Export includes branch name
- [ ] Import preserves branch attribution
- [ ] Database report shows tokens per branch
- [ ] Merging to main doesn't lose branch information
- [ ] CI/CD pipeline completes without errors
- [ ] Token metrics report shows all branches

## Common Issues and Solutions

### Issue: Branch name shows as "unknown"
**Solution:** Make sure you're in a git repository and have committed changes.

### Issue: Tokens not appearing in database
**Solution:**
1. Check if JSON files exist in temp/ folder
2. Run import script manually: `python token_metrics/scripts/import-token-usage.py`
3. Check Django migrations are up to date: `python manage.py migrate`

### Issue: Cannot find tracking file
**Solution:** Run `track-tokens.bat add 1 "test"` to initialize tracking for current branch

### Issue: AI Code Review pipeline fails
**Solution:**
1. Check that `scripts/ai-review.py` exists
2. Verify OPENAI_API_KEY is set in GitHub Secrets
3. Review the diff generation step for empty diffs

## File Structure

```
token_metrics/
├── local_tracking/
│   ├── tokens_{branch_name}.json     # Per-branch tracking files
│   └── tokens_{branch}_archived_*.json  # Archived after submission
├── temp/
│   ├── token_usage_*.json            # AI review tokens
│   ├── claude_local_*.json           # Local Claude tokens
│   └── *_tokens.json                 # Exported tokens
└── scripts/
    ├── auto-track-tokens.py          # Automatic tracking
    ├── export-tokens.py              # Export to portable format
    ├── import-token-usage.py         # Import from temp/ to DB
    └── report-token-metrics.py       # Generate reports
```

## Database Schema

The `TokenUsage` model stores:
- `git_branch` - Branch name where tokens were used
- `model_name` - AI model (Claude/GPT)
- `prompt_tokens` - Input tokens
- `completion_tokens` - Output tokens
- `total_tokens` - Sum of input + output
- `created_at` - Timestamp
- `endpoint` - API endpoint used

## CI/CD Integration

The token-metrics job in CI.yml:
1. Downloads AI review token data from artifacts
2. Checks for local token files in temp/
3. Runs import script to add to database
4. Generates comprehensive report
5. Uploads report as artifact
6. Displays summary in GitHub Actions UI

## Next Steps

After verifying everything works:
1. Merge your test branch to main
2. Verify tokens appear under correct branch in report
3. Archive or delete test files
4. Document any team-specific workflows
