@echo off
REM Install Git Hooks for Automatic Token Tracking
REM
REM This script installs git hooks that automatically track
REM Claude Code token usage when you commit.

echo.
echo ========================================
echo  Installing Git Hooks
echo ========================================
echo.

REM Check if .git directory exists
if not exist .git\ (
    echo Error: Not in a git repository root
    echo Please run this from the repository root directory
    exit /b 1
)

REM Create hooks directory if it doesn't exist
if not exist .git\hooks\ (
    mkdir .git\hooks
)

echo Installing post-commit hook...

REM Copy the Windows batch version
copy /Y token_metrics\hooks\post-commit.bat .git\hooks\post-commit.bat

REM Try to copy the Unix version too (for Git Bash)
copy /Y token_metrics\hooks\post-commit .git\hooks\post-commit 2>nul

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo The post-commit hook has been installed.
echo.
echo What happens now:
echo   1. Every time you commit, the hook runs
echo   2. It tries to detect your Claude token usage
echo   3. If found, it auto-saves to temp/ folder
echo   4. When you push, CI/CD imports your tokens
echo.
echo Test it:
echo   git commit -m "test"
echo   You should see "Auto-tracking Claude Code tokens..."
echo.
echo To uninstall:
echo   del .git\hooks\post-commit.bat
echo   del .git\hooks\post-commit
echo.

pause
