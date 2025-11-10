# Granular Token Statistics - Complete Documentation

## 📊 Overview

The token tracking system captures and displays **comprehensive granular statistics** across all dimensions, automatically displayed in your GitHub Actions pipeline on merge to main.

---

## ✅ What Statistics Are Captured

### 1. Per-Session Granular Data

Every token session captures:

| Field | Description | Example |
|-------|-------------|---------|
| **timestamp** | Exact date/time of session | `2025-01-09T14:30:45` |
| **git_branch** | Branch where tokens were used | `feature/auth-system` |
| **commit_sha** | Specific commit (when available) | `abc123def456...` |
| **model_name** | AI model used | `claude-sonnet-4-5-20250929` |
| **endpoint** | API endpoint/operation | `messages`, `generate_report_scores` |
| **prompt_tokens** | Input tokens (requests) | `36,000` |
| **completion_tokens** | Output tokens (responses) | `9,230` |
| **total_tokens** | Combined total | `45,230` |
| **source** | Where tokens came from | `local-claude-code`, `ai-review`, `auto-tracked` |
| **notes** | Developer annotations | `"Fixed authentication bug"` |
| **estimated_cost** | Calculated cost | `$0.2048` |

### 2. Aggregated Statistics

The system automatically calculates:

- **Total across all branches**
- **Per-branch totals**
- **Per-model breakdowns**
- **Per-endpoint analysis**
- **Daily/weekly/monthly aggregations**
- **Cost estimates with detailed breakdowns**
- **Usage trends and projections**

---

## 📈 Report Sections (Displayed in GitHub Pipeline)

When you merge to main, the pipeline automatically generates and displays this comprehensive report:

### Section 1: OVERALL STATISTICS

```
═══════════════════════════════════════════════════════════════════════
📊 OVERALL STATISTICS
═══════════════════════════════════════════════════════════════════════

  📝 Total Records:        127
  🔢 Total Tokens:         542,680
  📥 Prompt Tokens:        434,144
  📤 Completion Tokens:    108,536
  💰 Estimated Cost:       $2.9302

  📊 Average per Session:  4,272 tokens
  📈 Largest Session:      67,450 tokens
  📉 Smallest Session:     1,240 tokens
```

**Shows:**
- Total number of sessions recorded
- Complete token breakdown (input/output)
- Total estimated cost
- Session statistics (min/max/average)

---

### Section 2: CURRENT BRANCH DETAILED STATISTICS

```
═══════════════════════════════════════════════════════════════════════
🌳 CURRENT BRANCH: feature/scoring-transparency
═══════════════════════════════════════════════════════════════════════

  📊 Sessions:             15
  🔢 Total Tokens:         67,450
  📥 Prompt Tokens:        53,960
  📤 Completion Tokens:    13,490
  💰 Estimated Cost:       $0.3643
  📊 Avg per Session:      4,497 tokens
  📈 % of Total Usage:     12.4%
  📅 First Use:            2025-01-07 10:30:15
  📅 Last Use:             2025-01-09 16:45:30

  📅 Daily Activity on This Branch:
     2025-01-09:        22,100 tokens  (5 sessions)  $0.1192
     2025-01-08:        18,350 tokens  (4 sessions)  $0.0990
     2025-01-07:        15,000 tokens  (3 sessions)  $0.0809
     2025-01-06:        12,000 tokens  (3 sessions)  $0.0647
```

**Shows:**
- Detailed stats for the current branch
- Daily breakdown of activity
- First and last usage timestamps
- Percentage of total project usage
- Per-session averages

---

### Section 3: TIME-BASED ANALYSIS

```
═══════════════════════════════════════════════════════════════════════
📅 TIME-BASED ANALYSIS
═══════════════════════════════════════════════════════════════════════

  🕐 Last 24 Hours:
     Sessions:  7
     Tokens:    32,100
     Cost:      $0.1732

  📅 Last 7 Days:
     Sessions:  42
     Tokens:    189,450
     Cost:      $1.0219
     Daily Avg: 27,064 tokens ($0.1460/day)
     📊 Monthly Projection: 811,920 tokens ($4.38/month)

  📅 Last 30 Days:
     Sessions:  127
     Tokens:    542,680
     Cost:      $2.9302
```

**Shows:**
- Recent activity (24 hours, 7 days, 30 days)
- Daily averages
- Monthly cost projections
- Usage patterns over time

---

### Section 4: BRANCH BREAKDOWN (Top 10)

