# Token Tracking Scripts - Quick Reference

## 🚀 Simplified Interface

All scripts now use a **single command** with **optional flags**.

### track-tokens (.sh / .bat)

**Main token tracking script** - Windows (.bat) and Unix/Linux/Mac (.sh)

#### Default Action (No Arguments)
```bash
./track-tokens.sh           # Shows usage summary (last 30 days)
```

#### All Options
```bash
# Help
./track-tokens.sh --help    # or -h

# Track tokens
./track-tokens.sh --add                     # Interactive mode
./track-tokens.sh --add 10000 5000          # Quick add
./track-tokens.sh -a 10000 5000 "Bug fix"   # With notes

# Auto-extract
./track-tokens.sh --auto

# View usage
./track-tokens.sh --show        # Last 30 days (default)
./track-tokens.sh -s 7          # Last 7 days
./track-tokens.sh -s 0          # All time

# Detailed trends
./track-tokens.sh --trends      # Last 30 days
./track-tokens.sh -t 90         # Last 90 days

# Complete analysis
./track-tokens.sh --all         # All time, all branches

# Export
./track-tokens.sh --export                  # Default filename
./track-tokens.sh -e monthly_jan.csv        # Custom filename

# Dashboard
./track-tokens.sh --dashboard               # Default filename
./track-tokens.sh -d report.html            # Custom filename
```

---

## 📋 File Overview

### Main Scripts

| Script | Platform | Description |
|--------|----------|-------------|
| `track-tokens.sh` | Unix/Linux/Mac | Main CLI - simplified interface |
| `track-tokens.bat` | Windows | Main CLI - simplified interface |
| `automate-tracking.sh` | Unix/Linux/Mac | Automation with cron support |
| `token-utils.sh` | Unix/Linux/Mac | Utility functions to source |

### Python Scripts (Called by Wrappers)

| Script | Purpose |
|--------|---------|
| `track-claude-tokens.py` | Track tokens interactively or with args |
| `extract-claude-tokens.py` | Auto-extract from Claude logs |
| `analyze-token-trends.py` | Generate analysis and reports |
| `generate-dashboard.py` | Create HTML dashboard |
| `report-token-metrics.py` | Simple branch summary |
| `import-token-usage.py` | Import to database |

### Installation Scripts

| Script | Purpose |
|--------|---------|
| `install-git-hooks.sh` | Install hooks (Unix/Linux/Mac) |
| `install-git-hooks.bat` | Install hooks (Windows) |

---

## 🎯 Common Workflows

### Daily Development
```bash
# Morning check
./track-tokens.sh

# Track session
./track-tokens.sh --add

# End of day
./track-tokens.sh -s 1
```

### Weekly Review
```bash
# See trends
./track-tokens.sh --trends

# Generate dashboard
./track-tokens.sh --dashboard
```

### Monthly Export
```bash
# Export data
./track-tokens.sh --export monthly_$(date +%Y%m).csv

# Full analysis
./track-tokens.sh --all
```

---

## 💡 Pro Tips

### 1. No Arguments = Quick Summary
Just run the script to see current usage:
```bash
./track-tokens.sh    # Most common command
```

### 2. Short Flags for Speed
```bash
./track-tokens.sh -a    # Add tokens
./track-tokens.sh -t    # Trends
./track-tokens.sh -e    # Export
./track-tokens.sh -d    # Dashboard
```

### 3. All Options Have Defaults
Every flag works without additional parameters:
```bash
./track-tokens.sh --show      # Defaults to 30 days
./track-tokens.sh --export    # Defaults to token_usage_export.csv
./track-tokens.sh --dashboard # Defaults to token_dashboard.html
```

### 4. Help is Always Available
```bash
./track-tokens.sh --help
./track-tokens.bat --help
```

---

## 🔧 Setup (First Time)

### Unix/Linux/Mac
```bash
# Make executable
chmod +x track-tokens.sh automate-tracking.sh token-utils.sh

# Install hooks (optional)
./install-git-hooks.sh
```

### Windows
```batch
# Just run! No setup needed for .bat files

# Install hooks (optional)
.\install-git-hooks.bat
```

---

## 📚 Documentation

- **Quick Start:** `../QUICK_START_CLAUDE_TRACKING.md`
- **Bash Scripts Guide:** `../BASH_SCRIPTS_GUIDE.md`
- **Time Series Tracking:** `../TRACKING_OVER_TIME_GUIDE.md`

---

## 🆘 Help

### Get Help
```bash
./track-tokens.sh --help        # Comprehensive help
./automate-tracking.sh --help   # Automation help
```

### Troubleshooting
```bash
# Python not found
# → Install Python 3

# Permission denied (Unix/Linux/Mac)
chmod +x track-tokens.sh

# No data
./track-tokens.sh --add    # Add your first session
```

---

**Last Updated:** January 2025
**Version:** 3.0 (Simplified Interface)
