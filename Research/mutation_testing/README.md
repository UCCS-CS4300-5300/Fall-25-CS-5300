# Mutation Testing Results

This directory contains mutation testing reports that evaluate the effectiveness of the test suite.

## What's Here

- `mutation_results_*.json` - Machine-readable test results
- `mutation_report_*.md` - Human-readable detailed reports

## Quick Commands

```bash
# Run mutation tests on a module
python run_mutation_tests.py --module models --limit 20

# View all results
python -m mutmut results

# View specific mutation
python -m mutmut show 1

# Generate HTML report
python run_mutation_tests.py --module forms --html
```

## Understanding the Reports

### JSON Files (`mutation_results_*.json`)
Contains:
- Timestamp
- Module tested
- Summary statistics (killed, survived, timeout, suspicious)
- Test effectiveness score

### Markdown Files (`mutation_report_*.md`)
Contains:
- Detailed summary table
- Score interpretation and grade
- Explanations of each result type
- Next steps for improvement
- Commands reference

## Interpreting Results

| Mutation Score | Grade | Meaning |
|---------------|-------|---------|
| 80-100% | A | Excellent - Tests are highly effective |
| 60-79% | B | Good - Tests are reasonably effective |
| 40-59% | C | Fair - Tests have significant gaps |
| 0-39% | F | Poor - Tests are not effective |

## Workflow

1. **Run Tests**: `python run_mutation_tests.py --module <module> --limit 20`
2. **Check Score**: Look at mutation_report_*.md
3. **Review Survived**: `python -m mutmut show <id>`
4. **Add Tests**: Write tests to catch survived mutations
5. **Re-test**: Run mutation tests again
6. **Repeat**: Until score > 80%

## Tips

- Start with small modules and limited mutations
- Focus on killed vs survived ratio
- Survived mutations indicate weak tests
- Add boundary value tests to kill more mutations
- Use specific assertions (not just "result > 0")

For detailed guide, see: `MUTATION_TESTING_GUIDE.md` in project root
