# Bash Scripts for Token Tracking - Complete Guide

## 🚀 Overview

Comprehensive **bash scripts** for tracking and analyzing Claude Code token usage on Unix/Linux/Mac systems.

---

## 📁 Scripts Available

| Script | Purpose |
|--------|---------|
| `track-tokens.sh` | Main wrapper - track, view, export tokens |
| `automate-tracking.sh` | Automation - daily/weekly/monthly reports |
| `token-utils.sh` | Utility functions to source in your shell |

---

## 🔧 Setup

### Make Scripts Executable

```bash
cd token_metrics/scripts

# Make all scripts executable
chmod +x track-tokens.sh
chmod +x automate-tracking.sh
chmod +x token-utils.sh
chmod +x *.sh
```

### Install Git Hooks

```bash
# Install hooks for automatic tracking
./install-git-hooks.sh
```

---

## 📊 track-tokens.sh - Main Wrapper

### Basic Usage

```bash
# Interactive tracking
./track-tokens.sh add

# Track specific counts
./track-tokens.sh add 10000 5000

# With notes
./track-tokens.sh add 10000 5000 "Fixed authentication bug"

# Auto-extract (automatic)
./track-tokens.sh auto
```

### View Reports

```bash
# Quick summary (last 30 days)
./track-tokens.sh show

# Detailed trends
./track-tokens.sh trends

# Complete analysis (all time)
./track-tokens.sh all
```

### Export Data

```bash
# Export to CSV
./track-tokens.sh export usage.csv

# Generate HTML dashboard
./track-tokens.sh dashboard

# Custom output file
./track-tokens.sh dashboard my_report.html
```

### Examples

```bash
# Morning routine
./track-tokens.sh show

# Before merging
./track-tokens.sh trends

# Monthly export
./track-tokens.sh export monthly_jan2025.csv
./track-tokens.sh dashboard monthly_jan2025.html
```

---

## 🤖 automate-tracking.sh - Automation

### Daily Reports

```bash
# Generate daily summary
./automate-tracking.sh daily
```

**Output:**
- Text report with today's usage
- Saved to `token_metrics/reports/daily_YYYY-MM-DD.txt`

### Weekly Reports

```bash
# Generate weekly report
./automate-tracking.sh weekly
```

**Output:**
- Comprehensive weekly analysis
- CSV export
- Saved to `token_metrics/reports/weekly_YYYY-WNN.*`

### Monthly Exports

```bash
# Generate monthly package
./automate-tracking.sh monthly
```

**Creates:**
- `monthly_YYYY-MM.txt` - Full report
- `monthly_YYYY-MM.csv` - CSV data
- `monthly_YYYY-MM.json` - JSON data
- `monthly_YYYY-MM.html` - Interactive dashboard

### Watch Mode

```bash
# Continuously monitor and auto-track
./automate-tracking.sh watch
```

**Features:**
- Checks every 5 minutes
- Auto-extracts tokens when detected
- Runs in background
- Press Ctrl+C to stop

### Setup Cron Jobs

```bash
# Setup automated cron jobs
./automate-tracking.sh setup-cron
```

**Adds:**
- Daily summary: Every day at 9 AM
- Weekly report: Every Monday at 9 AM
- Monthly export: 1st of month at 9 AM

**View/Edit:**
```bash
# View current cron jobs
crontab -l

# Edit cron jobs
crontab -e

# Remove all cron jobs
crontab -r
```

---

## 🔧 token-utils.sh - Utility Functions

### Load Utilities

```bash
# Source the utilities
source token_metrics/scripts/token-utils.sh

# Or add to your ~/.bashrc
echo 'source ~/path/to/token-utils.sh' >> ~/.bashrc
```

### Available Functions

#### Quick Summary

```bash
token_summary
```

**Shows:**
- Current branch
- Total tokens used
- Number of sessions
- Estimated cost

#### Cost Check

```bash
# Check if over $50 (default)
token_cost_check

# Check if over $25
token_cost_check 25
```

**Returns:**
- Exit code 0 if under budget
- Exit code 1 if over budget
- Useful for CI/CD gates

