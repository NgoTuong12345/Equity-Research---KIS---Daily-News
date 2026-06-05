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

REM Step 2: Run HSX insider trading collection for the afternoon report.
REM Afternoon run at 15:00 covers the last 7 hours from the morning boundary.
echo [%DATE% %TIME%] Running HSX insider trading pipeline [7h]... >> "%LOG%"
cd /d "%BASE_DIR%\vietnam_news_scraper"
venv\Scripts\python.exe hsx_insider_scraper.py --hours 7 >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] WARNING: HSX insider scraper failed. Continuing news pipeline. >> "%LOG%"
) else (
    venv\Scripts\python.exe hsx_nlm_extractor.py >> "%LOG%" 2>&1
    if errorlevel 1 (
        echo [%DATE% %TIME%] WARNING: HSX NotebookLM extraction failed. Continuing news pipeline. >> "%LOG%"
    ) else (
        for /f "delims=" %%F in ('dir /b /o-d hsx_insider_trading_*_extracted.json 2^>nul') do (
            venv\Scripts\python.exe format_hsx_trading_news.py "%%F" >> "%LOG%" 2>&1
            goto :afternoon_hsx_done
        )
    )
)
:afternoon_hsx_done

REM Step 3: Upload to Google Sheets
echo [%DATE% %TIME%] Uploading to Sheets... >> "%LOG%"
cd /d "%BASE_DIR%\google-sheets-uploader"
node upload-to-sheets.js afternoon >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] ERROR: Upload failed. >> "%LOG%"
    exit /b 1
)

echo [%DATE% %TIME%] === Afternoon Run Complete === >> "%LOG%"
endlocal