```
═══════════════════════════════════════════════════════════════════════
🌿 BRANCH BREAKDOWN (Top 10)
═══════════════════════════════════════════════════════════════════════

  Rank   Branch                                    Tokens        Sessions         Cost
  ------ ------------------------------------- --------------- ---------- ------------
→  1    feature/scoring-transparency               67,450         15    $   0.3643
   2    feature/pdf-export                         58,920         12    $   0.3179
   3    feature/auth-system                        45,230          8    $   0.2440
   4    main                                       38,100         18    $   0.2056
   5    bugfix/test-failures                       22,800          6    $   0.1230
   6    feature/ui-improvements                    18,450          5    $   0.0995
   7    bugfix/authentication                      12,600          4    $   0.0680
   8    feature/api-endpoints                      10,200          3    $   0.0550
   9    refactor/database                           8,900          2    $   0.0480
   10   feature/reporting                           7,500          2    $   0.0405
```

**Shows:**
- Top 10 branches by token usage
- Total tokens per branch
- Number of sessions per branch
- Estimated cost per branch
- Current branch highlighted with →

---

### Section 5: MODEL & ENDPOINT ANALYSIS

```
═══════════════════════════════════════════════════════════════════════
🤖 MODEL & ENDPOINT ANALYSIS
═══════════════════════════════════════════════════════════════════════

  📱 By Model:
     Model                                              Tokens    Sessions         Cost
     --------------------------------------------- --------------- ---------- ------------
     claude-sonnet-4-5-20250929                        485,120        110    $   2.6177
     gpt-4-turbo                                        42,560         12    $   0.2655
     claude-sonnet-3-5-20241022                         15,000          5    $   0.0810

  🔗 By Endpoint:
     Endpoint                            Total Tokens    Sessions   Avg/Session
     ------------------------------ --------------- ---------- ---------------
     messages                               425,680         95          4,481
     generate_report_scores                  58,000         18          3,222
     generate_report_rationales              32,000         10          3,200
     generate_report_feedback                27,000          4          6,750
```

**Shows:**
- Breakdown by AI model
- Usage by API endpoint/operation
- Average tokens per endpoint
- Cost analysis by model

---

### Section 6: RECENT ACTIVITY (Last 10 Sessions)

```
═══════════════════════════════════════════════════════════════════════
📝 RECENT ACTIVITY (Last 10 Sessions)
═══════════════════════════════════════════════════════════════════════

  Timestamp            Branch                    Model        Endpoint            Tokens       Cost
  -------------------- ------------------------- ------------ --------------- ------------ ----------
  2025-01-09 16:45:30  feature/scoring           claude       messages              22,100   $ 0.1192
  2025-01-09 14:30:15  feature/scoring           claude       messages              18,350   $ 0.0990
  2025-01-09 10:15:00  feature/pdf-export        claude       generate_repo         15,800   $ 0.0853
  2025-01-08 16:20:45  feature/auth-system       gpt-4        messages               8,900   $ 0.0556
  2025-01-08 14:55:20  main                      claude       messages               6,500   $ 0.0351
  2025-01-08 11:30:10  feature/scoring           claude       messages              12,400   $ 0.0669
  2025-01-07 15:45:30  bugfix/test-failures      claude       messages               5,600   $ 0.0302
  2025-01-07 13:20:15  feature/ui-improvements   claude       messages               7,800   $ 0.0421
  2025-01-07 10:30:45  feature/scoring           claude       messages              15,000   $ 0.0809
  2025-01-06 16:10:25  main                      claude       messages               9,200   $ 0.0496
```

**Shows:**
- Last 10 token sessions with full details
- Timestamp, branch, model, endpoint
- Token counts and costs
- Most recent activity first

---

### Section 7: DETAILED COST ANALYSIS

```
═══════════════════════════════════════════════════════════════════════
💰 DETAILED COST ANALYSIS
═══════════════════════════════════════════════════════════════════════

  🤖 claude-sonnet-4-5-20250929
     Prompt:           388,096 tokens × $3.00/M = $1.1643
     Completion:        97,024 tokens × $15.00/M = $1.4554
     Total Cost:  $2.6197

  🤖 gpt-4-turbo
     Prompt:            34,048 tokens × $2.50/M = $0.0851
     Completion:         8,512 tokens × $10.00/M = $0.0851
     Total Cost:  $0.1702

  💵 TOTAL ESTIMATED COST: $2.9302
```

**Shows:**
- Detailed cost breakdown by model
- Separate prompt and completion costs
- Pricing rates per 1M tokens
- Individual and total costs

---

### Section 8: INSIGHTS & RECOMMENDATIONS

```
═══════════════════════════════════════════════════════════════════════
💡 INSIGHTS & RECOMMENDATIONS
═══════════════════════════════════════════════════════════════════════

  📊 Most Active Branch:
     feature/scoring-transparency - 67,450 tokens ($0.3643)

  📈 Usage Trend: INCREASING (+32.4% vs previous week)
     Current week avg:  27,064 tokens/day
     Previous week avg: 20,440 tokens/day
```

**Shows:**
- Most expensive branch
- Week-over-week trend analysis
- Usage pattern insights
- Cost optimization suggestions

---

