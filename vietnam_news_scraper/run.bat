@echo off
setlocal enabledelayedexpansion

REM Check if running in interactive mode
if "%INTERACTIVE_MODE%"=="" set INTERACTIVE_MODE=1
if "%TERM%"=="" set INTERACTIVE_MODE=0

echo ===================================================
echo  Vietnam Financial News Scraper - Bootstrapper
echo ===================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python (3.8 or newer) and check "Add Python to PATH".
    echo.
    if %INTERACTIVE_MODE% equ 1 pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo [INFO] Creating virtual environment (venv)...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        if %INTERACTIVE_MODE% equ 1 pause
        exit /b 1
    )
)

:: Activate virtual environment and install requirements
echo [INFO] Activating virtual environment...
call venv\Scripts\activate

echo [INFO] Installing/updating dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo [ERROR] Failed to install dependencies.
    if %INTERACTIVE_MODE% equ 1 pause
    exit /b 1
)

echo.
echo ===================================================
echo  Running Scraper...
echo ===================================================
echo.
python main.py
if !errorlevel! neq 0 (
    echo [ERROR] Scraper failed with exit code !errorlevel!
    if %INTERACTIVE_MODE% equ 1 pause
    exit /b !errorlevel!
)

echo.
echo ===================================================
echo  Scraper Finished!
echo ===================================================
echo.
if %INTERACTIVE_MODE% equ 1 pause
