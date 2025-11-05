@echo off
REM Run Django tests with coverage
REM This script runs all tests and generates a coverage report

echo ============================================================
echo Running Django Tests with Coverage
echo ============================================================
echo.

cd active_interview_backend

echo Installing coverage if needed...
pip install coverage -q

echo.
echo Running tests with coverage...
echo.

coverage run --source=active_interview_app manage.py test

echo.
echo ============================================================
echo Generating Coverage Report
echo ============================================================
echo.

coverage report

echo.
echo ============================================================
echo Generating HTML Coverage Report
echo ============================================================
echo.

coverage html

echo.
echo Coverage report generated!
echo Open 'htmlcov/index.html' to view detailed coverage
echo.

pause
