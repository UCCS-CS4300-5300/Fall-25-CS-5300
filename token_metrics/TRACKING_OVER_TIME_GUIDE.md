# Collecting Token Data Over Time - Complete Guide

## 🎯 Overview

This guide shows you how to **track and analyze your Claude Code token usage over time** to understand patterns, costs, and trends.

---

## 📊 Quick Start - Track Your Tokens

### Method 1: Automatic (After Each Commit)

**Setup once:**
```bash
cd token_metrics\scripts
.\install-git-hooks.bat
```

**Then every time you commit:**
- Hook automatically extracts and saves tokens
- Data accumulates in `token_metrics/local_tracking/`
- No manual work needed!

### Method 2: Manual Tracking

```bash
# Interactive
cd token_metrics\scripts
.\track-tokens.bat add

# Or with specific counts
.\track-tokens.bat add 10000 5000
```

---

## 📈 View Your Historical Data

### Simple Summary (Last 30 Days)

```bash
.\track-tokens.bat show
```

**Output:**
```
======================================================================
📊 CLAUDE CODE TOKEN USAGE ANALYSIS - Last 30 days
======================================================================

🌳 Branches tracked:        5
📝 Total sessions:          23
🔢 Total tokens:            107,046
💰 Estimated cost:          $0.5142
📊 Average per session:     4,654 tokens
```

### Detailed Trends

```bash
.\track-tokens.bat trends
```

**Shows:**
- Daily breakdown
- Weekly trends
- Usage insights
- Cost projections

### Complete Analysis (All Time)

```bash
.\track-tokens.bat all
```

**Shows:**
- All branches
- Daily usage
- Weekly trends
- Insights & recommendations
- Peak usage days
- Most active branches

---

## 📅 Time-Based Analysis

### Last 7 Days

```bash
python analyze-token-trends.py --days 7 --daily --insights
```

### Last 90 Days

```bash
python analyze-token-trends.py --days 90 --weekly --by-branch
```

### All Time

```bash
python analyze-token-trends.py --days 0 --all
```

---

## 📊 Example Reports

### Daily Breakdown

```
======================================================================
📅 DAILY USAGE BREAKDOWN
======================================================================

Date         Sessions          Tokens         Cost
----------------------------------------------------------------------
2025-01-09         3          45,230      $0.2048
2025-01-08         2          32,100      $0.1455
2025-01-07         1          15,000      $0.0680
2025-01-06         4          52,800      $0.2394
```

### Weekly Trends

```
======================================================================
📊 WEEKLY TRENDS
======================================================================

Week Starting    Sessions          Tokens         Cost
----------------------------------------------------------------------
2025-01-06         10         120,550      $0.5466
2024-12-30          8          95,230      $0.4318
2024-12-23          5          67,100      $0.3042
```

### By Branch

```
======================================================================
🌳 USAGE BY BRANCH
======================================================================

Branch                         Sessions          Tokens         Cost
----------------------------------------------------------------------
feature/scoring-transparency          8          45,230      $0.2050
feature/pdf-export                    6          38,500      $0.1745
bugfix/test-failures                  3          12,800      $0.0581
main                                  2           8,500      $0.0385
```

### Insights

```
======================================================================
💡 INSIGHTS
======================================================================

📈 Peak usage day:         2025-01-09 (45,230 tokens)
🌳 Most active branch:     feature/scoring-transparency (45,230 tokens)
📊 Average per day:        6,475 tokens
💰 Projected monthly cost: $2.92
```

---

## 💾 Export Your Data

### Export to CSV (for Excel, Google Sheets)

```bash
.\track-tokens.bat export my_usage.csv
```

**CSV Format:**
```csv
timestamp,branch,tokens,estimated_cost,notes
2025-01-09 14:30:00,feature/scoring,45230,0.2050,Auto-tracked
2025-01-08 10:15:00,feature/pdf-export,32100,0.1455,Fixed tests
```

### Export to JSON (for programming/analysis)

```bash
python analyze-token-trends.py --export-json usage_data.json
```

**JSON Includes:**
- Summary statistics
- Daily breakdown
- Weekly breakdown
- Per-branch totals
- All individual sessions

---

## 📊 Visual Dashboard

### Generate Interactive HTML Dashboard

```bash
python generate-dashboard.py
```

**Creates:**
- `token_dashboard.html` - Interactive charts and graphs
- Opens in your browser
- Shows:
  - Total sessions, tokens, costs
  - Daily usage line chart
  - Daily cost bar chart
  - Usage by branch
  - Trends over time

**View it:**
```bash
start token_dashboard.html  # Windows
open token_dashboard.html   # Mac
```

---

## 🔍 Advanced Analysis

### Compare Time Periods

```bash
# Last week
python analyze-token-trends.py --days 7 > last_week.txt

# Last month
python analyze-token-trends.py --days 30 > last_month.txt

# Compare
diff last_week.txt last_month.txt
```

### Find Expensive Features

```python
# In Python
import json

with open('usage_data.json') as f:
    data = json.load(f)

# Sort branches by cost
branches = data['by_branch']
expensive = sorted(
    branches.items(),
    key=lambda x: x[1]['estimated_cost'],
    reverse=True
)

print("Top 5 Most Expensive Branches:")
for name, stats in expensive[:5]:
    print(f"{name}: ${stats['estimated_cost']:.2f}")
```

### Track Progress Over Time

```bash
# Export weekly
python analyze-token-trends.py --export-json week_$(date +%Y%m%d).json

# Keep these files to see trends over months
```

---

## 📈 Tracking Strategies

### Strategy 1: Daily Review

```bash
# Every day, run:
.\track-tokens.bat show

# Every week, run:
.\track-tokens.bat trends

# Every month, export:
.\track-tokens.bat export monthly_$(date +%Y%m).csv
```

