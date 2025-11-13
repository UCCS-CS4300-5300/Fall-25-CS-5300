# Archive - Original (Incorrect) Analysis

**⚠️ Files in this directory contain INCORRECT data due to parsing bugs**

These files are kept for reference and comparison purposes only.

---

## What Was Wrong

The original analysis reported a **0% first-run failure rate**, which was incorrect due to:

1. **JSON parsing bug** - Checked wrong nesting level for tool results
2. **Wrong definition** - "First run" meant "first run in session" not "first run after writing tests"
3. **Missing data** - Didn't check both storage locations for test output

## Corrected Findings

See parent directory for corrected analysis:
- **Actual first-run failure rate: 57.14%**
- **Corrected in:** `../session_analysis_results.md`
- **Fixed script:** `../analyze_sessions.py`

---

## Files in Archive

### Original Analysis (Nov 11, 2025 - INCORRECT)
- `dakota-sessions-analysis-Nov11.md` - Original incorrect summary
- `research_metrics.json` - Old metrics with 0% failure rate
- `django_test_analysis.json` - First incorrect test analysis
- `session_analysis_report.json` - Old session data

### Broken Scripts
- `analyze_sessions.py` - Original script with parsing bugs

### Supporting Files
- `research_examples.md` - Example sessions (data was valid, interpretation was wrong)

---

## Key Differences

| Metric | Original (Wrong) | Corrected | Why Different |
|--------|-----------------|-----------|---------------|
| First-run failure rate | 0% | 57.14% | Parsing bug missed test outputs |
| Sessions with tests | 13 | 9 | Better filtering |
| Test iterations | 11.38 | 3.33 | Wrong definition of iteration |
| Regression rate | 38.46% | 55.56% | Better detection with correct data |

---

## For Researchers

**DO NOT cite these files in your paper.**

Use the corrected analysis in the parent directory instead.

This archive exists to:
1. Show the correction process (transparency)
2. Allow comparison between methodologies
3. Demonstrate importance of validating parsing logic

---

**User Question That Led to Discovery:**
> "The summary said no first test runs resulted in any failures, but i'm pretty sure i remember that when we worked on the role based access, there were initally tests in test_rbac.py that failed on the first time we ran them."

**Result:** User was correct! The 0% was wrong. After investigation, found parsing bugs and methodology issues. Corrected analysis shows 57.14% failure rate, which is realistic and valuable for research.

---

**Archived:** November 12, 2025
**Reason:** Incorrect due to parsing bugs
**See:** `../session_analysis_results.md` for corrected analysis
