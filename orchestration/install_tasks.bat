@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "MORNING_BAT=%SCRIPT_DIR%\run_morning.bat"
set "AFTERNOON_BAT=%SCRIPT_DIR%\run_afternoon.bat"

echo ===================================================
echo  KIS Daily News - Windows Task Scheduler Installer
echo ===================================================
echo.
echo Installing scheduled tasks for current user: %USERNAME%
echo Project Path: %SCRIPT_DIR%\..
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
exit /b 0

:error
echo.
echo [ERROR] Installation failed.
exit /b 1