#### Branch Comparison

```bash
# Compare two branches
token_branch_compare feature/auth feature/ui
```

**Shows:**
- Tokens per branch
- Cost per branch
- Difference

#### Top Branches

```bash
# Show top 5 most expensive branches
token_top_branches

# Show top 10
token_top_branches 10
```

#### Monthly Projection

```bash
# Based on last 7 days
token_monthly_projection

# Based on last 14 days
token_monthly_projection 14
```

#### Quick Add

```bash
# Add tokens with 80/20 split assumption
token_quick_add 15000
```

**Equivalent to:**
```bash
./track-tokens.sh add 12000 3000
```

---

## 🎯 Common Workflows

### Daily Development Workflow

```bash
# Morning: Check yesterday's usage
./automate-tracking.sh daily

# During work: Auto-tracking happens on commits
git commit -m "Feature update"
# → Hook auto-tracks tokens

# Before end of day: Quick check
token_summary
```

### Weekly Review Workflow

```bash
# Monday morning
./automate-tracking.sh weekly

# Review the reports
cat token_metrics/reports/weekly_*.txt

# Open dashboard
open token_metrics/reports/weekly_*.html
```

### Feature Cost Analysis

```bash
# Start feature
git checkout -b feature/new-auth
token_summary  # Note starting tokens

# Work on feature...
# (auto-tracking on commits)

# Before merging
token_summary
token_cost_check 30  # Ensure under $30 budget

# If under budget
git checkout main
git merge feature/new-auth
```

### Monthly Reporting

```bash
# End of month
./automate-tracking.sh monthly

# Send reports to accounting
cp token_metrics/reports/monthly_*.csv /path/to/accounting/

# Archive for records
tar -czf monthly_backup_$(date +%Y%m).tar.gz \
    token_metrics/reports/monthly_*
```

---

## 🔁 Integration Examples

### Add to Git Workflow

```bash
# .git/hooks/pre-push
#!/bin/bash
source token_metrics/scripts/token-utils.sh

# Check cost before pushing
if ! token_cost_check 100; then
    echo "⚠️  Token cost over budget!"
    read -p "Continue push? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
```

### Add to CI/CD

```yaml
# .github/workflows/token-check.yml
name: Token Cost Check

on: [pull_request]

jobs:
  cost-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Check token cost
        run: |
          source token_metrics/scripts/token-utils.sh
          token_cost_check 50 || {
            echo "::warning::Token cost exceeds $50"
            exit 1
          }
```

### Add to Shell Profile

```bash
# Add to ~/.bashrc or ~/.zshrc

# Load token utilities
if [ -f ~/projects/your-repo/token_metrics/scripts/token-utils.sh ]; then
    source ~/projects/your-repo/token_metrics/scripts/token-utils.sh
fi

# Alias for convenience
alias tokens='token_summary'
alias token-add='token_quick_add'
alias token-check='token_cost_check'
```

---

## 📊 Example Outputs

### track-tokens.sh show

```
======================================================================
📊 CLAUDE CODE TOKEN USAGE ANALYSIS - Last 30 days
======================================================================

🌳 Branches tracked:        5
📝 Total sessions:          23
🔢 Total tokens:            124,679
💰 Estimated cost:          $0.5655
📊 Average per session:     5,421 tokens
```

### token_summary

```
📊 Quick Token Summary
Branch: feature/scoring-transparency

  Tokens:   45,230
  Sessions: 8
  Cost:     $0.2050
```

### token_branch_compare

```
🔄 Branch Comparison

feature/auth:
  Tokens:   45,230
  Sessions: 8
  Cost:     $0.2050

feature/ui:
  Tokens:   32,100
  Sessions: 6
  Cost:     $0.1455

Difference:
  feature/auth used 13,130 more tokens ($0.0595 more)
```

### token_top_branches

```
🏆 Top 5 Most Expensive Branches

  feature/scoring-transparency            45,230 tokens  $0.2050
  feature/pdf-export                      38,500 tokens  $0.1745
  feature/auth-system                     32,100 tokens  $0.1455
  bugfix/test-failures                    12,800 tokens  $0.0581
  main                                     8,500 tokens  $0.0385
```

