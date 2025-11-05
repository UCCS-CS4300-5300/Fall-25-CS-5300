# Token Tracking System Architecture

## Overview

Complete token tracking system with persistent storage, export/import capabilities, and CI/CD integration.

---

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    TOKEN TRACKING SYSTEM                        │
│                                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐ │
│  │  Local         │  │  Export/Import │  │  CI/CD           │ │
│  │  Tracking      │  │  System        │  │  Integration     │ │
│  └────────────────┘  └────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component 1: Local Tracking

### Purpose
Accumulate tokens across multiple Claude Code sessions before submitting to database.

### Files
- `auto-track-tokens.py` - Core tracking logic
- `add-tokens.bat` - Quick add command
- `show-tokens.bat` - View status
- `submit-tokens.bat` - Submit to database

### Data Flow
```
Claude Code Session
       │
       ↓ (User records token count)
   add-tokens.bat [count] [notes]
       │
       ↓
┌──────────────────────────────────┐
│ token_metrics/local_tracking/    │
│ tokens_[branch].json             │
│                                  │
│ {                                │
│   "branch": "feature/api",       │
│   "total_tokens": 125847,        │
│   "sessions": [                  │
│     {                            │
│       "timestamp": "...",        │
│       "tokens": 50000,           │
│       "notes": "..."             │
│     }                            │
│   ]                              │
│ }                                │
└──────────────────────────────────┘
       │
       ↓ (When ready)
   submit-tokens.bat
       │
       ↓
   temp/claude_local_*.json
       │
       ↓
   Database (TokenUsage table)
```

### Key Features
- ✅ Persistent storage (survives sessions)
- ✅ Branch-specific tracking
- ✅ Session history with timestamps
- ✅ Automatic archiving on submit
- ✅ Gitignored (private data)

---

## Component 2: Export/Import System

### Purpose
Transfer token data between instances, machines, or team members without database access.

### Files
- `export-tokens.py` - Export to portable file
- `import-tokens.py` - Import from portable file
- `export-tokens.bat` - Quick export
- `import-tokens.bat` - Quick import

### Data Flow

#### Export Flow
```
Local Tracking Data
       │
       ↓
   export-tokens.bat output.json
       │
       ↓
┌──────────────────────────────────┐
│ Portable JSON Export             │
│ output.json                      │
│                                  │
│ {                                │
│   "export_metadata": {           │
│     "exported_at": "...",        │
│     "exported_by": "user",       │
│     "source_machine": "..."      │
│   },                             │
│   "token_data": {                │
│     "branch": "...",             │
│     "total_tokens": 125847,      │
│     "sessions": [...]            │
│   },                             │
│   "git_context": {               │
│     "branch": "...",             │
│     "commit": "..."              │
│   }                              │
│ }                                │
└──────────────────────────────────┘
       │
       ↓ (Share via email, USB, cloud, etc.)
   Different Machine/Instance
```

#### Import Flow
```
Received Export File
       │
       ↓
   import-tokens.bat file.json --merge
       │
       ├─ Check existing data
       ├─ Validate JSON structure
       ├─ Display import summary
       │
       ↓ (User confirms)
   Merge/Replace Local Tracking
       │
       ↓
┌──────────────────────────────────┐
│ Updated Local Tracking           │
│ tokens_[branch].json             │
│                                  │
│ {                                │
│   "total_tokens": 200000,        │
│   "sessions": [                  │
│     ...(existing)...,            │
│     ...(imported)...             │
│   ],                             │
│   "import_history": [            │
│     {                            │
│       "imported_at": "...",      │
│       "imported_from": "...",    │
│       "tokens_added": 75000      │
│     }                            │
│   ]                              │
│ }                                │
└──────────────────────────────────┘
```

### Key Features
- ✅ Platform-independent (JSON format)
- ✅ Merge or replace modes
- ✅ Import history tracking
- ✅ Metadata for traceability
- ✅ No database dependency

---

## Component 3: CI/CD Integration

### Purpose
Automatically track and report token usage in GitHub Actions pipeline.

### Files
- `import-token-usage.py` - Import CI/CD temp files
- `report-token-metrics.py` - Generate reports
- `CI.yml` - GitHub Actions workflow

### Data Flow
```
Git Push
   │
   ↓
┌─────────────────────────────────────┐
│ GitHub Actions: ai-review Job      │
│                                     │
│ 1. Run OpenAI code review          │
│ 2. Track tokens → temp/*.json      │
│ 3. Upload artifact                 │
└─────────────────────────────────────┘
   │
   ↓ (Artifact uploaded)
┌─────────────────────────────────────┐
│ GitHub Actions: token-metrics Job  │
│                                     │
│ 1. Download artifacts              │
│ 2. Import temp/*.json to DB        │
│ 3. Generate report                 │
│ 4. Display in summary              │
└─────────────────────────────────────┘
   │
   ↓
┌─────────────────────────────────────┐
│ Token Metrics Report                │
│                                     │
│ ══════════════════════════════════  │
│ TOKEN USAGE BY BRANCH               │
│ ══════════════════════════════════  │
│                                     │
│ Branch                  Tokens      │
│ ─────────────────────────────────   │
│ feature/api            125,847      │
│ main                    98,234      │
│ bugfix/auth             73,567      │
│ ─────────────────────────────────   │
│ TOTAL                  297,648      │
│                                     │
└─────────────────────────────────────┘
```

### Key Features
- ✅ Automatic on every push
- ✅ Branch-specific breakdown
- ✅ Historical tracking
- ✅ Cost estimation
- ✅ Visible in GitHub Actions UI

---

## Complete End-to-End Flow

### Scenario: Developer working across 3 sessions

