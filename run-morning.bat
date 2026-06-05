@echo off
setlocal

set "BASE_DIR=C:\Users\Administrator\Playwright-Daily-News"
set "LOG=%BASE_DIR%\google-sheets-uploader\logs\run.log"

echo [%DATE% %TIME%] === Morning Run Started === >> "%LOG%"

REM Step 1: Run the Python news scraper
echo [%DATE% %TIME%] Running scraper... >> "%LOG%"
cd /d "%BASE_DIR%\vietnam_news_scraper"
call run.bat >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] ERROR: Scraper failed. >> "%LOG%"
    exit /b 1
)
echo [%DATE% %TIME%] Scraper finished. >> "%LOG%"

REM Step 2: Run HSX insider trading collection for the morning report.
REM Morning run at 7:55 covers the previous 16 hours, avoiding overlap with afternoon.
echo [%DATE% %TIME%] Running HSX insider trading pipeline... >> "%LOG%"
cd /d "%BASE_DIR%\vietnam_news_scraper"
venv\Scripts\python.exe hsx_insider_scraper.py >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] WARNING: HSX insider scraper failed. Continuing news pipeline. >> "%LOG%"
) else (
    venv\Scripts\python.exe hsx_nlm_extractor.py >> "%LOG%" 2>&1
    if errorlevel 1 (
        echo [%DATE% %TIME%] WARNING: HSX NotebookLM extraction failed. Continuing news pipeline. >> "%LOG%"
    ) else (
        for /f "delims=" %%F in ('dir /b /o-d hsx_insider_trading_*_extracted.json 2^>nul') do (
            venv\Scripts\python.exe format_hsx_trading_news.py "%%F" >> "%LOG%" 2>&1
            goto :morning_hsx_done
        )
    )
)
:morning_hsx_done

REM Step 3: Upload to Google Sheets
echo [%DATE% %TIME%] Uploading to Sheets... >> "%LOG%"
cd /d "%BASE_DIR%\google-sheets-uploader"
node upload-to-sheets.js morning >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] ERROR: Upload failed. >> "%LOG%"
    exit /b 1
)

echo [%DATE% %TIME%] === Morning Run Complete === >> "%LOG%"
endlocal
