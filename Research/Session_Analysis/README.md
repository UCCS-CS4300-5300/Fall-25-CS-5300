# Claude Code Session Analysis - Research Package

**Complete toolkit for analyzing Claude Code session logs for SWE research**

---

## 📊 Key Findings

**Research Question 1.2 - Test Failure Analysis:**
- **First-run failure rate: 57.14%** - Tests fail over half the time on first execution
- **Success rate: 100%** - All sessions eventually succeed through iteration
- **Average iterations: 3.33** - Efficient debugging process
- **Regression detection: 55.56%** - Tests catch breaking changes effectively

**Research Question 2 - Development Patterns:**
- **100% completion rate** - All meaningful sessions resulted in working code
- **Error-driven reprompts: 16.82%** - Low error rate
- **Iterative refinement: 10.03%** - Normal collaborative development

---

## 📁 Package Contents

```
Session_Analysis/
├── session_analysis_results.md  # Complete research findings (ready for paper)
├── research_metrics.json        # Structured data for analysis
├── analyze_sessions.py          # Reusable analysis script (Version 3)
├── README.md                    # This file
└── results/                     # Analysis output
    ├── analysis_results_corrected.json
    ├── analysis_report_corrected.txt
    └── session_summary_corrected.csv

../logs/                         # Test sequence logs (auto-generated)
├── test_sequence_*_historical.md   # Historical test sequences from session analysis
└── test_sequence_*.md              # Future test sequences (created during sessions)
```

**NEW in Version 3:** Automatically generates test sequence logs from historical session data, identical to the format used for future logging (see `AGENTS.md`).

---

## 🚀 Quick Start

### Run the Analysis

```bash
# Navigate to directory
cd Research/Session_Analysis

# Run with default settings (fresh analysis)
python analyze_sessions.py

# Custom paths
python analyze_sessions.py \
  --sessions-dir "C:\Users\YOUR_NAME\.claude\projects\C--Users-dakot-Documents-Repositories-Fall-25-CS-5300" \
  --output-dir "./my_results"
```

### Incremental Analysis (Merge New Sessions)

**For teammates continuing research or adding new data:**

```bash
# Merge new sessions with existing analysis
python analyze_sessions.py --merge

# With custom paths
python analyze_sessions.py \
  --sessions-dir "C:\Users\YOUR_NAME\.claude\projects" \
  --output-dir "./results" \
  --merge
```

**How it works:**
- Loads existing `results/analysis_results_corrected.json`
- Identifies which sessions have already been analyzed
- Only processes new sessions (skips duplicates)
- Merges new data with existing sessions
- Recalculates all metrics with combined dataset
- Updates all output files with merged results

**Benefits:**
- **No duplicate work** - Only analyze new sessions
- **Cumulative data** - Build comprehensive dataset over time
- **Team collaboration** - Multiple teammates can contribute sessions
- **Continuous research** - Update findings as project evolves

### Requirements

- **Python 3.7+** (no external dependencies)
- **Claude Code session logs** in JSONL format
- **~5 minutes** to analyze 28 sessions (less for incremental updates)

---

## 📝 Test Sequence Logs (NEW)

### What Are Test Sequence Logs?

Test sequence logs capture the complete iteration history of test runs during development. Each log contains:
- **YAML frontmatter** - Structured data for quick statistics extraction
- **Markdown narrative** - Human-readable iteration-by-iteration breakdown
- **Failure patterns** - Detailed tracking of what failed and why

**Format matches the logging standard in `AGENTS.md`** - This ensures consistency between historical data (generated from past sessions) and future data (created during sessions).

### Automatic Generation

**The analysis script now automatically generates test sequence logs from historical sessions:**

```bash
# Run analysis (generates both metrics AND test sequence logs)
python analyze_sessions.py --merge
```

**Output:**
- Analysis results → `results/`
- Test sequence logs → `../logs/test_sequence_*_historical.md`

### File Naming Convention

```
test_sequence_YYYYMMDD_HHMMSS_<feature-name>_historical.md
```

Example: `test_sequence_20251113_143022_rbac_permissions_historical.md`

The `_historical` suffix indicates logs generated from past session data (vs. real-time logs created during future sessions).

### Log Contents

Each log contains:

**YAML Frontmatter:**
- `sequence_id` - Unique identifier for this test sequence
- `feature` - Feature name being tested
- `test_file` - Path to test file
- `session_id` - Reference to original Claude Code session
- `iterations[]` - Array of test runs with:
  - Timestamp, test counts, pass/fail/error metrics
  - New test failures vs. regression failures
  - Execution time (when available)
