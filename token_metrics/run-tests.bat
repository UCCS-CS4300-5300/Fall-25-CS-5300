@echo off
REM Run token metrics tests with coverage

echo.
echo ============================================================
echo   TOKEN METRICS TEST SUITE
echo ============================================================
echo.

cd /d "%~dp0"

echo Running tests with coverage...
echo.

REM Run pytest with coverage for token_metrics
python -m pytest backend/tests/ ^
    --cov=scripts ^
    --cov=backend ^
    --cov-report=term-missing ^
    --cov-report=html:backend/tests/htmlcov ^
    --cov-report=json:backend/tests/coverage.json ^
    --tb=short ^
    -v

if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo   TESTS FAILED
    echo ============================================================
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   TESTS PASSED
echo ============================================================
echo.
echo Coverage report generated:
echo   - HTML: backend/tests/htmlcov/index.html
echo   - JSON: backend/tests/coverage.json
echo.

REM Check coverage percentage
python -c "import json; data=json.load(open('backend/tests/coverage.json')); total=data['totals']['percent_covered']; print(f'\nTotal Coverage: {total:.2f}%%'); exit(0 if total >= 80 else 1)"

if %errorlevel% neq 0 (
    echo.
    echo WARNING: Coverage is below 80%%
    echo.
) else (
    echo.
    echo SUCCESS: Coverage is >= 80%%
    echo.
)

pause
