@echo off
cd /d "%~dp0active_interview_backend"
echo Running all tests with coverage...
python -m coverage run manage.py test -v 2
echo.
echo Generating coverage report for all files...
python -m coverage report -m
