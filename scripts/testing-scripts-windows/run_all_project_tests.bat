@echo off
cd /d "%~dp0active_interview_backend"
echo.
echo Running ALL project tests...
echo This may take a while...
echo.
python -m pytest active_interview_app\tests\ -v --tb=short
echo.
echo Exit code: %ERRORLEVEL%
echo.
echo All tests completed. Press any key to exit.
pause
