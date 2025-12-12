@echo off
REM ============================================================================
REM Unified Mutation Testing Script
REM ============================================================================
REM This script provides a menu-driven interface for mutation testing.
REM ============================================================================

SETLOCAL EnableDelayedExpansion

REM Set colors
SET "GREEN=[92m"
SET "YELLOW=[93m"
SET "RED=[91m"
SET "CYAN=[96m"
SET "NC=[0m"

:MAIN_MENU
cls
echo.
echo ============================================================================
echo MUTATION TESTING - UNIFIED RUNNER
echo ============================================================================
echo.
echo Select your testing approach:
echo.
echo   %CYAN%1.%NC% Quick Test (Single module with limit) %GREEN%[RECOMMENDED]%NC%
echo      Perfect for rapid feedback - 20-40 minutes
echo.
echo   %CYAN%2.%NC% Full Module Test (Complete module analysis)
echo      Comprehensive testing - 30-90 minutes per module
echo.
echo   %CYAN%3.%NC% Full Application Test %YELLOW%[WARNING: 8-24+ hours]%NC%
echo      Test ALL Python files - Very time intensive
echo.
echo   %CYAN%4.%NC% Custom Configuration (Advanced)
echo      Specify your own parameters
echo.
echo   %CYAN%5.%NC% View Previous Results
echo      Browse existing mutation test reports
echo.
echo   %CYAN%6.%NC% Help / Documentation
echo      Learn about mutation testing
echo.
echo   %CYAN%0.%NC% Exit
echo.
echo ============================================================================
echo.

SET /P MAIN_CHOICE="Enter your choice (0-6): "

if "%MAIN_CHOICE%"=="1" goto QUICK_TEST
if "%MAIN_CHOICE%"=="2" goto FULL_MODULE_TEST
if "%MAIN_CHOICE%"=="3" goto FULL_APP_TEST
if "%MAIN_CHOICE%"=="4" goto CUSTOM_CONFIG
if "%MAIN_CHOICE%"=="5" goto VIEW_RESULTS
if "%MAIN_CHOICE%"=="6" goto SHOW_HELP
if "%MAIN_CHOICE%"=="0" goto EXIT
echo %RED%Invalid choice!%NC%
pause
goto MAIN_MENU

REM ============================================================================
REM QUICK TEST - Single module with mutation limit
REM ============================================================================
:QUICK_TEST
cls
echo.
echo ============================================================================
echo QUICK MUTATION TEST
echo ============================================================================
echo.
echo This runs a limited mutation test on one module (20-40 minutes)
echo Perfect for getting quick feedback on test effectiveness.
echo.
echo Available modules:
echo   1. pdf_export      (Simplest - ~10-20 mutations) %GREEN%[BEST FOR FIRST TIME]%NC%
echo   2. permissions     (Small - ~10-20 mutations)
echo   3. serializers     (Small - ~15-25 mutations)
echo   4. invitation_utils(Small - ~20-30 mutations)
echo   5. forms           (Medium - ~30-50 mutations)
echo   6. user_data_utils (Medium - ~30-50 mutations)
echo   7. models          (Large - ~50-100 mutations)
echo   8. views           (Very Large - ~100+ mutations)
echo   9. Custom module name
echo.

SET /P MODULE_CHOICE="Select module (1-9): "

SET MODULE=
if "%MODULE_CHOICE%"=="1" SET MODULE=pdf_export
if "%MODULE_CHOICE%"=="2" SET MODULE=permissions
if "%MODULE_CHOICE%"=="3" SET MODULE=serializers
if "%MODULE_CHOICE%"=="4" SET MODULE=invitation_utils
if "%MODULE_CHOICE%"=="5" SET MODULE=forms
if "%MODULE_CHOICE%"=="6" SET MODULE=user_data_utils
if "%MODULE_CHOICE%"=="7" SET MODULE=models
if "%MODULE_CHOICE%"=="8" SET MODULE=views
if "%MODULE_CHOICE%"=="9" (
    SET /P MODULE="Enter module name (without .py): "
)

