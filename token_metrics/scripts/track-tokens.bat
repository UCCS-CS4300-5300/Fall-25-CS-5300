@echo off
REM Claude Code Token Tracker - Simplified Interface
REM
REM Usage:
REM   track-tokens.bat                    - Show usage summary (default)
REM   track-tokens.bat --help             - Show this help
REM   track-tokens.bat --add              - Track tokens interactively
REM   track-tokens.bat --add 1000 500     - Track specific counts
REM   track-tokens.bat --trends           - Show detailed trends
REM   track-tokens.bat --export file.csv  - Export to CSV

setlocal EnableDelayedExpansion

set SCRIPT_DIR=%~dp0
set REPO_ROOT=%SCRIPT_DIR%..\..

REM Default values
set ACTION=show
set DAYS=30
set OUTPUT_FILE=
set INPUT_TOKENS=
set OUTPUT_TOKENS=
set NOTES=

REM Parse arguments
:parse_args
if "%~1"=="" goto execute

if /i "%~1"=="-h" goto show_help
if /i "%~1"=="--help" goto show_help
if /i "%~1"=="/?" goto show_help

if /i "%~1"=="-a" goto parse_add
if /i "%~1"=="--add" goto parse_add

if /i "%~1"=="--auto" (
    set ACTION=auto
    shift
    goto parse_args
)

if /i "%~1"=="-s" goto parse_show
if /i "%~1"=="--show" goto parse_show

if /i "%~1"=="-t" goto parse_trends
if /i "%~1"=="--trends" goto parse_trends

if /i "%~1"=="--all" (
    set ACTION=all
    shift
    goto parse_args
)

if /i "%~1"=="-e" goto parse_export
if /i "%~1"=="--export" goto parse_export

if /i "%~1"=="-d" goto parse_dashboard
if /i "%~1"=="--dashboard" goto parse_dashboard

echo ❌ Unknown option: %~1
echo.
echo Run 'track-tokens.bat --help' for usage information
exit /b 1

:parse_add
set ACTION=add
shift
REM Check if next arg is a number
echo %~1| findstr /r "^[0-9][0-9]*$" >nul
if %errorlevel% equ 0 (
    set INPUT_TOKENS=%~1
    shift
    echo %~1| findstr /r "^[0-9][0-9]*$" >nul
    if %errorlevel% equ 0 (
        set OUTPUT_TOKENS=%~1
        shift
        REM Check for notes (not a flag)
        if not "%~1"=="" (
            echo %~1| findstr /r "^-" >nul
            if %errorlevel% neq 0 (
                set NOTES=%~1
                shift
            )
        )
    )
)
goto parse_args

:parse_show
set ACTION=show
shift
echo %~1| findstr /r "^[0-9][0-9]*$" >nul
if %errorlevel% equ 0 (
    set DAYS=%~1
    shift
)
goto parse_args

:parse_trends
set ACTION=trends
shift
echo %~1| findstr /r "^[0-9][0-9]*$" >nul
if %errorlevel% equ 0 (
    set DAYS=%~1
    shift
)
goto parse_args

:parse_export
set ACTION=export
shift
if not "%~1"=="" (
    echo %~1| findstr /r "^-" >nul
    if %errorlevel% neq 0 (
        set OUTPUT_FILE=%~1
        shift
    ) else (
        set OUTPUT_FILE=token_usage_export.csv
    )
) else (
    set OUTPUT_FILE=token_usage_export.csv
)
goto parse_args

:parse_dashboard
set ACTION=dashboard
shift
if not "%~1"=="" (
    echo %~1| findstr /r "^-" >nul
    if %errorlevel% neq 0 (
        set OUTPUT_FILE=%~1
        shift
    ) else (
        set OUTPUT_FILE=token_dashboard.html
    )
) else (
    set OUTPUT_FILE=token_dashboard.html
)
goto parse_args

