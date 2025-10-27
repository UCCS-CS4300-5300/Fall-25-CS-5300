# Quick Test & Coverage Guide

## Run Tests with Coverage (Windows)

```batch
.\run_tests_with_coverage.bat
```

This will:
1. Run all Django tests
2. Generate coverage report
3. Create HTML report in `active_interview_backend/htmlcov/`

## Manual Commands

### Run specific test file:
```bash
cd active_interview_backend
python manage.py test active_interview_app.tests.test_views_comprehensive -v 2
```

### Run all tests:
```bash
cd active_interview_backend
python manage.py test -v 2
```

### Run with coverage:
```bash
cd active_interview_backend
coverage run manage.py test -v 2
coverage report -m
coverage html
```

## Check Coverage Results

### Option 1: Console Output
After running tests, look for lines like:
```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
active_interview_app/views.py           450     50    89%
active_interview_app/merge_stats_models.py  100   5    95%
-----------------------------------------------------------
TOTAL                                   2000    150    92%
```

### Option 2: HTML Report (Recommended)
```bash
cd active_interview_backend
start htmlcov/index.html  # Windows
# or
open htmlcov/index.html   # Mac/Linux
```

Green lines = covered ✅
Red lines = not covered ❌

## What to Look For

### Success Criteria:
- ✅ All tests pass (no failures)
- ✅ `views.py` coverage ≥ 80%
- ✅ `merge_stats_models.py` coverage ≥ 80%
- ✅ TOTAL coverage ≥ 80%

### If Coverage is Still Low:

1. **Open HTML report** to see which specific lines aren't covered
2. **Check for**:
   - Exception handling blocks (try/except)
   - Error conditions (if errors)
   - Edge cases (empty data, None values)
   - Alternative code paths

3. **Add tests** for uncovered lines in appropriate test file:
   - Views → `test_views_comprehensive.py`
   - Models → `test_models.py` or `test_token_tracking.py`
   - Forms → `test_forms.py`

## Test File Mapping

| Code File | Test File |
|-----------|-----------|
| `views.py` | `test_views_comprehensive.py`, `test_views_extended.py`, `test_additional_views.py` |
| `models.py` | `test_models.py` |
| `merge_stats_models.py` | `test_token_tracking.py` |
| `token_usage_models.py` | `test_token_tracking.py` |
| `forms.py` | `test_forms.py` |
| `serializers.py` | `test_serializers.py` |

## Common Issues & Solutions

### Issue: Tests fail with import errors
**Solution:** Make sure you're in the correct directory and have installed all dependencies:
```bash
cd active_interview_backend
pip install -r requirements.txt
```

### Issue: Coverage shows 0% for some files
**Solution:** Check `.coveragerc` to ensure files aren't being excluded

### Issue: Shell/bash errors on Windows
**Solution:** Use the batch script or run Python commands directly:
```batch
cd active_interview_backend
python -m coverage run manage.py test
python -m coverage report -m
```

### Issue: Some tests fail due to missing URLs
**Solution:** Check that URL names in tests match `urls.py`:
- Use `reverse('url-name')` from `active_interview_app/urls.py`
- Common URLs: `'index'`, `'chat-list'`, `'chat-create'`, `'register_page'`, etc.

## CI/CD Integration

When you push to GitHub, the CI pipeline will:
1. Run lint checks
2. Run security scans
3. **Run tests with coverage** ← Your tests run here
4. Check coverage ≥ 80% ← Must pass
5. **Run AI code review** ← Only if coverage passes ✅
6. Generate LOC metrics
7. Archive reports

**Coverage failure = AI review is skipped**

## Quick Coverage Check

After making changes, quickly verify coverage:

```bash
cd active_interview_backend
coverage run manage.py test
coverage report | grep -E "(views.py|merge_stats_models.py|TOTAL)"
```

Should show something like:
```
active_interview_app/views.py           450     50    89%
active_interview_app/merge_stats_models.py  100   5    95%
TOTAL                                   2000    150    92%
```

All ≥ 80% = ✅ Ready to push!

## Files Created for You

| File | Purpose |
|------|---------|
| `run_tests_with_coverage.bat` | Windows batch script to run tests easily |
| `TESTING_IMPROVEMENTS.md` | Full documentation of all test improvements |
| `COVERAGE_SUMMARY.md` | Summary of coverage improvements |
| `QUICK_TEST_GUIDE.md` | This file - quick reference |

---

**Need Help?**
Check the HTML coverage report (`htmlcov/index.html`) to see exactly which lines need tests!