### Strategy 2: Per-Feature Tracking

```bash
# When starting a feature
git checkout -b feature/new-auth

# Work and commit (auto-tracking happens)
# ...

# Before merging, check cost
python analyze-token-trends.py --by-branch

# Decide if feature is worth the AI cost
```

### Strategy 3: Budget Monitoring

```bash
# Check monthly projection
python analyze-token-trends.py --days 30 --insights

# Look for "Projected monthly cost"
# Adjust usage if over budget
```

---

## 📊 Data Storage Locations

### Local Tracking Files
**Location:** `token_metrics/local_tracking/tokens_<branch>.json`

**Per-branch cumulative data:**
```json
{
  "branch": "feature/scoring",
  "total_tokens": 45230,
  "sessions": [
    {
      "timestamp": "2025-01-09T14:30:00",
      "tokens": 15000,
      "notes": "Auto-tracked from commit"
    },
    {
      "timestamp": "2025-01-09T16:45:00",
      "tokens": 18000,
      "notes": "Fixed failing tests"
    }
  ],
  "created_at": "2025-01-09T10:00:00",
  "last_updated": "2025-01-09T16:45:00"
}
```

### Temp Files (For CI/CD)
**Location:** `temp/claude_local_*.json`

**Individual session records for pipeline import**

### Database (After Merge)
**Table:** `active_interview_app_tokenusage`

**Permanent records queryable via Django ORM**

---

## 🎓 Real-World Examples

### Example 1: Monthly Cost Tracking

```bash
# Create monthly tracking script
cat > track_monthly.bat << 'EOF'
@echo off
set MONTH=%date:~4,2%-%date:~10,4%
python analyze-token-trends.py --days 30 > reports\usage_%MONTH%.txt
python analyze-token-trends.py --export-csv reports\usage_%MONTH%.csv
echo Monthly report saved!
EOF

# Run monthly
.\track_monthly.bat
```

### Example 2: Team Comparison

```python
# analyze_team.py
from active_interview_app.token_usage_models import TokenUsage
from django.contrib.auth.models import User

users = User.objects.all()
for user in users:
    usage = TokenUsage.objects.filter(user=user)
    total = sum(u.total_tokens for u in usage)
    cost = sum(u.estimated_cost for u in usage)
    print(f"{user.username}: {total:,} tokens (${cost:.2f})")
```

### Example 3: Feature Cost Analysis

```bash
# Before feature
git checkout -b feature/new-ui
BEFORE=$(python -c "import json; print(json.load(open('usage_data.json'))['summary']['total_cost'])")

# Work on feature...

# After feature
AFTER=$(python -c "import json; print(json.load(open('usage_data.json'))['summary']['total_cost'])")

# Calculate feature cost
python -c "print(f'Feature cost: ${$AFTER - $BEFORE:.2f}')"
```

---

## 🔧 Integration with Your Workflow

### In Your Development Cycle

```bash
# 1. Start feature
git checkout -b feature/new-thing

# 2. Work with Claude Code
# (auto-tracking happens on each commit)

# 3. Check usage before PR
.\track-tokens.bat show

# 4. Add to PR description
echo "## Token Usage" >> PR.md
python analyze-token-trends.py --by-branch | grep new-thing >> PR.md

# 5. Merge to main
# (CI/CD automatically imports and reports)
```

### In Your Weekly Review

```bash
# Monday morning
.\track-tokens.bat trends > weekly_review.txt

# Review:
# - Which features used most tokens?
# - Are costs trending up or down?
# - Any unusually expensive days?

# Adjust strategy accordingly
```

---

## 💡 Pro Tips

### 1. **Regular Exports**
Create automated exports for long-term archival:
```bash
# Add to your weekly script
python analyze-token-trends.py --export-json backups\tokens_$(date +%Y%m%d).json
```

### 2. **Set Alerts**
Monitor for unusual usage:
```bash
# Check if today's usage is > 50,000 tokens
USAGE=$(python analyze-token-trends.py --days 1 --export-json - | jq '.summary.total_tokens')
if [ $USAGE -gt 50000 ]; then
    echo "⚠️ High usage today: $USAGE tokens"
fi
```

### 3. **Track Context**
Always add notes when manually tracking:
```bash
python track-claude-tokens.py --input-tokens 15000 --output-tokens 8000 \
    --notes "Debugged complex authentication issue"
```

### 4. **Review Before Merging**
Check branch costs before merging to main:
```bash
python analyze-token-trends.py --by-branch | grep $(git branch --show-current)
```

---

## 🆘 Troubleshooting

### Data Not Accumulating?

**Check:**
```bash
# Verify tracking files exist
ls token_metrics\local_tracking\

# Should see: tokens_<branch-name>.json files

# If empty, run manual tracking
.\track-tokens.bat add
```

### Wrong Totals?

**Fix:**
```bash
# Re-calculate from temp files
python import-token-usage.py

# Re-generate tracking files
python analyze-token-trends.py --days 0 > /dev/null
```

### Lost Data?

**Recover:**
```bash
# Temp files still there?
ls temp\claude_local_*.json

# Re-import if needed
python import-token-usage.py
```

---

## 📚 Summary

**You now have:**
- ✅ Automatic token tracking per commit
- ✅ Historical data collection per branch
- ✅ Time-series analysis (daily/weekly/monthly)
- ✅ Cost estimation and projections
- ✅ Export to CSV/JSON
- ✅ Visual dashboards
- ✅ Trend insights and recommendations

**Use it to:**
- Track costs over time
- Understand your usage patterns
- Budget AI spending
- Optimize expensive operations
- Compare features
- Monitor team usage

---

**Last Updated:** January 2025
**Version:** 2.0 (Time-Series Tracking)
