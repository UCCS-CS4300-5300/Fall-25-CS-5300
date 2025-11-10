# Claude Code Token Tracking - Quick Start

## ✨ What It Does

**Automatically tracks Claude Code token usage** per developer and per branch!

- ✅ **Automatic extraction** from Claude Code conversations
- ✅ **Per-branch tracking** - see costs per feature
- ✅ **Per-user attribution** - track individual usage
- ✅ **CI/CD reports** - automatic reporting on merge to `main`
- ✅ **Cost estimation** - see dollar amounts

---

## ⚡ Super Quick Commands

**Just run the script!** No arguments needed for common tasks.

### Windows
```batch
cd token_metrics\scripts

# Show current usage (default)
.\track-tokens.bat

# Track new session
.\track-tokens.bat --add

# See all options
.\track-tokens.bat --help
```

### Unix/Linux/Mac
```bash
cd token_metrics/scripts

# Show current usage (default)
./track-tokens.sh

# Track new session
./track-tokens.sh --add

# See all options
./track-tokens.sh --help
```

### Available Commands
- `--show [DAYS]` - Usage summary (default: 30 days)
- `--add [INPUT] [OUTPUT]` - Track tokens (interactive or specific)
- `--trends [DAYS]` - Detailed trends with breakdown
- `--export [FILE]` - Export to CSV
- `--dashboard [FILE]` - Generate HTML dashboard
- `--auto` - Auto-extract from logs
- `--all` - Complete analysis (all time)

**Short flags:** `-s`, `-a`, `-t`, `-e`, `-d`, `-h`

---

## 🚀 Setup (One-Time)

### Step 1: Install Git Hooks

**Windows:**
```bash
cd token_metrics\scripts
.\install-git-hooks.bat
```

**Mac/Linux:**
```bash
cd token_metrics/scripts
chmod +x install-git-hooks.sh
./install-git-hooks.sh
```

### Step 2: That's It!

The hooks are now active and will track tokens automatically.

---

## 📊 How It Works

### Automatic Mode (Preferred)

When you commit code, the git hook:

1. **Searches** for Claude Code conversation data
2. **Extracts** token usage from system messages like:
   ```
   Token usage: 58992/200000; 141008 remaining
   ```
3. **Saves** to `temp/` directory automatically
4. **Reports** in GitHub Actions when you merge

### Manual Fallback

If automatic extraction fails, you'll be prompted:

```
⚠ Auto-extraction failed, switching to manual mode
Did you use Claude Code for this commit?
Check the Claude Code UI for token counts (bottom right)

Track tokens manually? (y/N):
```

Just enter `y` and type in the counts from Claude Code UI.

---

## 🎯 Where Tokens Are Tracked

### 1. Local Tracking Files
**Location:** `token_metrics/local_tracking/tokens_<branch-name>.json`

Per-branch summary of all sessions:
```json
{
  "branch": "feature/new-ui",
  "total_tokens": 45230,
  "sessions": [
    {
      "timestamp": "2025-01-09T14:30:00",
      "tokens": 15000,
      "notes": "Auto-tracked from commit"
    }
  ]
}
```

### 2. Temp Files for CI/CD
**Location:** `temp/claude_local_YYYYMMDD_HHMMSS.json`

Individual session records:
```json
{
  "timestamp": "2025-01-09T14:30:00.000000",
  "git_branch": "feature/new-ui",
  "commit_sha": "abc123def...",
  "model_name": "claude-sonnet-4-5-20250929",
  "endpoint": "messages",
  "prompt_tokens": 36000,
  "completion_tokens": 9230,
  "total_tokens": 45230,
  "source": "auto-tracked"
}
```

### 3. Database (After Merge)
**Location:** Django `TokenUsage` table

Permanent records with:
- `user` - Who used the tokens
- `git_branch` - Which branch
- `model_name` - Which AI model
- `total_tokens` - How many tokens
- `estimated_cost` - Dollar amount

---

## 📈 View Usage Reports

### During Development

**Check your branch total:**
```bash
python token_metrics/scripts/report-token-metrics.py
```

**Output:**
```
======================================================================
TOKEN USAGE REPORT - Branch: feature/new-ui
======================================================================

📊 Total API Requests: 5
🔢 Total Tokens Used: 45,230
💰 Estimated Cost: $0.2370

📈 Breakdown by Model:
----------------------------------------------------------------------
  Model: claude-sonnet-4-5-20250929
  ├─ Requests: 5
  ├─ Prompt Tokens: 36,000
  ├─ Completion Tokens: 9,230
  ├─ Total Tokens: 45,230
  └─ Cost: $0.2370
```

### After Merging to Main

**GitHub Actions automatically:**
1. Imports all temp files
2. Generates comprehensive report
3. Shows cumulative statistics
4. Uploads as artifact

**View in GitHub:**
- Go to Actions tab
- Click on workflow run
- See "Token Usage Metrics" summary

---

## 💡 Manual Tracking (If Needed)

### Track Forgotten Sessions