## 🔄 How It Works in GitHub Actions

### Automatic Flow

1. **Developer commits code** with Claude Code token usage
   - Tokens saved to `temp/claude_local_*.json` via git hooks

2. **Push to GitHub** (any branch)
   - Git hook files included in commit
   - Token data committed to temp/

3. **CI/CD runs** on pull request or merge to main
   - `ai-review` job runs AI code review (generates more tokens)
   - Token data saved to `temp/token_usage_*.json`

4. **Token-metrics job runs** (after tests pass)
   - Downloads all token data from artifacts
   - Imports ALL JSON files from temp/
   - Runs `report-token-metrics.py`
   - Generates comprehensive report

5. **Report displayed in GitHub Actions**
   - Visible in workflow run summary
   - All granular stats shown
   - Formatted tables and sections
   - Automatic cost calculations

### GitHub Actions Job Configuration

From `.github/workflows/CI.yml` (lines 581-742):

```yaml
token-metrics:
  name: Report Token Usage Metrics
  runs-on: ubuntu-latest
  needs: [test, ai-review]
  if: always() && (needs.test.result == 'success' || needs.test.result == 'failure')

  steps:
    # ... download artifacts, setup python ...

    - name: Import Token Usage from All Sources
      run: |
        python token_metrics/scripts/import-token-usage.py

    - name: Generate Token Metrics Report
      run: |
        python token_metrics/scripts/report-token-metrics.py | tee token-metrics-report.txt

    - name: Add Token Metrics to Summary
      run: |
        cat token-metrics-report.txt >> $GITHUB_STEP_SUMMARY
```

**Result:** Full report visible in every workflow run!

---

## 📊 Data Storage & Persistence

### 1. Temporary Files (Pre-Import)

**Location:** `temp/*.json`

**Formats:**
- `claude_local_YYYYMMDD_HHMMSS.json` - Local Claude Code sessions
- `token_usage_TIMESTAMP.json` - AI review tokens
- `*_tokens.json` - Exported token files

**Structure:**
```json
{
  "timestamp": "2025-01-09T14:30:45",
  "git_branch": "feature/scoring-transparency",
  "commit_sha": "abc123def456",
  "model_name": "claude-sonnet-4-5-20250929",
  "endpoint": "messages",
  "prompt_tokens": 12000,
  "completion_tokens": 3000,
  "total_tokens": 15000,
  "source": "auto-tracked",
  "notes": "Implemented scoring transparency"
}
```

### 2. Local Tracking Files (Per-Branch Cumulative)

**Location:** `token_metrics/local_tracking/tokens_<branch>.json`

**Purpose:** Track cumulative usage per branch locally

**Structure:**
```json
{
  "branch": "feature/scoring-transparency",
  "total_tokens": 67450,
  "sessions": [
    {
      "timestamp": "2025-01-09T14:30:45",
      "input_tokens": 12000,
      "output_tokens": 3000,
      "total_tokens": 15000,
      "notes": "Session notes"
    }
  ],
  "created_at": "2025-01-07T10:30:15",
  "last_updated": "2025-01-09T16:45:30"
}
```

### 3. Database (Permanent Records)

**Table:** `active_interview_app_tokenusage`

**Schema:**
```sql
CREATE TABLE token_usage (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    git_branch VARCHAR(255),
    model_name VARCHAR(100),
    endpoint VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    estimated_cost DECIMAL(10,4),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Accessed via Django ORM:**
```python
from active_interview_app.token_usage_models import TokenUsage

# Query all usage
total = TokenUsage.objects.aggregate(Sum('total_tokens'))

# Query by branch
branch_stats = TokenUsage.objects.filter(
    git_branch='feature/scoring-transparency'
).aggregate(
    total=Sum('total_tokens'),
    avg=Avg('total_tokens'),
    count=Count('id')
)
```

---

## 🎯 Example: Complete Tracking Flow

### Scenario: Developer working on a feature

```bash
# 1. Developer starts feature
git checkout -b feature/new-auth

# 2. Work with Claude Code (multiple sessions)
#    → Git hooks auto-track tokens on each commit
git commit -m "Add login form"
# ✅ Auto-tracked: 12,000 input + 3,000 output tokens

git commit -m "Add validation"
# ✅ Auto-tracked: 15,000 input + 4,200 output tokens

git commit -m "Add tests"
# ✅ Auto-tracked: 8,500 input + 2,100 output tokens

# 3. Check local usage
track-tokens.bat --show
# Shows: 39,800 tokens on feature/new-auth

# 4. Create PR and merge to main
git push origin feature/new-auth
# Creates PR, CI/CD runs

# 5. On merge to main
# GitHub Actions automatically:
#   ├─ Imports all temp/*.json files
#   ├─ Stores in database
#   ├─ Generates comprehensive report
#   └─ Displays in workflow summary