- `summary` - Overall statistics (iterations, failure rates, final status)
- `coverage` - Test coverage changes (when available)

**Markdown Narrative:**
- Iteration-by-iteration breakdown
- Failed test names
- Test output excerpts
- Sequence summary with learnings

### Using Test Sequence Logs for Research

**Quick Statistics:**
```bash
cd ../logs
python extract_stats.py
```

**Data Mining:**
- All logs have structured YAML → easy to parse
- Extract aggregate metrics across all sequences
- Compare historical vs. future test patterns
- Identify common failure types

**Benefits for Your Paper:**
1. **Reproducible data** - Teammates can generate identical logs from same sessions
2. **Granular detail** - Beyond just "tests passed/failed", see iteration-by-iteration progress
3. **Pattern analysis** - Mine common failure types across all test sequences
4. **Temporal analysis** - Track how test quality changes over time

---

## 📖 What Gets Measured

### Q1.2: Test Failure Analysis

**Metrics:**
1. **First-run failure rate** - % of newly written tests that fail on first execution
   - Definition: First test run *after* editing a test file
   - Result: **57.14%** (8 out of 14 first runs failed)

2. **Test iterations** - How many test runs before all pass
   - Result: **3.33 average** per session

3. **Regression detection** - % of sessions where existing tests caught breaking changes
   - Result: **55.56%** (5 out of 9 sessions)

**Session Types:** new, refactor, exploratory

### Q2: Reprompt Analysis

**Metrics:**
1. **Reprompt count** - User follow-up messages per session
   - Result: **~96 per session** (includes tool results)

2. **Reprompt reasons** - Why users had to reprompt
   - Errors: 16.82%
   - Refinements: 10.03%
   - Other: 71% (tool results, system messages)

3. **Success rate** - % of sessions that completed
   - Result: **100%** (all meaningful sessions succeeded)

---

## 📈 Understanding the Results

### Test Metrics Explained

| Metric | Value | What It Means |
|--------|-------|---------------|
| **57% first-run failures** | 8/14 failed | AI-generated tests often need debugging |
| **100% eventual success** | 15/15 succeeded | Iteration leads to working code |
| **3.33 avg iterations** | Per session | Efficient TDD workflow |
| **56% regression detection** | 5/9 sessions | Tests catch breaking changes |

### Common Test Failures

1. **HTTP status codes** - `302 != 200`, `302 != 403`
2. **Auth redirects** - Misunderstanding Django redirect behavior
3. **Assertion errors** - Permission/authorization logic
4. **Test setup** - Missing fixtures or test data

### Session Types

- **New features:** 32.1% (9 sessions)
- **Refactoring:** 21.4% (6 sessions)
- **Exploratory:** 46.4% (13 sessions)

---

## 🔧 For Your Teammates

### Running on Your Own Sessions

1. **Find your session logs:**
   ```
   Windows: C:\Users\YOUR_NAME\.claude\projects
   Mac/Linux: ~/.claude/projects
   ```

2. **Run the analysis:**
   ```bash
   python analyze_sessions.py \
     --sessions-dir "path/to/your/.claude/projects" \
     --project "YOUR_PROJECT_NAME"
   ```

3. **Check results:**
   - Analysis results saved to `results/` directory
   - Test sequence logs saved to `../logs/` directory
   - Open `analysis_report_corrected.txt` for summary
   - Review `../logs/test_sequence_*_historical.md` for detailed test iterations

### Continuing Research (Adding Your Sessions)

**Workflow for team collaboration:**

1. **Get the latest research package:**
   ```bash
   git pull origin main
   cd Research/Session_Analysis
   ```

2. **Run incremental analysis with your sessions:**
   ```bash
   python analyze_sessions.py \
     --sessions-dir "C:\Users\YOUR_NAME\.claude\projects" \
     --merge
   ```

3. **Review updated findings:**
   - All metrics automatically recalculated
   - Your sessions merged with existing data
   - session_analysis_results.md ready for manual updates if needed

4. **Commit and share:**
   ```bash
   git add results/
   git commit -m "Add session analysis from [YOUR_NAME]"
   git push
   ```

**IMPORTANT:** The `--merge` flag ensures your sessions are added to existing data, not replacing it. This preserves the cumulative research dataset.

### Customizing the Analysis

Edit `analyze_sessions.py` to:
- Change session categorization logic
- Add new metrics
- Filter specific session types
- Adjust "first run" definition