---

## 🔧 Advanced Usage

### Pipe to Other Commands

```bash
# Export and email
./track-tokens.sh export monthly.csv
mail -s "Monthly Token Report" accounting@company.com < monthly.csv

# Dashboard to web server
./track-tokens.sh dashboard /var/www/html/token-dashboard.html
```

### Combine with jq

```bash
# Get specific data from JSON export
./track-tokens.sh export - \
  | jq '.summary.total_cost'

# Filter branches over $10
./track-tokens.sh export - \
  | jq -r '.by_branch | to_entries[] | select(.value.estimated_cost > 10) | .key'
```

### Scheduled Reports

```bash
# Send daily email
cat > send_daily_report.sh << 'EOF'
#!/bin/bash
./automate-tracking.sh daily | mail -s "Daily Token Report" you@email.com
EOF

chmod +x send_daily_report.sh

# Add to cron
echo "0 18 * * * /path/to/send_daily_report.sh" | crontab -
```

---

## 🆘 Troubleshooting

### Scripts Not Executable

```bash
chmod +x token_metrics/scripts/*.sh
```

### Python Not Found

```bash
# Check Python installation
which python3

# If missing, install
# Mac:
brew install python3

# Ubuntu/Debian:
sudo apt-get install python3

# CentOS/RHEL:
sudo yum install python3
```

### jq Not Found

```bash
# Mac:
brew install jq

# Ubuntu/Debian:
sudo apt-get install jq

# CentOS/RHEL:
sudo yum install jq
```

### bc Not Found

```bash
# Mac:
brew install bc

# Ubuntu/Debian:
sudo apt-get install bc

# CentOS/RHEL:
sudo yum install bc
```

### Cron Jobs Not Running

```bash
# Check cron service
sudo service cron status  # Ubuntu/Debian
sudo service crond status # CentOS/RHEL

# Check logs
tail -f /var/log/syslog | grep CRON
```

---

## 💡 Pro Tips

### 1. **Alias Common Commands**

Add to `~/.bashrc`:
```bash
alias ta='./track-tokens.sh add'
alias ts='./track-tokens.sh show'
alias tt='./track-tokens.sh trends'
alias td='./track-tokens.sh dashboard'
```

### 2. **Quick Status in PS1**

Add token count to your prompt:
```bash
# Add to ~/.bashrc
token_prompt() {
    local REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
    if [ -n "$REPO_ROOT" ]; then
        local BRANCH=$(git branch --show-current 2>/dev/null)
        local SAFE_BRANCH=$(echo "$BRANCH" | tr '/' '_')
        local FILE="$REPO_ROOT/token_metrics/local_tracking/tokens_$SAFE_BRANCH.json"

        if [ -f "$FILE" ] && command -v jq >/dev/null 2>&1; then
            local TOKENS=$(jq -r '.total_tokens // 0' "$FILE")
            echo " [${TOKENS}t]"
        fi
    fi
}

PS1='[\u@\h \W$(token_prompt)]$ '
```

### 3. **Auto-Export on Branch Switch**

```bash
# Add to ~/.bashrc
checkout() {
    git checkout "$@" && ./track-tokens.sh show
}
```

---

## 📚 Summary

**Bash Scripts Provided:**

✅ `track-tokens.sh` - Main CLI tool
✅ `automate-tracking.sh` - Automation & scheduling
✅ `token-utils.sh` - Shell functions

**Features:**

✅ Interactive tracking
✅ Auto-extraction
✅ Historical analysis
✅ Cost checking
✅ Branch comparison
✅ Automated reports
✅ Cron job setup
✅ Data export (CSV/JSON/HTML)
✅ CI/CD integration

**Use for:**

- Daily development tracking
- Weekly team reviews
- Monthly accounting reports
- Budget monitoring
- Feature cost analysis
- Automated alerts

---

**Last Updated:** January 2025
**Platform:** Unix/Linux/Mac (Bash)