**Simplified (Recommended):**
```bash
# Windows
cd token_metrics\scripts
.\track-tokens.bat --add

# Unix/Linux/Mac
cd token_metrics/scripts
./track-tokens.sh --add
```

**Direct Python Call:**
```bash
python token_metrics/scripts/track-claude-tokens.py --interactive
```

### Track Specific Counts

**Simplified:**
```bash
# Windows
.\track-tokens.bat --add 10000 5000 "Implemented authentication"

# Unix/Linux/Mac
./track-tokens.sh --add 10000 5000 "Implemented authentication"
```

**Direct Python Call:**
```bash
python token_metrics/scripts/track-claude-tokens.py \
  --input-tokens 10000 \
  --output-tokens 5000 \
  --notes "Implemented authentication"
```

### Batch Import to Database

```bash
cd active_interview_backend
python manage.py shell
```

```python
from active_interview_app.models import User
from active_interview_app.token_tracking import record_token_usage

# Import tokens for a specific user
user = User.objects.get(username='your-username')

# This runs automatically in CI/CD, but you can trigger manually:
from active_interview_app.management.commands.import_tokens import Command
cmd = Command()
cmd.handle()
```

---

## 🔧 Troubleshooting

### Hook Not Running

**Problem:** No prompt after commits

**Solution:**
```bash
# Re-install hooks
cd token_metrics/scripts
.\install-git-hooks.bat  # Windows
./install-git-hooks.sh   # Mac/Linux

# Check hook exists
ls .git/hooks/post-commit
```

### Auto-Extraction Always Fails

**Problem:** Always falls back to manual

**Possible Causes:**
1. Claude Code conversation files not accessible
2. Different Claude Code version/storage location
3. Running in non-interactive mode (IDE git integration)

**Solution:**
- Use manual mode: Enter tokens when prompted
- Or track later: `python token_metrics/scripts/track-claude-tokens.py --interactive`

### Tokens Not in Reports

**Problem:** Tracked tokens don't appear in GitHub Actions

**Check:**
```bash
# 1. Verify temp files exist
ls temp/claude_local_*.json

# 2. Manually import
cd active_interview_backend
python manage.py migrate
python token_metrics/scripts/import-token-usage.py
```

---

## 💰 Cost Tracking

### Current Pricing (Jan 2025)

**Claude Sonnet 4.5:**
- Input: $0.003 / 1K tokens
- Output: $0.015 / 1K tokens

**Example Cost:**
- 10,000 input + 5,000 output tokens
- = (10 × $0.003) + (5 × $0.015)
- = $0.03 + $0.075
- = **$0.105**

### Update Pricing

Edit `active_interview_backend/active_interview_app/token_usage_models.py`:

```python
costs = {
    'claude-sonnet-4-5-20250929': {
        'prompt': 0.003,      # Update here
        'completion': 0.015   # Update here
    }
}
```

---

## 📝 Best Practices

### 1. **Track Promptly**
- Let auto-extraction run after each commit
- If manual, track while Claude Code window is still open

### 2. **Add Context**
- Use `--notes` flag for manual tracking
- Helps understand what features cost what

### 3. **Review Before Merging**
- Check `temp/` directory has your token files
- Run local report to see branch totals
- Commit temp files so they're imported in CI/CD

### 4. **Monitor Costs**
- Review GitHub Actions summaries
- Track trends over time
- Optimize expensive operations

---

## 🎓 Examples

### Example 1: Feature Development

```bash
# Work on feature
git checkout -b feature/auth-system

# Make commits with Claude Code
git commit -m "Add login form"
# → Hook runs, extracts tokens automatically ✅

git commit -m "Add password validation"
# → Hook runs, extracts tokens automatically ✅

# Check your usage so far
python token_metrics/scripts/report-token-metrics.py
# → Shows total for feature/auth-system branch

# Merge to main
git checkout main
git merge feature/auth-system
git push origin main
# → CI/CD imports all tokens, generates report
```

### Example 2: Batch Session

```bash
# Had a long Claude Code session, forgot to track

# Track manually
python token_metrics/scripts/track-claude-tokens.py --interactive
# Input tokens: 25000
# Output tokens: 12000
# Notes: Implemented entire auth system
# ✅ Saved!
```

### Example 3: Team Report

```python
# In Django admin or shell
from active_interview_app.token_usage_models import TokenUsage

# Get all usage for a branch
summary = TokenUsage.get_branch_summary('feature/auth-system')
print(f"Total tokens: {summary['total_tokens']:,}")
print(f"Total cost: ${summary['total_cost']:.4f}")

# See by model
for model, stats in summary['by_model'].items():
    print(f"{model}: {stats['total_tokens']:,} tokens (${stats['cost']:.4f})")
```

---

## 🆘 Need Help?

1. **Documentation:** See `token_metrics/docs/TOKEN_TRACKING.md` for full details
2. **Scripts:** Check `token_metrics/scripts/` for utilities
3. **Issues:** Report problems in GitHub Issues
4. **Questions:** Ask the team in Slack/Discord

---

**Last Updated:** January 2025
**System Version:** 2.0 (Auto-Extraction)