:show_help
echo ╔═══════════════════════════════════════════════════════╗
echo ║       📊 CLAUDE CODE TOKEN TRACKER                   ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo USAGE:
echo   track-tokens.bat [OPTIONS]
echo.
echo DEFAULT ^(no arguments^):
echo   Shows quick usage summary for current branch ^(last 30 days^)
echo.
echo OPTIONS:
echo.
echo   -h, --help, /?
echo       Show this help message
echo.
echo   -a, --add [INPUT] [OUTPUT] [NOTES]
echo       Track tokens
echo       • No args: Interactive mode ^(prompts for input^)
echo       • With args: Track specific counts
echo       Examples:
echo         track-tokens.bat --add                    # Interactive
echo         track-tokens.bat -a 10000 5000            # Quick add
echo         track-tokens.bat -a 10000 5000 "Bug fix" # With notes
echo.
echo   --auto
echo       Attempt automatic token extraction from Claude logs
echo       Example:
echo         track-tokens.bat --auto
echo.
echo   -s, --show [DAYS]
echo       Show usage summary
echo       • Default: Last 30 days
echo       • 0 = All time
echo       Examples:
echo         track-tokens.bat --show      # Last 30 days
echo         track-tokens.bat -s 7        # Last 7 days
echo         track-tokens.bat -s 0        # All time
echo.
echo   -t, --trends [DAYS]
echo       Show detailed trends with daily/weekly breakdown
echo       • Default: Last 30 days
echo       Examples:
echo         track-tokens.bat --trends    # Last 30 days
echo         track-tokens.bat -t 90       # Last 90 days
echo.
echo   --all
echo       Show complete analysis ^(all time, all branches^)
echo       Example:
echo         track-tokens.bat --all
echo.
echo   -e, --export [FILE]
echo       Export to CSV
echo       • Default: token_usage_export.csv
echo       Examples:
echo         track-tokens.bat --export              # Default filename
echo         track-tokens.bat -e monthly_jan.csv    # Custom filename
echo.
echo   -d, --dashboard [FILE]
echo       Generate interactive HTML dashboard
echo       • Default: token_dashboard.html
echo       • Automatically opens in browser
echo       Examples:
echo         track-tokens.bat --dashboard           # Default filename
echo         track-tokens.bat -d report.html        # Custom filename
echo.
echo COMMON WORKFLOWS:
echo.
echo   Daily check:
echo     track-tokens.bat
echo.
echo   Track new session:
echo     track-tokens.bat --add
echo.
echo   Weekly review:
echo     track-tokens.bat --trends
echo.
echo   Monthly export:
echo     track-tokens.bat --export monthly_202501.csv
echo.
echo   Generate dashboard:
echo     track-tokens.bat --dashboard
echo.
echo AUTOMATION:
echo   For automated tracking, see:
echo     automate-tracking.bat --help
echo.
exit /b 0

:execute
REM Execute based on action
if "%ACTION%"=="add" goto action_add
if "%ACTION%"=="auto" goto action_auto
if "%ACTION%"=="show" goto action_show
if "%ACTION%"=="trends" goto action_trends
if "%ACTION%"=="all" goto action_all
if "%ACTION%"=="export" goto action_export
if "%ACTION%"=="dashboard" goto action_dashboard

:action_add
if "%INPUT_TOKENS%"=="" (
    echo 🤖 Interactive Token Tracking
    python %SCRIPT_DIR%track-claude-tokens.py --interactive
) else (
    if "%OUTPUT_TOKENS%"=="" (
        echo ❌ Error: Need both input and output tokens
        echo Usage: track-tokens.bat --add [input-tokens] [output-tokens]
        exit /b 1
    )

    if not "%NOTES%"=="" (
        python %SCRIPT_DIR%track-claude-tokens.py --input-tokens %INPUT_TOKENS% --output-tokens %OUTPUT_TOKENS% --notes "%NOTES%"
    ) else (
        python %SCRIPT_DIR%track-claude-tokens.py --input-tokens %INPUT_TOKENS% --output-tokens %OUTPUT_TOKENS%
    )
)
exit /b %ERRORLEVEL%

:action_auto
echo 🔍 Attempting automatic token extraction...
python %SCRIPT_DIR%extract-claude-tokens.py --auto-track
exit /b %ERRORLEVEL%

:action_show
python %SCRIPT_DIR%analyze-token-trends.py --days %DAYS%
exit /b %ERRORLEVEL%

:action_trends
python %SCRIPT_DIR%analyze-token-trends.py --days %DAYS% --daily --weekly --insights
exit /b %ERRORLEVEL%

:action_all
python %SCRIPT_DIR%analyze-token-trends.py --days 0 --all
exit /b %ERRORLEVEL%

:action_export
if "%OUTPUT_FILE%"=="" set OUTPUT_FILE=token_usage_export.csv
echo 📊 Exporting to %OUTPUT_FILE%...
python %SCRIPT_DIR%analyze-token-trends.py --days 0 --export-csv %OUTPUT_FILE%
if %ERRORLEVEL% equ 0 (
    echo ✅ Export complete: %OUTPUT_FILE%
)
exit /b %ERRORLEVEL%

:action_dashboard
if "%OUTPUT_FILE%"=="" set OUTPUT_FILE=token_dashboard.html
echo 📊 Generating dashboard...
python %SCRIPT_DIR%generate-dashboard.py --output %OUTPUT_FILE%
if %ERRORLEVEL% equ 0 (
    echo ✅ Dashboard created: %OUTPUT_FILE%
    echo 🌐 Opening in browser...
    start "" "%OUTPUT_FILE%"
)
exit /b %ERRORLEVEL%
