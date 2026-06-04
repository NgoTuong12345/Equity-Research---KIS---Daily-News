@echo off
setlocal

set "BASE_DIR=C:\Users\Administrator\Playwright-Daily-News"
set "LOG=%BASE_DIR%\google-sheets-uploader\logs\run.log"

echo [%DATE% %TIME%] === Afternoon Run Started === >> "%LOG%"

REM Step 1: Run the Python news scraper
echo [%DATE% %TIME%] Running scraper... >> "%LOG%"
cd /d "%BASE_DIR%\vietnam_news_scraper"
call run.bat >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] ERROR: Scraper failed. >> "%LOG%"
    exit /b 1
)
echo [%DATE% %TIME%] Scraper finished. >> "%LOG%"

REM Step 2: Upload to Google Sheets
echo [%DATE% %TIME%] Uploading to Sheets... >> "%LOG%"
cd /d "%BASE_DIR%\google-sheets-uploader"
node upload-to-sheets.js afternoon >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] ERROR: Upload failed. >> "%LOG%"
    exit /b 1
)

echo [%DATE% %TIME%] === Afternoon Run Complete === >> "%LOG%"
endlocal
