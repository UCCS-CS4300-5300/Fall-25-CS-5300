@echo off
REM Quick Mutation Test Script
REM This script runs a fast mutation test on a small module to verify setup

echo ====================================================================
echo QUICK MUTATION TEST - SETUP VERIFICATION
echo ====================================================================
echo.
echo This will run a small mutation test to verify everything is working.
echo It tests the pdf_export module with 5 mutations.
echo.
echo Estimated time: 5-10 minutes
echo.
pause

echo.
echo Running mutation test...
echo.

python run_mutation_tests.py --module pdf_export --limit 5 --html

echo.
echo ====================================================================
echo QUICK TEST COMPLETE
echo ====================================================================
echo.
echo Check the results in: Research/mutation_testing/
echo.
pause
