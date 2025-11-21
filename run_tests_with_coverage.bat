@echo off
REM Windows batch script to run tests with coverage

echo ========================================
echo Running Django Tests with Coverage
echo ========================================
echo.

cd active_interview_backend

echo Running tests with coverage...
python -m coverage run manage.py test -v 2

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo Tests FAILED!
    echo ========================================
    exit /b 1
)

echo.
echo ========================================
echo Generating Coverage Report
echo ========================================
echo.

REM Generate text report
python -m coverage report -m > coverage_report.txt

REM Also display to console
python -m coverage report -m

echo.
echo Coverage report saved to: coverage_report.txt
echo.

REM Generate HTML report
python -m coverage html

echo HTML coverage report generated in: htmlcov/index.html
echo.
echo ========================================
echo Tests completed successfully!
echo ========================================
