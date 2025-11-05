# Token Export/Import System

Share token tracking data across different instances, machines, or databases without modifying the database.

## Overview

This system allows you to:
- ✅ Export token data to a portable JSON file
- ✅ Share token tracking with teammates
- ✅ Transfer data between machines
- ✅ Backup your token tracking
- ✅ Merge data from multiple sources
- ✅ Keep separate instances independent

## Quick Start

### Export Your Tokens

```bash
# Export current branch's tokens
export-tokens.bat my_tokens.json

# Or use Python directly
python token_metrics/scripts/export-tokens.py --output my_tokens.json
```

### Import Tokens (Different Machine/Instance)

```bash
# Import (replaces existing data for that branch)
import-tokens.bat my_tokens.json

# Import and merge with existing data
import-tokens.bat my_tokens.json --merge

# Or use Python directly
python token_metrics/scripts/import-tokens.py --input my_tokens.json --merge
```

---

## Use Cases

### 1. Multiple Developers on Same Branch

**Developer A:**
```bash
# Work with Claude Code
add-tokens.bat 50000 "Initial API implementation"

# Export to share
export-tokens.bat team_tokens.json
# Share team_tokens.json via Slack/email
```

**Developer B:**
```bash
# Receive team_tokens.json
# Import and merge with your own work
import-tokens.bat team_tokens.json --merge

# Add your own tokens
add-tokens.bat 30000 "Added authentication"

# Export combined data
export-tokens.bat combined_tokens.json
```

### 2. Working Across Machines

**On Laptop:**
```bash
add-tokens.bat 40000 "Mobile work"
export-tokens.bat laptop_work.json
# Copy to USB or cloud storage
```

**On Desktop:**
```bash
# Import from laptop
import-tokens.bat laptop_work.json --merge

# Continue working
add-tokens.bat 25000 "Desktop work"

# Submit combined total
submit-tokens.bat
```

### 3. Separate Database Instances

**Instance A (Development):**
```bash
add-tokens.bat 60000 "Dev environment testing"
export-tokens.bat dev_tokens.json
```

**Instance B (Staging):**
```bash
# Import dev tokens
import-tokens.bat dev_tokens.json

# Add staging-specific tokens
add-tokens.bat 20000 "Staging validation"

# Export for production
export-tokens.bat staging_tokens.json
```

**Instance C (Production):**
```bash
# Import all accumulated tokens
import-tokens.bat staging_tokens.json
submit-tokens.bat
# Now all tokens tracked in production DB
```

### 4. Backup and Recovery

```bash
# Regular backup
export-tokens.bat backup_$(date +%Y%m%d).json

# If tracking file lost/corrupted
import-tokens.bat backup_20250115.json
```

---

## File Format

### Export File Structure

```json
{
  "export_metadata": {
    "exported_at": "2025-01-15T14:30:00",
    "exported_by": "username",
    "export_version": "1.0",
    "source_machine": "LAPTOP-ABC123"
  },
  "token_data": {
    "branch": "feature/api-improvements",
    "total_tokens": 125847,
    "sessions": [
      {
        "timestamp": "2025-01-15T10:00:00",
        "tokens": 50000,
        "notes": "Initial implementation"
      },
      {
        "timestamp": "2025-01-15T13:00:00",
        "tokens": 75847,
        "notes": "Added tests"
      }
    ],
    "created_at": "2025-01-15T10:00:00",
    "last_updated": "2025-01-15T13:00:00"
  },
  "git_context": {
    "branch": "feature/api-improvements",
    "commit": "a1b2c3d4e5f6..."
  }
}
```

---

## Commands Reference

### Export Commands

```bash
# Basic export
export-tokens.bat output.json

# Python - export current branch
python token_metrics/scripts/export-tokens.py --output tokens.json

# Python - export specific branch
python token_metrics/scripts/export-tokens.py --output tokens.json --branch main

# Python - export without metadata
python token_metrics/scripts/export-tokens.py --output tokens.json --no-metadata
```

### Import Commands

```bash
# Basic import (replaces)
import-tokens.bat tokens.json

# Import and merge
import-tokens.bat tokens.json --merge

# Python - basic import
python token_metrics/scripts/import-tokens.py --input tokens.json

# Python - import and merge
python token_metrics/scripts/import-tokens.py --input tokens.json --merge
```

