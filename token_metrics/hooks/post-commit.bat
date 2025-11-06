@echo off
REM Git Post-Commit Hook - Automatic Claude Token Tracking (Windows)
REM
REM This hook runs after every commit and attempts to track
REM Claude Code token usage automatically.
REM
REM Installation:
REM   Copy this file to .git\hooks\post-commit.bat
REM   Or run: token_metrics\hooks\install-hooks.bat

echo.
echo Auto-tracking Claude Code tokens...
python token_metrics\scripts\extract-claude-tokens.py --auto-track --notes "Auto-tracked on commit" --silent

exit /b 0