See the script's inline comments for guidance.

---

## 📝 For Your Research Paper

### Recommended Figures/Tables

**Table 1: Test Failure Metrics**
```
Metric                          | Value
--------------------------------|-------
First-run failure rate          | 57.14%
First-run failure rate (by session) | 83.33%
Average test iterations         | 3.33
Regression detection rate       | 55.56%
Eventual success rate           | 100%
```

**Table 2: Session Breakdown**
```
Type         | Count | Percentage
-------------|-------|------------
Exploratory  | 13    | 46.4%
New features | 9     | 32.1%
Refactoring  | 6     | 21.4%
```

**Figure 1: Test Iteration Distribution**
- X-axis: Number of iterations (1, 2, 3, 4+)
- Y-axis: Number of sessions
- Data: See `results/session_summary_corrected.csv`

### Key Claims You Can Make

✅ **Supported by data:**
- "Claude-generated tests fail 57% of the time on first execution"
- "All sessions achieved 100% success through iterative debugging (n=15)"
- "Average 3.33 test iterations indicates efficient TDD workflow"
- "Tests detected regressions in 56% of development sessions"

❌ **NOT supported:**
- ~~"Claude writes perfect tests"~~ (57% fail on first run)
- ~~"No debugging required"~~ (3.33 avg iterations needed)
- ~~"Code works immediately"~~ (only 43% pass first time)

---

## ⚠️ Important Notes

### About the 57% Failure Rate

**This is a GOOD finding for research** because:
1. Shows **realistic AI capabilities** - not artificially perfect
2. Demonstrates **effective human-AI collaboration** - iteration works
3. Provides **learnable patterns** - auth/HTTP errors are consistent
4. Validates **TDD methodology** - tests catch issues early

### Limitations

1. **Limited test coverage** - Only 32% of sessions ran tests locally
2. **No CI/CD integration** - GitHub Actions data not included
3. **Time data missing** - Cannot measure actual time-to-completion
4. **No human baseline** - Cannot compare to human-only development
5. **Reprompts include system messages** - Actual user prompts are subset

---

## 💡 Tips & Troubleshooting

### Common Issues

**"No sessions found"**
- Check `--sessions-dir` points to correct location
- Verify project name matches JSONL filenames

**"No meaningful sessions"**
- Sessions need ≥2 code edits or ≥10 messages
- Adjust thresholds in script if needed

**"No test runs detected"**
- Only Django tests (`manage.py test`) are captured
- Tests must be run during Claude Code session (not in separate terminal)
- Check if team uses CI/CD instead of local testing

### Best Practices

1. **Run analysis incrementally** - New sessions only
2. **Document assumptions** - Note any customizations
3. **Validate findings** - Spot-check a few sessions manually
4. **Track session IDs** - Reference specific examples in paper
5. **Share with teammates** - Get feedback on categorization

---

## 📚 Additional Resources

### Files in This Package

- **`session_analysis_results.md`** - Complete findings with examples, ready for paper
- **`research_metrics.json`** - All metrics in structured JSON format
- **`results/analysis_results_corrected.json`** - Raw session data
- **`results/session_summary_corrected.csv`** - Spreadsheet for charts

### For More Context

- See `session_analysis_results.md` for detailed analysis
- Check `archive/` for historical analysis versions
- Review `analyze_sessions.py` code for methodology

---

## 🎓 Research Context

**Study:** Measuring Claude Sonnet 4.5's effectiveness in modifying existing codebases

**Project:** Fall-25-CS-5300 Django application

**Thesis Questions:**
1. How accurately does Claude modify code without errors? → **57% first-run failures, 100% eventual success**
2. What % passes tests without modification? → **42.86% (100% - 57.14%)**
3. Code quality ratings? → **Requires separate code review (not in session logs)**

---

## 📞 Support

**Questions about:**
- **This analysis:** Check `session_analysis_results.md` or contact research team
- **Claude Code:** https://github.com/anthropics/claude-code/issues
- **The script:** Read inline comments in `analyze_sessions.py`

---

**Analysis Tool Version:** 3.0 (with test sequence log generation)
**Last Updated:** November 13, 2025
**For:** CS 4300/5300 Fall 2025 SWE Research Study

**Version 3.0 Changes:**
- Automatically generates test sequence logs from historical session data
- Logs saved to `Research/logs/` with `_historical` suffix
- Format matches AGENTS.md logging standard for future sessions
- Enables comprehensive test iteration analysis for research