---

## Workflow Examples

### Team Collaboration Workflow

```
Developer A                Developer B                Developer C
    │                          │                          │
    ├─ Work (50k tokens)       │                          │
    ├─ export-tokens.bat       │                          │
    └─────► tokens_v1.json ────┴────► import --merge     │
                                       Work (30k tokens)   │
                                       export-tokens.bat   │
                               tokens_v2.json ─────────────┴─► import --merge
                                                                Work (20k tokens)
                                                                Total: 100k tokens
                                                                submit-tokens.bat
```

### Multi-Instance Workflow

```
Local Development          Staging Server          Production Database
      │                         │                          │
      ├─ Work (60k tokens)      │                          │
      ├─ export-tokens.bat      │                          │
      └───► dev.json ───────────┴─► import-tokens.bat     │
                                     Test (10k tokens)      │
                                     export-tokens.bat      │
                                 stage.json ────────────────┴─► import-tokens.bat
                                                                 submit-tokens.bat
                                                                 (70k in prod DB)
```

---

## Best Practices

### 1. Naming Convention

Use descriptive filenames:
```bash
export-tokens.bat tokens_feature-name_username_date.json
# Example: tokens_api-work_john_20250115.json
```

### 2. Version Control

Add export files to `.gitignore` (already done):
```gitignore
token_metrics/local_tracking/*.json
*.tokens.json
```

### 3. Regular Exports

Export before major changes:
```bash
# Before submitting
export-tokens.bat backup_pre_submit.json
submit-tokens.bat
```

### 4. Merge vs Replace

- **Replace** (`import-tokens.bat file.json`): Use when starting fresh
- **Merge** (`import-tokens.bat file.json --merge`): Use to combine work

### 5. Verification

Always check after import:
```bash
import-tokens.bat received_tokens.json --merge
show-tokens.bat
# Verify the totals look correct
```

---

## Security & Privacy

### What's Included

- ✅ Token counts
- ✅ Session timestamps
- ✅ Branch names
- ✅ Notes/descriptions
- ✅ Export metadata (who, when, where)

### What's NOT Included

- ❌ Database credentials
- ❌ API keys
- ❌ Code/implementation details
- ❌ Actual conversations/prompts
- ❌ User passwords

### Sharing Guidelines

✅ **Safe to share:**
- Within your development team
- Across your own machines
- For backup purposes

⚠️ **Be cautious:**
- Contains branch names (might reveal feature names)
- Contains export metadata (username, machine name)
- Token counts could indicate project scope

---

## Troubleshooting

### Import says "already exists"

Either:
1. Use `--merge` flag to combine data
2. Or manually reset first: `python token_metrics/scripts/auto-track-tokens.py --reset`

### File format error

Ensure the JSON file is valid:
```bash
python -m json.tool my_tokens.json
```

### Tokens not showing after import

Check the branch name:
```bash
python token_metrics/scripts/auto-track-tokens.py --show
```

The imported data is branch-specific.

### Lost export file

Check common locations:
- Repo root directory
- Downloads folder
- Email attachments
- Shared drives

---

## Advanced Usage

### Script Integration

```python
from token_metrics.scripts.export_tokens import export_tokens
from token_metrics.scripts.import_tokens import import_tokens

# Export
export_tokens('output.json', branch='main')

# Import
import_tokens('input.json', merge=True)
```

### Automation

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
export-tokens.bat "backups/tokens_backup_$DATE.json"
```

### Batch Processing

```bash
# Import multiple files
for file in tokens_*.json; do
    import-tokens.bat "$file" --merge
done
```

---

## Related Documentation

- **Main Guide**: `TOKEN_TRACKING_GUIDE.md`
- **Local Tracking**: `token_metrics/local_tracking/README.md`
- **Full Documentation**: `token_metrics/docs/TOKEN_TRACKING.md`

---

## Summary

The export/import system gives you complete control over your token tracking data:

1. **Export** when you want to share or backup
2. **Import** when you receive data or move machines
3. **Merge** to combine multiple sources
4. **Submit** when ready to record in database

This keeps your instances independent while allowing seamless data transfer! 🚀
