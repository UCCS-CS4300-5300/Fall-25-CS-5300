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
Determine the path to the session longs first and use that path instead of the 
example path below.
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
- **NEW:** Generates test sequence logs in `Research/logs/` directory

**Test sequence logs (NEW in V3):**
- Automatically generated from historical session data
- Saved to `Research/logs/test_sequence_*_historical.md`
- Format matches AGENTS.md standard for consistency
- Contains YAML frontmatter + markdown narrative
- Enables detailed test iteration analysis

## Output Files

**Analysis results** (in `Research/Session_Analysis/results/`):
- `analysis_results_corrected.json` - Raw session data (for merging)
- `analysis_report_corrected.txt` - Text report with all metrics
- `session_summary_corrected.csv` - CSV for spreadsheet/charts

**Test sequence logs** (in `Research/logs/`):
- `test_sequence_*_historical.md` - Historical test sequences extracted from sessions

**Documentation:**
- `Research/Session_Analysis/README.md` - Full usage guide
- `Research/logs/README.md` - Test logging documentation

The `--merge` flag ensures incremental updates without reprocessing existing sessions.
