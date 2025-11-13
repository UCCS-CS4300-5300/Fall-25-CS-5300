# Test Run Logs

This directory contains logs of Django test runs for research purposes.

## Purpose

These logs support the research study on **Claude Code's effectiveness in test-driven development**. They capture:

1. **First-run test failures** - New tests that fail on initial execution
2. **Regression detection** - Existing tests that fail after code changes
3. **Debugging iterations** - Multiple test runs showing the debugging process
4. **Test coverage evolution** - How coverage changes over time

## Usage

**For Claude Code:** Follow the logging guidelines in [AGENTS.md](../../AGENTS.md#4-test-run-logging-for-research)

**For Researchers:** These logs provide:
- **Quick statistics extraction** - Parse YAML frontmatter only (~30 lines)
- **Complete debugging narrative** - Full context when needed
- **Structured iteration data** - All runs in one file
- **Root cause analysis** - Why tests failed and how they were fixed

## Log Format

**Filename:** `test_sequence_YYYYMMDD_HHMMSS_<feature-name>.md`

**Structure:** YAML frontmatter (statistics) + Markdown narrative (context)

### Key Benefits

✅ **Fast statistics extraction** - Parse only YAML (first ~30 lines)
✅ **No file linking needed** - All iterations in one place
✅ **Compact but complete** - Stats + narrative in single file
✅ **Easy analysis** - Straightforward YAML parsing

### Quick Statistics Extraction

```python
import yaml

# Parse just the metadata (fast!)
with open('test_sequence_*.md') as f:
    content = f.read()
    metadata = yaml.safe_load(content.split('---')[1])

# Get key metrics
iterations = metadata['summary']['total_iterations']
first_run_failures = metadata['iterations'][0]['failed']
regressions = metadata['iterations'][0]['regression_failures']

print(f"Feature required {iterations} iterations")
print(f"First run: {first_run_failures} failures")
print(f"Regressions: {regressions}")
```

Or use the provided script:
```bash
python extract_stats.py
```

## Complete Example

See [test_sequence_20251112_194500_rbac_permissions.md](test_sequence_20251112_194500_rbac_permissions.md) for a full example showing:

- YAML frontmatter with 3 iterations
- Iteration progression: 9 failures → 3 failures → all passing
- Detailed narrative for each iteration
- Root cause analysis
- Final statistics and patterns

**Quick preview of the example:**
- Feature: RBAC Permissions (25 tests)
- Total iterations: 3
- First-run failure rate: 36% (9/25 tests)
- Regression failures: 0
- Coverage improvement: +3%
- Result: ✅ Success

The YAML section provides instant statistics, while the markdown narrative explains the debugging journey in detail.

## Analysis Integration

These logs can be analyzed alongside Claude Code session logs to:
- Calculate accurate first-run failure rates
- Identify common test failure patterns
- Measure iteration counts for debugging
- Track test coverage improvements

**Related:** See [Session Analysis Tools](../Session_Analysis/) for automated analysis of session logs.

## Directory Structure

```
Research/logs/
├── README.md                                              # This file
├── test_sequence_20251112_194500_rbac_permissions.md     # RBAC feature (3 iterations) ✅
├── test_sequence_*.md                                     # Additional test sequences
└── extract_stats.py                                       # Statistics extraction script
```

## Key Features

- **One file per feature** - All iterations in single log
- **YAML frontmatter** - Structured data for quick parsing
- **Markdown narrative** - Full context for human reading
- **Regression tracking** - Clearly separates new test failures from regressions
- **Committed to repo** - Research transparency
- **Easy analysis** - Use `extract_stats.py` to get aggregate metrics

---

**For detailed research findings:** See [Session Analysis Results](../Session_Analysis/session_analysis_results.md)
