Analyze Claude Code session logs for SWE research study.

## Research Context

**Thesis:** Measure Claude Sonnet 4.5's effectiveness in understanding and improving an existing codebase.

**Research Questions:**

**Q1:** How accurately does Claude modify code without introducing errors?
- Q1.2: Test failure rates and regression counts (analyzable from session logs)

**Q2:** What percentage of Claude's code passes tests without human modification?
- Q2.1: Developer time debugging Claude's output
- Q2.2: Number of prompt iterations per successful task

**Q3:** Code quality ratings (requires separate code review - not in session logs)

## Task

Run the session analysis tool and generate an updated research report:

1. Use the existing analysis script: `Research/Session_Analysis/analyze_sessions.py`
2. Use `--merge` flag to analyze only new sessions (skips already-analyzed sessions)
3. Review updated findings in `Research/Session_Analysis/session_analysis_results.md`
4. Generate report showing:
   - **Q1.2 Metrics:** Test failure rates, iterations, regression detection
   - **Q2 Metrics:** Reprompt patterns, success rates, error resolution
   - Session categorization: new/refactor/test_only
   - Concrete examples with session IDs

## Analysis Script Usage

```bash
cd Research/Session_Analysis

# Incremental analysis (recommended - merges with existing data)
python analyze_sessions.py --merge

# Or with custom paths
python analyze_sessions.py \
  --sessions-dir "C:\Users\dakot\.claude\projects" \
  --project "Fall-25-CS-5300" \
  --merge
```

## Output Requirements

The script automatically:
- Identifies and processes only new sessions
- Merges new data with existing results
- Recalculates all metrics with combined dataset
- Updates all output files in `results/` directory

Review and manually update if needed:
- `session_analysis_results.md` - Main research findings
- `research_metrics.json` - Key metrics in JSON format

## Existing Results

All analysis results are in `Research/Session_Analysis/`:
- `session_analysis_results.md` - Complete research findings (ready for paper)
- `research_metrics.json` - Structured metrics
- `results/analysis_results_corrected.json` - Raw session data
- `results/analysis_report_corrected.txt` - Text report
- `results/session_summary_corrected.csv` - CSV for charts
- `README.md` - Full usage guide

The `--merge` flag ensures incremental updates without reprocessing existing sessions.