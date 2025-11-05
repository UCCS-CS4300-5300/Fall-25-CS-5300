@echo off
REM Quick launcher for token tracking
REM All token functionality is in token_metrics/ folder

echo.
echo Token Tracking Quick Launcher
echo =============================
echo.

if "%1"=="" (
    echo Commands:
    echo   track-tokens.bat add [count] [notes]     - Add tokens
    echo   track-tokens.bat show                    - Show total
    echo   track-tokens.bat submit                  - Submit to DB
    echo   track-tokens.bat export [file]           - Export
    echo   track-tokens.bat import [file]           - Import
    echo   track-tokens.bat help                    - Full docs
    echo.
    echo Examples:
    echo   track-tokens.bat add 50000 "My feature"
    echo   track-tokens.bat show
    echo   track-tokens.bat submit
    echo.
    exit /b 0
)

if /i "%1"=="add" (
    if "%2"=="" (
        echo Error: Token count required
        echo Usage: track-tokens.bat add [count] [notes] [--auto-export]
        exit /b 1
    )
    cd token_metrics
    call add-tokens.bat %2 "%~3" %4
    cd ..
    exit /b %errorlevel%
)

if /i "%1"=="show" (
    cd token_metrics
    call show-tokens.bat
    cd ..
    exit /b %errorlevel%
)

if /i "%1"=="submit" (
    cd token_metrics
    call submit-tokens.bat
    cd ..
    exit /b %errorlevel%
)

if /i "%1"=="export" (
    if "%2"=="" (
        echo Error: Filename required
        echo Usage: track-tokens.bat export [filename]
        exit /b 1
    )
    cd token_metrics
    call export-tokens.bat %2
    cd ..
    exit /b %errorlevel%
)

if /i "%1"=="import" (
    if "%2"=="" (
        echo Error: Filename required
        echo Usage: track-tokens.bat import [filename] [--merge]
        exit /b 1
    )
    cd token_metrics
    call import-tokens.bat %2 %3
    cd ..
    exit /b %errorlevel%
)

if /i "%1"=="help" (
    echo.
    echo Full documentation: token_metrics\docs\TOKEN_TRACKING_GUIDE.md
    echo Quick reference: token_metrics\docs\QUICK_TOKEN_REFERENCE.md
    echo.
    echo Or navigate to token_metrics folder for direct access:
    echo   cd token_metrics
    echo   add-tokens.bat [count] [notes]
    echo.
    pause
    exit /b 0
)

echo Unknown command: %1
echo Run without arguments for help
exit /b 1