```
┌─────────────────────────────────────────────────────────────────┐
│ Session 1: Initial Development (Laptop)                        │
└─────────────────────────────────────────────────────────────────┘
         │
         ↓ Claude Code work (50k tokens)
    add-tokens.bat 50000 "Initial API setup"
         │
         ↓
    [Local: tokens_feature-api.json]
    total_tokens: 50000
    sessions: 1
         │
         ↓ Export for backup
    export-tokens.bat backup_day1.json

┌─────────────────────────────────────────────────────────────────┐
│ Session 2: Continue Development (Desktop)                      │
└─────────────────────────────────────────────────────────────────┘
         │
         ↓ Transfer backup_day1.json to desktop
    import-tokens.bat backup_day1.json
         │
         ↓ Claude Code work (40k tokens)
    add-tokens.bat 40000 "Add authentication"
         │
         ↓
    [Local: tokens_feature-api.json]
    total_tokens: 90000
    sessions: 2

┌─────────────────────────────────────────────────────────────────┐
│ Session 3: Testing & Documentation (Laptop again)              │
└─────────────────────────────────────────────────────────────────┘
         │
         ↓ Get latest from desktop
    import-tokens.bat desktop_export.json --merge
         │
         ↓ Claude Code work (30k tokens)
    add-tokens.bat 30000 "Tests and docs"
         │
         ↓
    [Local: tokens_feature-api.json]
    total_tokens: 120000
    sessions: 3
         │
         ↓ Submit to database
    submit-tokens.bat
         │
         ↓
    [Database: TokenUsage table]
    120,000 tokens recorded for feature/api branch
         │
         ↓ Push to GitHub
    git push
         │
         ↓
    [CI/CD Pipeline]
    - AI review runs (adds ~10k tokens)
    - Token metrics job imports all data
    - Report generated
         │
         ↓
    [GitHub Actions Summary]
    Branch: feature/api
    Total: 130,000 tokens
    Cost: $0.35
```

---

## Multi-Instance Architecture

### Scenario: Dev → Staging → Production

```
┌─────────────────────────────────────┐
│ Development Instance (DB #1)        │
│                                     │
│ • Local development work            │
│ • Token tracking: 60k tokens        │
│ • Export: dev_tokens.json           │
└─────────────────────────────────────┘
            │
            ↓ (Export file shared)
┌─────────────────────────────────────┐
│ Staging Instance (DB #2)            │
│                                     │
│ • Import: dev_tokens.json           │
│ • Staging tests: 20k tokens         │
│ • Total: 80k tokens                 │
│ • Export: staging_tokens.json       │
└─────────────────────────────────────┘
            │
            ↓ (Export file shared)
┌─────────────────────────────────────┐
│ Production Instance (DB #3)         │
│                                     │
│ • Import: staging_tokens.json       │
│ • Submit to prod database           │
│ • Total recorded: 80k tokens        │
│ • CI/CD reports show full usage     │
└─────────────────────────────────────┘
```

**Key Point**: Each database is separate, but token data flows through export/import files!

---

## Storage Locations

### Local Machine
```
token_metrics/
├── local_tracking/
│   ├── tokens_[branch].json          # Active tracking
│   ├── tokens_*_archived_*.json      # Submitted/reset data
│   └── README.md
└── scripts/
    ├── auto-track-tokens.py
    ├── export-tokens.py
    └── import-tokens.py
```

### Portable/Shared
```
Anywhere you save them:
├── my_work.json                       # Export file
├── team_tokens.json                   # Shared export
├── backup_20250115.json               # Backup
└── dev_to_prod.json                   # Instance transfer
```

### Database
```
TokenUsage Table:
├── id
├── created_at
├── git_branch
├── model_name
├── prompt_tokens
├── completion_tokens
├── total_tokens
└── estimated_cost

MergeTokenStats Table:
├── id
├── merge_date
├── source_branch
├── cumulative_total_tokens
├── cumulative_cost
└── ...
```

### CI/CD (Temporary)
```
temp/
├── token_usage_*.json                 # AI review tokens
├── claude_local_*.json                # Local tracking exports
└── (cleaned after import)

GitHub Actions Artifacts:
└── ai-review-token-data/
    └── token_usage_*.json
```

---

## Security & Privacy Model

### Private (Gitignored)
- ✅ `token_metrics/local_tracking/*.json` - Your personal tracking
- ✅ Export files (you control where they go)
- ✅ `temp/*.json` - Temporary data

### Shared (In Git)
- ✅ Scripts and batch files
- ✅ Documentation
- ✅ Database models (structure only, not data)

### Database
- ✅ TokenUsage records (after submit)
- ✅ MergeTokenStats (aggregated data)
- ⚠️ Access controlled by Django permissions

---

## Benefits Summary

| Feature | Benefit |
|---------|---------|
| **Local Tracking** | Accumulate across sessions |
| **Export/Import** | Share without database access |
| **Gitignored** | Keep personal data private |
| **Branch-Specific** | Accurate attribution |
| **Merge Support** | Combine multiple sources |
| **CI/CD Reports** | Team visibility |
| **Archive History** | Never lose data |
| **Cost Tracking** | Budget awareness |

---

## Technology Stack

- **Language**: Python 3
- **Data Format**: JSON
- **Database**: Django ORM (PostgreSQL)
- **CI/CD**: GitHub Actions
- **Version Control**: Git
- **OS Support**: Windows (batch files), Linux/Mac (can use Python directly)

---

## Future Enhancements (Potential)

- [ ] Auto-detect token usage from Claude Code logs
- [ ] Web UI for viewing/managing tokens
- [ ] API endpoints for programmatic access
- [ ] Real-time sync across machines
- [ ] Budget alerts/warnings
- [ ] Integration with other AI tools

---

This architecture provides a complete, flexible token tracking system that works across any development workflow! 🚀
