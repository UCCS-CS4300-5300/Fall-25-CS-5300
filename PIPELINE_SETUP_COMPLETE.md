# ✅ Pipeline Token Tracking - Ready to Use!

## What's Already Set Up

Your token tracking system is **fully configured** and ready to run in the GitHub Actions pipeline! 🎉

### ✅ What Happens Automatically

**Every time a PR is merged to `main`:**

1. **GitHub Actions workflow triggers** (.github/workflows/token-tracking.yml)
2. **Detects the merged branch** from the commit message
3. **Queries the database** for all tokens used on that branch
4. **Saves merge record** to database with:
   - Total tokens used by that branch
   - Estimated cost for that branch
   - **Cumulative total tokens** (sum of ALL merges)
   - **Cumulative total cost** (sum of ALL merges)
5. **Posts a comment** on the PR with summary
6. **Archives reports** for 90 days

### ✅ What's Configured

| Component | Status | Location |
|-----------|--------|----------|
| GitHub Actions Workflow | ✅ Ready | `.github/workflows/token-tracking.yml` |
| Database Models | ✅ Created | `active_interview_app/merge_stats_models.py` |
| Management Command | ✅ Ready | `management/commands/record_merge.py` |
| Django Admin | ✅ Configured | Can view data at `/admin/` |
| Cumulative Tracking | ✅ Automatic | Calculates on each merge |

## 🚀 Quick Start

### Option 1: Automatic Setup (Recommended)

```bash
# Run the automated setup script
chmod +x SETUP_TOKEN_TRACKING.sh
./SETUP_TOKEN_TRACKING.sh
```

### Option 2: Manual Setup

```bash
cd active_interview_backend

# Create database tables
python manage.py makemigrations
python manage.py migrate

# Verify setup
python manage.py shell -c "from active_interview_app.merge_stats_models import MergeTokenStats; print('✓ Setup complete!')"
```

## 📊 Example: How It Works

Let's say you merge 3 feature branches:

```
┌──────────────────────────────────────────────────────────────┐
│ Merge #1: feature/login → main                               │
├──────────────────────────────────────────────────────────────┤
│ Branch Tokens:      15,000                                   │
│ Branch Cost:        $0.63                                    │
│ Cumulative Tokens:  15,000  ← First merge                   │
│ Cumulative Cost:    $0.63                                    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Merge #2: feature/oauth → main                               │
├──────────────────────────────────────────────────────────────┤
│ Branch Tokens:      21,200                                   │
│ Branch Cost:        $0.89                                    │
│ Cumulative Tokens:  36,200  ← 15,000 + 21,200               │
│ Cumulative Cost:    $1.52   ← $0.63 + $0.89                 │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Merge #3: feature/chat → main                                │
├──────────────────────────────────────────────────────────────┤
│ Branch Tokens:      42,500                                   │
│ Branch Cost:        $1.79                                    │
│ Cumulative Tokens:  78,700  ← Running total!                │
│ Cumulative Cost:    $3.31   ← Running total!                │
└──────────────────────────────────────────────────────────────┘
```

**The cumulative totals keep growing with each merge, giving you the total project cost!**

## 📱 Where to See Results

### 1. GitHub PR Comments (Automatic)

After merging, check your PR for this comment:

```
🎯 Token Usage Summary

This PR has been merged to main. Here's the token usage impact:

Branch Usage
- Total Tokens: 21,200
- Estimated Cost: $0.89

Cumulative Totals (All Merges)
- Total Tokens: 78,700
- Total Cost: $3.31

View the full workflow run for detailed reports.
```

### 2. GitHub Actions Tab

1. Go to **Actions** tab in GitHub
2. Click on **"Token Usage Tracking"** workflow
3. View the job summary with full reports

### 3. Django Admin Interface

```bash
# Create superuser if you haven't
python manage.py createsuperuser

# Then visit:
# http://localhost:8000/admin/
# Navigate to: Merge Token Statistics
```

You'll see a table with all merges and cumulative totals!

### 4. Query in Python/Shell

```python
from active_interview_app.merge_stats_models import MergeTokenStats

# Get total cumulative tokens
total_tokens = MergeTokenStats.get_total_cumulative_tokens()
total_cost = MergeTokenStats.get_total_cumulative_cost()

print(f"Total tokens from all merges: {total_tokens:,}")
print(f"Total cost from all merges: ${total_cost:.2f}")

# Get all merge records
merges = MergeTokenStats.objects.all().order_by('-merge_date')
for merge in merges:
    print(f"{merge.source_branch}: {merge.total_tokens:,} tokens (Cumulative: {merge.cumulative_total_tokens:,})")

# Get top 5 most expensive branches
top = MergeTokenStats.get_top_branches(limit=5)
for branch in top:
    print(f"{branch['source_branch']}: ${branch['total_cost']:.2f}")
```

## 🔄 Pipeline Workflow Details

### When Does It Run?

The workflow triggers on:
- ✅ **Push to main** (when PR is merged)
- ✅ **Manual dispatch** (can trigger manually from Actions tab)

### What Does It Do?

