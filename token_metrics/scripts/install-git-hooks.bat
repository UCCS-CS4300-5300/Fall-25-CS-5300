@echo off
REM Install Git Hooks (Windows)
REM
REM This script installs custom git hooks for the repository.
REM It copies files from .githooks to .git/hooks directory.

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo            Git Hooks Installation Script (Windows)
echo ============================================================
echo.

REM Get repository root
for /f "delims=" %%i in ('git rev-parse --show-toplevel') do set REPO_ROOT=%%i

REM Convert forward slashes to backslashes for Windows
set REPO_ROOT=%REPO_ROOT:/=\%

set HOOKS_DIR=%REPO_ROOT%\.githooks
set GIT_HOOKS_DIR=%REPO_ROOT%\.git\hooks

REM Check if .githooks directory exists
if not exist "%HOOKS_DIR%" (
    echo ERROR: .githooks directory not found
    echo Expected: %HOOKS_DIR%
    exit /b 1
)

REM Check if .git/hooks directory exists
if not exist "%GIT_HOOKS_DIR%" (
    echo ERROR: .git/hooks directory not found
    echo Expected: %GIT_HOOKS_DIR%
    echo Are you in a git repository?
    exit /b 1
)

set INSTALLED=0
set SKIPPED=0

echo Installing git hooks...
echo.

REM Install hooks
for %%f in ("%HOOKS_DIR%\*") do (
    set "hook_name=%%~nxf"
    set "source=%%f"
    set "target=%GIT_HOOKS_DIR%\!hook_name!"

    REM Check if hook already exists
    if exist "!target!" (
        REM Backup existing hook
        set "timestamp=%date:~-4%%date:~-10,2%%date:~-7,2%-%time:~0,2%%time:~3,2%%time:~6,2%"
        set "timestamp=!timestamp: =0!"
        set "backup=!target!.backup-!timestamp!"

        echo Backing up: !hook_name! -^> !backup!
        move "!target!" "!backup!" >nul
    )

    REM Copy hook
    copy "!source!" "!target!" >nul

    echo Installed: !hook_name!
    set /a INSTALLED+=1
)

echo.
echo ============================================================
echo                  Installation Summary
echo ============================================================
echo.
echo   Installed: %INSTALLED% hook(s)
echo.

if %INSTALLED% gtr 0 (
    echo Git hooks installed successfully!
    echo.
    echo Installed hooks:

    for %%f in ("%HOOKS_DIR%\*") do (
        set "hook_name=%%~nxf"
        echo   * !hook_name!

        if "!hook_name!"=="post-commit" (
            echo     -^> Prompts to track Claude Code token usage after commits
        )
    )
) else (
    echo No new hooks were installed
)

echo.
echo Tip: You can disable hooks temporarily with:
echo   git commit --no-verify
echo.

endlocal