if "%MODULE%"=="" (
    echo %RED%Invalid choice!%NC%
    pause
    goto QUICK_TEST
)

echo.
echo Selected module: %CYAN%%MODULE%%NC%
echo.
SET /P LIMIT="Enter mutation limit (recommended: 10-50): "

SET /P HTML_CHOICE="Generate HTML report? (Y/N): "
SET HTML=
if /I "%HTML_CHOICE%"=="Y" SET HTML=--html

goto RUN_TEST

REM ============================================================================
REM FULL MODULE TEST - Complete module without limit
REM ============================================================================
:FULL_MODULE_TEST
cls
echo.
echo ============================================================================
echo FULL MODULE MUTATION TEST
echo ============================================================================
echo.
echo This tests ALL mutations in a single module (30-90 minutes)
echo.
echo Available modules:
echo   1. pdf_export      (Simple, ~20-40 min)
echo   2. permissions     (Simple, ~20-40 min)
echo   3. serializers     (Simple, ~30-50 min)
echo   4. invitation_utils(Medium, ~30-60 min)
echo   5. forms           (Medium, ~40-80 min)
echo   6. user_data_utils (Medium, ~40-80 min)
echo   7. models          (Large, ~1-3 hours)
echo   8. views           (Very Large, ~3-6 hours)
echo   9. Custom module name
echo.

SET /P MODULE_CHOICE="Select module (1-9): "

SET MODULE=
if "%MODULE_CHOICE%"=="1" SET MODULE=pdf_export
if "%MODULE_CHOICE%"=="2" SET MODULE=permissions
if "%MODULE_CHOICE%"=="3" SET MODULE=serializers
if "%MODULE_CHOICE%"=="4" SET MODULE=invitation_utils
if "%MODULE_CHOICE%"=="5" SET MODULE=forms
if "%MODULE_CHOICE%"=="6" SET MODULE=user_data_utils
if "%MODULE_CHOICE%"=="7" SET MODULE=models
if "%MODULE_CHOICE%"=="8" SET MODULE=views
if "%MODULE_CHOICE%"=="9" (
    SET /P MODULE="Enter module name (without .py): "
)

if "%MODULE%"=="" (
    echo %RED%Invalid choice!%NC%
    pause
    goto FULL_MODULE_TEST
)

SET LIMIT=

SET /P HTML_CHOICE="Generate HTML report? (Y/N): "
SET HTML=
if /I "%HTML_CHOICE%"=="Y" SET HTML=--html

goto RUN_TEST

REM ============================================================================
REM FULL APPLICATION TEST - Test everything
REM ============================================================================
:FULL_APP_TEST
cls
echo.
echo ============================================================================
echo FULL APPLICATION MUTATION TEST
echo ============================================================================
echo.
echo %YELLOW%WARNING: This will take 8-24+ HOURS to complete!%NC%
echo.
echo This tests ALL Python files in active_interview_app/
echo Each mutation requires running the entire test suite.
echo.
echo Recommended alternatives:
echo   - Test modules individually (Option 2)
echo   - Use quick test mode (Option 1)
echo.
SET /P CONFIRM="Are you SURE you want to continue? (yes/NO): "

if /I NOT "%CONFIRM%"=="yes" (
    echo Cancelled.
    pause
    goto MAIN_MENU
)

SET MODULE=
SET LIMIT=

SET /P HTML_CHOICE="Generate HTML report? (Y/N): "
SET HTML=
if /I "%HTML_CHOICE%"=="Y" SET HTML=--html

goto RUN_TEST

REM ============================================================================
REM CUSTOM CONFIGURATION
REM ============================================================================
:CUSTOM_CONFIG
cls
echo.
echo ============================================================================
echo CUSTOM MUTATION TEST CONFIGURATION
echo ============================================================================
echo.

SET /P MODULE="Enter module name (leave empty for all modules): "

