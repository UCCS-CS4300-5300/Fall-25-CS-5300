@echo off
cd /d "%~dp0active_interview_backend"
echo.
echo Current directory: %CD%
echo.
echo Checking if pytest is installed...
python -m pytest --version
echo.
echo Running specific test...
echo Command: python -m pytest active_interview_app\tests\test_views_coverage_boost.py::GenerateReportAITest::test_generate_report_rationale_parsing -v
echo.
python -m pytest active_interview_app\tests\test_views_coverage_boost.py::GenerateReportAITest::test_generate_report_rationale_parsing -v
echo.
echo Exit code: %ERRORLEVEL%
echo.
echo Test completed. Press any key to exit.
pause
