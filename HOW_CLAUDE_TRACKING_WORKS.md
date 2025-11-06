# How Claude Token Tracking Works

## Overview
Currently, Claude Code token tracking is **semi-manual** - you need to manually log your token usage after each session, but the system makes it very easy.

---

## 📊 Current Process (Semi-Manual)

### Step 1: Check Your Token Usage
At the end of your Claude Code session, you'll see a message like:
```
Token usage: 54161/200000; 145839 remaining
```

This tells you that you've used **54,161 tokens** in this session.

### Step 2: Add Tokens to Tracking
Run this command from your repo root:

```bash
track-tokens.bat add 54161 "Description of what you worked on"
```

**Example:**
```bash
track-tokens.bat add 54161 "Fixed token tracking and AI review pipeline"
```

### Step 3: Automatic Actions
The script automatically:
1. ✅ Saves tokens to your current branch file: `token_metrics/local_tracking/tokens_{branch}.json`
2. ✅ Exports to temp folder: `temp/claude_local_{timestamp}.json`
3. ✅ Tracks session history with timestamps
4. ✅ Shows you the running total

**Output you'll see:**
```
✅ Added 54,161 tokens to tracking
📊 Total accumulated: 54,161 tokens
🌳 Branch: token-usage
📝 Sessions tracked: 1

💾 Auto-exported to: tokens_token-usage_20251105_001139.json
```

### Step 4: When You Push to GitHub
The CI/CD pipeline automatically:
1. Finds your exported tokens in `temp/`
2. Imports them to the database with your branch name
3. Generates a report showing all token usage
4. Cleans up the temp files

---

## 🎯 Quick Reference

### Add tokens after a session:
```bash
track-tokens.bat add <tokens> "optional notes"
```

### Check your current total:
```bash
track-tokens.bat show
```

### Export for backup/sharing:
```bash
track-tokens.bat export my_backup.json
```

### Submit to database manually (optional):
```bash
track-tokens.bat submit
```

---

## 📁 Where Everything Lives

### Local Tracking (Per Branch)
```
token_metrics/local_tracking/
├── tokens_main.json              # Main branch tokens
├── tokens_feature-branch.json    # Feature branch tokens
└── tokens_token-usage.json       # Current branch tokens
```

