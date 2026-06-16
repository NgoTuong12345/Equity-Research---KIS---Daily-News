@echo off
setlocal enabledelayedexpansion

REM Get the directory of this script (orchestration folder)
set "SCRIPT_DIR=%~dp0"
REM Remove trailing backslash if present
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "MORNING_BAT=%SCRIPT_DIR%\run-morning.bat"
set "AFTERNOON_BAT=%SCRIPT_DIR%\run-afternoon.bat"

echo ===================================================
echo  KIS Daily News - Windows Task Scheduler Installer
echo ===================================================
echo.
echo Installing scheduled tasks for the current user: %USERNAME%
echo.
echo [1/2] Creating KIS-Daily-News-Morning task...
echo Target: "%MORNING_BAT%"
schtasks /create /tn "KIS-Daily-News-Morning" /tr "\"%MORNING_BAT%\"" /sc daily /st 07:55 /it /f
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create morning task.
    goto :error
)

echo.
echo [2/2] Creating KIS-Daily-News-Afternoon task...
echo Target: "%AFTERNOON_BAT%"
schtasks /create /tn "KIS-Daily-News-Afternoon" /tr "\"%AFTERNOON_BAT%\"" /sc daily /st 15:00 /it /f
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create afternoon task.
    goto :error
)

echo.
echo ===================================================
echo  Installation Complete!
echo ===================================================
echo Both tasks have been successfully scheduled:
echo  - Morning Run: Daily at 07:55 AM (Interactive)
echo  - Afternoon Run: Daily at 15:00 (3:00 PM) (Interactive)
echo.
echo These tasks are set to run only when you are logged on.
echo This ensures Playwright and Chrome can access your session profile.
echo.
pause
exit /b 0

:error
echo.
echo [ERROR] Installation failed. Make sure you run this script as administrator if permission is denied.
pause
exit /b 1