# 6. View report in GitHub Actions
# Report shows:
#   ✅ Total tokens: 39,800
#   ✅ Cost: $0.2146
#   ✅ 3 sessions
#   ✅ Daily breakdown
#   ✅ Comparison to other branches
#   ✅ All granular statistics
```

---

## 💡 What Makes These Stats "Granular"?

| Level | What's Captured | Example Use Case |
|-------|----------------|------------------|
| **Individual Session** | Every API call tracked separately | "This specific debugging session cost $0.15" |
| **Hourly** | Activity by hour of day | "Most tokens used between 2-4 PM" |
| **Daily** | Day-by-day breakdown | "Monday had 35% more usage than Friday" |
| **Weekly** | Week-over-week trends | "Usage increased 20% this week" |
| **Per-Branch** | Complete branch lifetime stats | "This feature cost $2.50 total" |
| **Per-Model** | Claude vs GPT-4 usage | "90% of tokens are Claude, 10% GPT-4" |
| **Per-Endpoint** | API operation breakdown | "Report generation uses 40% of tokens" |
| **Per-Developer** | Individual attribution | "Team member A used 45% of tokens" |
| **Cost Breakdown** | Prompt vs completion costs | "Completion tokens are 75% of cost" |

---

## 🚀 Benefits of Granular Tracking

### 1. Cost Management
- See exactly where money is being spent
- Identify expensive features early
- Make informed decisions about AI usage
- Set and monitor budgets per feature

### 2. Performance Insights
- Understand which operations use most tokens
- Optimize expensive API calls
- Track improvements over time
- Compare different approaches

### 3. Team Accountability
- Transparent usage tracking
- Fair cost allocation
- Usage patterns visible
- Encourage efficient AI use

### 4. Planning & Forecasting
- Monthly projections based on real data
- Trend analysis (increasing/decreasing)
- Budget planning for future features
- Cost estimation for new work

### 5. Documentation & Auditing
- Complete historical record
- Export data for reports
- Track usage over project lifetime
- Compliance and billing records

---

## 📚 Accessing Granular Data

### In GitHub Actions (Automatic)
✅ Displayed automatically on every merge to main
✅ Full report in workflow summary
✅ No manual steps required

### Locally (Manual)
```bash
# Quick summary
track-tokens.bat --show

# Detailed trends
track-tokens.bat --trends

# Complete analysis
track-tokens.bat --all

# Export to CSV
track-tokens.bat --export monthly_jan2025.csv

# Interactive dashboard
track-tokens.bat --dashboard
```

### Via Django Admin
```python
# In Django shell or admin
from active_interview_app.token_usage_models import TokenUsage

# Get granular stats
stats = TokenUsage.get_branch_summary('feature/scoring-transparency')
# Returns: {
#   'total_tokens': 67450,
#   'total_cost': 0.3643,
#   'by_model': {...},
#   'by_endpoint': {...},
#   'daily_breakdown': [...]
# }
```

---

## ✅ Verification Checklist

To ensure granular stats are working:

- [ ] **Git hooks installed** - Automatic tracking enabled
- [ ] **Temp files generated** - Check `temp/` has .json files
- [ ] **GitHub Actions configured** - CI.yml has token-metrics job
- [ ] **Database migrations run** - TokenUsage model exists
- [ ] **Report generates locally** - `python report-token-metrics.py` works
- [ ] **Pipeline displays report** - Check GitHub Actions summary

---

## 🆘 Troubleshooting

### No stats in pipeline?
**Check:**
1. Are temp files being committed? `git status temp/`
2. Is token-metrics job running? Check GitHub Actions logs
3. Are there any import errors? Check import-token-usage.py output

### Stats seem incomplete?
**Check:**
1. Git hooks installed: `ls .git/hooks/post-commit`
2. Auto-tracking working: commit and check for prompts
3. Temp files created: `ls temp/*.json`

### Costs seem wrong?
**Update pricing in report-token-metrics.py:**
```python
# Line 77-96: Update model pricing
if 'claude-sonnet-4-5' in model_name.lower():
    prompt_cost = (prompt_tokens / 1_000_000) * 3.00  # Update here
    completion_cost = (completion_tokens / 1_000_000) * 15.00  # Update here
```

---

## 📊 Summary

**You now have:**
- ✅ **8 comprehensive report sections** with all granular data
- ✅ **Automatic display** in GitHub Actions on every merge
- ✅ **Per-session, daily, weekly, monthly** breakdowns
- ✅ **Branch, model, endpoint** analysis
- ✅ **Detailed cost calculations** with pricing transparency
- ✅ **Trend analysis** and projections
- ✅ **Recent activity** tracking
- ✅ **Complete historical records** in database

**All automatically visible in your pipeline! 🎉**

---

**Last Updated:** January 2025
**Version:** 2.0 (Granular Statistics Enhancement)
