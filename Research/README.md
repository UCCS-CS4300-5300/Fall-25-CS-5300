# Research Data and Analysis

This directory contains research data and analysis tools for the **Claude Code effectiveness study**.

## Study Overview

**Research Question:** How effective is Claude Sonnet 4.5 at modifying and extending an existing Django codebase?

**Specific Metrics:**
1. Test failure rates on first execution
2. Debugging iteration counts
3. Regression detection rates
4. Code quality and success rates

## Directory Structure

```
Research/
├── README.md                           # This file
├── Session_Analysis/                   # Automated session log analysis
│   ├── session_analysis_results.md    # Key research findings (ready for paper)
│   ├── analyze_sessions.py            # Analysis script with incremental support
│   ├── research_metrics.json          # Structured metrics
│   ├── README.md                      # Usage guide for teammates
│   ├── results/                       # Analysis outputs (JSON, CSV, reports)
│   └── archive/                       # Historical analysis versions
│
└── logs/                              # Test run logs for detailed analysis
    ├── README.md                      # Logging guide
    ├── EXAMPLE_test_run_*.md          # Example log format
    └── test_run_*.md                  # Individual test run logs
```

## Data Sources

### 1. Claude Code Session Logs (Automated)
**Location:** `~/.claude/projects/`
**Format:** JSONL (one message per line)
**Analysis:** Automated via `Session_Analysis/analyze_sessions.py`

**What's captured:**
- User prompts and Claude responses
- Tool usage (file edits, test runs, bash commands)
- Test output embedded in tool results
- Conversation flow and iterations

**Current findings:**
- 57.14% first-run test failure rate
- 100% eventual success rate
- 3.33 average test iterations per session
- See [Session Analysis Results](Session_Analysis/session_analysis_results.md) for details

### 2. Test Run Logs (Manual - Sequence Format)
**Location:** `Research/logs/`
**Format:** YAML frontmatter + Markdown (sequence-based)
**Logging:** Claude Code creates logs per [AGENTS.md guidelines](../AGENTS.md#4-test-run-logging-for-research)

**What's captured:**
- **YAML metadata:** Structured stats for all iterations (quick parsing)
- **Markdown narrative:** Detailed failure info, root causes, resolutions
- **New test failures:** Tracked separately per iteration
- **Regression failures:** Pre-existing tests that broke
- **Coverage impact:** Initial → Final coverage change

**Structure:** One file per test sequence (all iterations together)

**Example file:** `test_sequence_20251112_194500_rbac_permissions.md`
```yaml
---
iterations:
  - number: 1
    failed: 9
    new_test_failures: 9
    regression_failures: 0
  - number: 2
    failed: 3
    new_test_failures: 3
    regression_failures: 0
  - number: 3
    failed: 0
summary:
  total_iterations: 3
  first_run_failure_rate: 36.0
---
```

**Purpose:** Enables quick statistical analysis + detailed debugging context:
- Parse YAML only for stats (first ~30 lines)
- Read full narrative for deep dives
- All iterations in one place (no linking needed)
- Extract with simple Python script (`logs/extract_stats.py`)

## Using the Research Data

### For Team Members Adding Data

**Session logs** are automatically captured by Claude Code. To add your data:
```bash
cd Research/Session_Analysis
python analyze_sessions.py --merge
```
See [Session Analysis README](Session_Analysis/README.md) for details.

**Test run logs** are created by Claude Code automatically per AGENTS.md guidelines.
- No manual action needed - Claude logs after each test run
- Logs saved to `Research/logs/test_run_YYYYMMDD_HHMMSS.md`
- See [Test Logging README](logs/README.md) for format

### For Researchers Analyzing Data

**Automated analysis:**
1. Run `Session_Analysis/analyze_sessions.py` to process all sessions
2. View results in `Session_Analysis/session_analysis_results.md`
3. Export data from `Session_Analysis/results/*.json` for statistical analysis

**Manual analysis:**
1. Review test logs in `logs/` for detailed failure patterns
2. Cross-reference session IDs with test logs for correlation
3. Identify common error types and resolution strategies

**Key metrics available:**
- First-run failure rate (by run and by session)
- Test iteration counts
- Regression detection rate
- Success rates
- Coverage evolution
- Error type distribution (from logs)

## Current Research Findings

### Session Analysis (28 sessions, 9 with local tests)

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **First-run failure rate** | 57.14% | Tests fail over half the time on first execution |
| **Success rate** | 100% | All sessions eventually succeeded through iteration |
| **Avg iterations** | 3.33 | Efficient TDD workflow with Claude |
| **Regression detection** | 55.56% | Tests effectively catch breaking changes |

**Common failure patterns:**
- HTTP status mismatches (302 vs 200/403)
- Authentication/authorization logic errors
- Django redirect behavior misunderstandings
- Test setup/teardown issues

**Full analysis:** [Session Analysis Results](Session_Analysis/session_analysis_results.md)

## For Your Research Paper

**Data sources to cite:**
1. `Session_Analysis/session_analysis_results.md` - Main findings
2. `Session_Analysis/research_metrics.json` - Structured metrics
3. `Session_Analysis/results/*.csv` - Data for charts
4. `logs/*.md` - Qualitative examples and detailed failure analysis

**Recommended figures:**
- Table 1: Test failure metrics (from session analysis)
- Figure 1: Test iteration distribution (from CSV data)
- Table 2: Common error patterns (from test logs)
- Figure 2: Coverage evolution over time (from test logs)

**Claims supported by data:**
- ✅ "Claude-generated tests fail 57% of the time on first execution"
- ✅ "All sessions achieved 100% success through iterative debugging"
- ✅ "Average 3.33 iterations indicates efficient TDD workflow"
- ✅ "Tests detected regressions in 56% of development sessions"

## Research Methodology

### Data Collection
- **Session logs:** Automatically captured by Claude Code during development
- **Test logs:** Manually created by Claude Code per AGENTS.md guidelines
- **Time period:** October-November 2025
- **Project:** Fall-25-CS-5300 Django application

### Analysis Approach
1. **Automated parsing** of session logs (JSONL format)
2. **Correlation** of test file edits with subsequent test runs
3. **Classification** of test failures (new test vs regression)
4. **Manual validation** of findings against test logs
5. **Pattern identification** for common error types

### Limitations
- Only 32% of sessions included local test runs (rest use CI/CD)
- No timestamp data in session logs for time-to-completion
- Reprompt counts include system messages
- No human baseline for comparison
- GitHub Actions test data not integrated

### Future Work
- Integrate CI/CD logs for complete test coverage
- Add timestamp tracking for time-to-completion metrics
- Compare to human developer baseline
- Build taxonomy of error types from test logs
- Track learning curves over time

## Questions?

**About session analysis:**
- See [Session_Analysis/README.md](Session_Analysis/README.md)
- Review analysis script: `Session_Analysis/analyze_sessions.py`

**About test logging:**
- See [logs/README.md](logs/README.md)
- Check example: `logs/EXAMPLE_test_run_*.md`
- Guidelines in [AGENTS.md](../AGENTS.md#4-test-run-logging-for-research)

**About research methodology:**
- See [Session_Analysis/session_analysis_results.md](Session_Analysis/session_analysis_results.md)
- Contact research team with questions

---

**Study:** CS 4300/5300 Fall 2025 Software Engineering Research
**Last Updated:** November 12, 2025