if NOT "%MODULE%"=="" (
    SET /P LIMIT="Enter mutation limit (leave empty for no limit): "
) else (
    SET LIMIT=
)

SET /P HTML_CHOICE="Generate HTML report? (Y/N): "
SET HTML=
if /I "%HTML_CHOICE%"=="Y" SET HTML=--html

goto RUN_TEST

REM ============================================================================
REM RUN THE ACTUAL TEST
REM ============================================================================
:RUN_TEST
cls
echo.
echo ============================================================================
echo MUTATION TEST CONFIGURATION
echo ============================================================================
echo.
if "%MODULE%"=="" (
    echo Target: %YELLOW%ALL modules%NC%
    echo Estimated time: %YELLOW%8-24+ hours%NC%
) else (
    echo Target: %CYAN%%MODULE%.py%NC%
    if "%LIMIT%"=="" (
        echo Mutations: %CYAN%All%NC%
    ) else (
        echo Mutations: %CYAN%Limited to %LIMIT%%NC%
    )
)
if /I "%HTML_CHOICE%"=="Y" (
    echo HTML Report: %GREEN%Yes%NC%
) else (
    echo HTML Report: No
)
echo ============================================================================
echo.
echo Press Ctrl+C to cancel, or
pause

REM Check Python installation
echo.
echo [Step 1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%ERROR: Python is not installed or not in PATH%NC%
    pause
    goto MAIN_MENU
)
echo %GREEN%✓ Python is installed%NC%