```yaml
1. Detect merged branch from commit message
   ↓
2. Start Django container with database
   ↓
3. Run migrations to ensure tables exist
   ↓
4. Run: python manage.py record_merge --source-branch <branch>
   ↓
5. Calculate tokens used by that branch
   ↓
6. Save to database with cumulative totals
   ↓
7. Generate full token usage report
   ↓
8. Post PR comment with summary
   ↓
9. Upload reports as artifacts (90 day retention)
```

## 🎯 Key Features

### Cumulative Tracking
- ✅ **Running total** of all merged branches
- ✅ **Never resets** - grows over project lifetime
- ✅ **Automatic calculation** on each merge
- ✅ Saved in database permanently

### Per-Branch Analysis
- ✅ See exactly what each feature cost
- ✅ Compare branches by token usage
- ✅ Identify expensive features

### Historical Records
- ✅ Complete history of all merges
- ✅ Track who merged what and when
- ✅ Link to original PR
- ✅ View trends over time

## 📋 Testing the Setup

### Test Merge Tracking Manually

```bash
cd active_interview_backend

# Record a test merge
python manage.py record_merge \
  --source-branch test-branch \
  --commit abc123 \
  --merged-by "Your Name"

# View the result
python manage.py shell -c "
from active_interview_app.merge_stats_models import MergeTokenStats
latest = MergeTokenStats.objects.latest('merge_date')
print(f'Source: {latest.source_branch}')
print(f'Tokens: {latest.total_tokens:,}')
print(f'Cumulative: {latest.cumulative_total_tokens:,}')
"
```

### Test in GitHub Actions

1. Go to **Actions** tab
2. Select **"Token Usage Tracking"** workflow
3. Click **"Run workflow"**
4. Enter a test branch name
5. Click **"Run workflow"** button
6. Watch it run and check the summary!

## 🔍 Verify Everything Works

Run these commands to verify the setup:

```bash
cd active_interview_backend

# 1. Check migrations
python manage.py showmigrations | grep active_interview_app

# 2. Check models are registered
python manage.py shell -c "
from active_interview_app.merge_stats_models import MergeTokenStats
from active_interview_app.token_usage_models import TokenUsage
print('✓ MergeTokenStats model loaded')
print('✓ TokenUsage model loaded')
"

# 3. Check admin is configured
python manage.py shell -c "
from django.contrib import admin
print('✓ Admin site configured')
"

# 4. Test cumulative calculation
python manage.py shell -c "
from active_interview_app.merge_stats_models import MergeTokenStats
total = MergeTokenStats.get_total_cumulative_tokens()
print(f'Current cumulative total: {total:,} tokens')
"
```

## 📁 Important Files

| File | Purpose |
|------|---------|
| `.github/workflows/token-tracking.yml` | GitHub Actions workflow |
| `active_interview_app/merge_stats_models.py` | Database model with cumulative logic |
| `active_interview_app/management/commands/record_merge.py` | Recording command |
| `active_interview_app/admin.py` | Django admin interface |
| `MERGE_TOKEN_TRACKING.md` | Complete documentation |
| `MERGE_TRACKING_QUICKSTART.md` | Quick reference guide |

## 🆘 Troubleshooting

### Workflow Didn't Run After Merge

**Check:**
1. Was it merged to `main`? (Only runs on main)
2. Check Actions tab for any failed runs
3. Verify `.github/workflows/token-tracking.yml` exists

### "No token data found" in Report

**This is normal if:**
- The branch didn't make any API calls yet
- Token tracking not enabled in views.py (see `EXAMPLE_TOKEN_TRACKING.md`)

**To add token tracking to your code:**
See `EXAMPLE_TOKEN_TRACKING.md` for exact code examples

### Cumulative Total Seems Wrong

**Verify:**
```python
# Check all merge records
from active_interview_app.merge_stats_models import MergeTokenStats
for m in MergeTokenStats.objects.all().order_by('merge_date'):
    print(f"{m.merge_date}: {m.cumulative_total_tokens:,}")
```

The cumulative should increase with each record.

### Can't See Data in Admin

1. Create superuser: `python manage.py createsuperuser`
2. Visit: http://localhost:8000/admin/
3. Look for "Merge Token Statistics" section

## 💰 Cost Tracking

The system calculates costs using these default rates:
- **Prompt tokens:** $0.03 per 1,000 tokens
- **Completion tokens:** $0.06 per 1,000 tokens

To update rates, edit:
- `active_interview_app/management/commands/record_merge.py` (line ~49)

## 🎉 Summary

You now have:
- ✅ **Automatic tracking** on every merge to main
- ✅ **Cumulative totals** saved in database
- ✅ **PR comments** with token summaries
- ✅ **GitHub Actions integration**
- ✅ **Django Admin interface** for viewing data
- ✅ **90-day report archival**
- ✅ **Historical tracking** of all merges

**Just merge your PRs normally - everything else is automatic!** 🚀

---

**Next Step:** Run the setup script, then merge a PR to see it in action!

```bash
./SETUP_TOKEN_TRACKING.sh
```
