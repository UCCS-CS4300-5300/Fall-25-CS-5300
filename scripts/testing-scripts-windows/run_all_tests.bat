@echo off
cd /d "%~dp0active_interview_backend"
echo.
echo Running all tests in test_views_coverage_boost.py...
echo.
python -m pytest active_interview_app\tests\test_views_coverage_boost.py -v
echo.
echo Exit code: %ERRORLEVEL%
echo.
echo Tests completed. Press any key to exit.
pause