REM Check mutmut installation
echo.
echo [Step 2/5] Checking mutmut installation...
python -m mutmut --version >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%WARNING: mutmut has compatibility issues on Windows%NC%
    echo.
    echo You have two options:
    echo   1. Run this script in WSL (Windows Subsystem for Linux)
    echo   2. Use manual mutation testing (see MANUAL_MUTATION_TESTING.md)
    echo.
    echo To install WSL:
    echo   wsl --install
    echo.
    echo To run in WSL:
    echo   wsl
    echo   cd /mnt/c/Users/j`/Git-Repos/Fall-25-CS-5300
    echo   ./run_mutation_tests.sh
    echo.
    pause
    goto MAIN_MENU
)
echo %GREEN%✓ mutmut is installed%NC%

REM Check if tests pass
echo.
echo [Step 3/5] Running baseline tests...
echo This ensures tests pass before we start mutating code...
cd active_interview_backend
python manage.py test active_interview_app.tests --verbosity=0 >nul 2>&1
if errorlevel 1 (
    echo %RED%ERROR: Baseline tests are failing!%NC%
    echo You must fix failing tests before running mutation tests.
    echo.
    echo Run this command to see failures:
    echo   cd active_interview_backend
    echo   python manage.py test active_interview_app.tests
    echo.
    pause
    cd ..
    goto MAIN_MENU
)
cd ..
echo %GREEN%✓ Baseline tests passed%NC%

REM Create reports directory
echo.
echo [Step 4/5] Setting up reports directory...
if not exist "Research\mutation_testing" mkdir "Research\mutation_testing"
echo %GREEN%✓ Reports directory ready%NC%

REM Start mutation testing
echo.
echo [Step 5/5] Running mutation tests...
echo.
echo ============================================================================
echo MUTATION TESTING IN PROGRESS
echo ============================================================================
echo.
echo Started at: %DATE% %TIME%
echo.

REM Build command
SET CMD=python run_mutation_tests.py
if NOT "%MODULE%"=="" SET CMD=%CMD% --module %MODULE%
if NOT "%LIMIT%"=="" SET CMD=%CMD% --limit %LIMIT%
if "%HTML%"=="--html" SET CMD=%CMD% --html

echo Command: %CMD%
echo.
echo You can monitor progress below.
echo Feel free to minimize this window or do other work.
echo.
echo ============================================================================
echo.

REM Record start time
SET START_TIME=%TIME%

REM Run mutation tests
%CMD%

REM Record end time
SET END_TIME=%TIME%

echo.
echo ============================================================================
echo MUTATION TESTING COMPLETE
echo ============================================================================
echo.
echo Started:  %START_TIME%
echo Finished: %END_TIME%
echo.
echo Reports saved in: Research\mutation_testing\
echo.
echo %GREEN%View your results:%NC%
echo   1. Open Research\mutation_testing\mutation_report_*.md
if "%HTML%"=="--html" (
    echo   2. Open html\index.html in your browser
)
echo.
echo %GREEN%Next steps:%NC%
echo   1. Review the mutation score
echo   2. Check survived mutations: python -m mutmut results
echo   3. View specific mutations: python -m mutmut show [id]
echo   4. Add tests for survived mutations
echo.
echo.
SET /P MENU_CHOICE="Return to main menu? (Y/N): "
if /I "%MENU_CHOICE%"=="Y" goto MAIN_MENU
goto EXIT

REM ============================================================================
REM VIEW PREVIOUS RESULTS
REM ============================================================================
:VIEW_RESULTS
cls
echo.
echo ============================================================================
echo PREVIOUS MUTATION TEST REPORTS
echo ============================================================================
echo.

if not exist "Research\mutation_testing" (
    echo No reports found. Run a mutation test first.
    pause
    goto MAIN_MENU
)

echo Recent reports:
echo.
dir /B /O-D "Research\mutation_testing\mutation_report_*.md" 2>nul | findstr /N "^"

if errorlevel 1 (
    echo No reports found. Run a mutation test first.
) else (
    echo.
    echo Reports are located in: Research\mutation_testing\
    echo.
    SET /P VIEW_CHOICE="Enter report number to view (or 0 to go back): "

    if NOT "%VIEW_CHOICE%"=="0" (
        REM This would require more complex logic to open specific file
        echo.
        echo Opening reports folder...
        start Research\mutation_testing
    )
)

echo.
pause
goto MAIN_MENU

REM ============================================================================
REM SHOW HELP
REM ============================================================================
:SHOW_HELP
cls
echo.
echo ============================================================================
echo MUTATION TESTING HELP
echo ============================================================================
echo.
echo WHAT IS MUTATION TESTING?
echo   Mutation testing evaluates test quality by making small changes
echo   (mutations) to your code and checking if tests catch them.
echo.
echo   - KILLED mutation = Tests detected the change (GOOD!)
echo   - SURVIVED mutation = Tests missed the change (Need more tests)
echo.
echo MUTATION SCORE:
echo   Percentage of mutations killed by your tests
echo   - 80%%+ = Excellent test coverage
echo   - 60-80%% = Good test coverage
echo   - 40-60%% = Fair, needs improvement
echo   - Below 40%% = Poor, needs significant work
echo.
echo WHICH OPTION TO CHOOSE?
echo   1. QUICK TEST: Best for getting started and rapid feedback
echo      - Tests one module with limited mutations
echo      - Takes 20-40 minutes
echo      - Perfect for iterative development
echo.
echo   2. FULL MODULE: Complete analysis of one module
echo      - Tests all mutations in one module
echo      - Takes 30-90 minutes per module
echo      - Good for thorough module validation
echo.
echo   3. FULL APP: Comprehensive testing (rarely needed)
echo      - Tests entire application
echo      - Takes 8-24+ hours
echo      - Only use before major releases
echo.
echo TIPS:
echo   - Start with Quick Test on pdf_export or permissions
echo   - Fix survived mutations by adding test cases
echo   - Use HTML reports for visual analysis
echo   - Run baseline tests first to ensure they pass
echo.
echo DOCUMENTATION:
echo   - See MUTATION_TESTING_GUIDE.md for detailed info
echo   - See MANUAL_MUTATION_TESTING.md for alternatives
echo   - See Research\mutation_testing\ for past results
echo.
echo ============================================================================
echo.
pause
goto MAIN_MENU

REM ============================================================================
REM EXIT
REM ============================================================================
:EXIT
echo.
echo Goodbye!
echo.
exit /b 0