**These files:**
- Track your running total per branch
- Persist across sessions
- Git-ignored (won't be committed)

### Temporary Export (Auto-Generated)
```
temp/
├── claude_local_20251105_001139.json
├── claude_local_20251105_004215.json
└── token_usage_20251105_143022.json
```

**These files:**
- Created automatically when you add tokens
- Used by CI/CD to import to database
- Deleted after successful import

### Database (Persistent)
- All tokens stored in Django database
- Includes branch name, model, timestamp
- Used for reporting and cost tracking

---

## 🤔 Why Not Fully Automatic?

### Current Limitation:
Claude Code doesn't expose an API or hook to automatically capture token usage at the end of each session.

### Future Enhancement Ideas:

1. **Git Hook** - Auto-prompt for tokens on commit
2. **Exit Hook** - Capture tokens when Claude Code exits
3. **Conversation Parser** - Parse conversation history for token counts

---

## 🔄 Complete Workflow Example

```bash
# 1. Start working on a feature branch
git checkout -b my-new-feature

# 2. Use Claude Code for your work
#    (You see: "Token usage: 45000/200000")

# 3. Add those tokens to tracking
track-tokens.bat add 45000 "Implemented user authentication"

# Output:
# ✅ Added 45,000 tokens to tracking
# 📊 Total accumulated: 45,000 tokens
# 🌳 Branch: my-new-feature
# 💾 Auto-exported to: tokens_my-new-feature_20251105_143022.json

# 4. Continue working... later in the day
#    (You see: "Token usage: 32000/200000")

# 5. Add more tokens
track-tokens.bat add 32000 "Fixed bugs and added tests"

# Output:
# ✅ Added 32,000 tokens to tracking
# 📊 Total accumulated: 77,000 tokens  # Running total!
# 🌳 Branch: my-new-feature
# 💾 Auto-exported to: tokens_my-new-feature_20251105_160845.json

# 6. Commit and push
git add .
git commit -m "Add authentication feature"
git push origin my-new-feature

# 7. CI/CD automatically:
# - Imports your token files from temp/
# - Saves to database with branch "my-new-feature"
# - Generates report
# - Shows in GitHub Actions summary

# 8. Merge to main
# Your tokens remain attributed to "my-new-feature" branch!
```

---

## 📊 Viewing Your Token Usage

### Option 1: Local Status
```bash
track-tokens.bat show
```

**Shows:**
- Current branch total
- Session history
- Last 5 sessions with timestamps

### Option 2: Generate Report (After Import)
```bash
python token_metrics/scripts/report-token-metrics.py
```

**Shows:**
- All branches with token totals
- Current branch stats
- Recent activity (last 7 days)
- Model breakdown
- Cost estimates

### Option 3: GitHub Actions
- Go to Actions tab in GitHub
- Click on any workflow run
- Check "Report Token Usage Metrics" job
- See comprehensive report in summary

---

## 💡 Pro Tips

### 1. Track Frequently
Don't wait until the end of the day - track after each Claude Code session:
```bash
track-tokens.bat add 25000 "Morning: Implemented feature X"
track-tokens.bat add 18000 "Afternoon: Fixed bugs"
track-tokens.bat add 12000 "Evening: Code review updates"
```

### 2. Use Descriptive Notes
Good notes help with reporting:
```bash
✅ Good: track-tokens.bat add 50000 "User authentication - OAuth2 integration"
❌ Bad:  track-tokens.bat add 50000 "stuff"
```

### 3. Check Before Pushing
Before you push to GitHub:
```bash
# Verify your tokens are tracked
track-tokens.bat show

# Check temp folder has export files
dir temp\claude_local_*.json
```

### 4. Export for Backup
At the end of each week or iteration:
```bash
track-tokens.bat export week_23_tokens.json
```

---

## 🐛 Troubleshooting

### "Where do I see my token usage in Claude Code?"
Look for messages like:
```
Token usage: 54161/200000; 145839 remaining
```
These appear throughout your conversation, especially at the end.

### "I forgot to track my tokens!"
Check your conversation history for token usage messages and add them retroactively:
```bash
track-tokens.bat add 54000 "Retroactive: token tracking work"
```

### "My tokens show wrong branch"
Make sure you're on the correct branch before running track-tokens:
```bash
git branch  # Check current branch
git checkout correct-branch
track-tokens.bat add 50000 "Work on correct branch"
```

### "Files not appearing in temp/"
The `--auto-export` flag should create files automatically. If not:
```bash
# Manual export
cd token_metrics
export-tokens.bat my_manual_export.json
```

---

## 🚀 Future Automation Ideas

If you want to make this more automatic, you could:

### Option 1: Git Pre-Commit Hook
Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
echo "Did you track your Claude Code tokens?"
echo "Run: track-tokens.bat add [tokens] 'description'"
read -p "Press enter to continue..."
```

### Option 2: Alias for Quick Tracking
Add to your shell profile:
```bash
alias ct='track-tokens.bat add'
# Usage: ct 50000 "My work"
```

### Option 3: End-of-Day Reminder
Set a reminder to check conversation history and track tokens before ending your workday.

---

## Summary

**Current System:**
- ✅ Easy to use: One command to track tokens
- ✅ Automatic export to temp/
- ✅ Automatic CI/CD import
- ✅ Branch-aware tracking
- ❌ Requires manual input after each session

**To Track Your Tokens:**
1. Look for "Token usage: X/200000" in Claude Code
2. Run: `track-tokens.bat add X "what you did"`
3. Push to GitHub
4. CI/CD handles the rest!

**The system remembers:**
- Which branch you worked on
- When you used the tokens
- Running totals per branch
- Full history for reporting
