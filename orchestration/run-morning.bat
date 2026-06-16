@echo off
setlocal

REM PROJECT_ROOT is the parent of the orchestration/ folder
set "PROJECT_ROOT=%~dp0.."
set "LOG=%PROJECT_ROOT%\phases\02_curate\logs\run.log"

REM Idempotency guard — derive YYYYMMDD via wmic (locale-independent)
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set _DT=%%I
set TODAY=%_DT:~0,8%
set "DONE_FLAG=%PROJECT_ROOT%\phases\02_curate\logs\morning_%TODAY%.done"

if exist "%DONE_FLAG%" (
    echo [%DATE% %TIME%] SKIP: morning upload already completed today ^(sentinel: %DONE_FLAG%^). >> "%LOG%"
    echo [%DATE% %TIME%] Delete the sentinel file to force a re-run. >> "%LOG%"
    exit /b 0
)

echo [%DATE% %TIME%] === Morning Run Started === >> "%LOG%"

REM Step 1: Run the Python news scraper
echo [%DATE% %TIME%] Running scraper... >> "%LOG%"
cd /d "%PROJECT_ROOT%\phases\01_scrape"
call run.bat >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] ERROR: Scraper failed. >> "%LOG%"
    exit /b 1
)
echo [%DATE% %TIME%] Scraper finished. >> "%LOG%"

REM Step 2: Run HSX insider trading collection for the morning report.
REM Morning run at 7:55 covers the previous 16 hours, avoiding overlap with afternoon.
echo [%DATE% %TIME%] Running HSX insider trading pipeline... >> "%LOG%"
cd /d "%PROJECT_ROOT%\phases\01_scrape"
venv\Scripts\python.exe hsx_insider_scraper.py --session morning >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] WARNING: HSX insider scraper failed. Continuing news pipeline. >> "%LOG%"
) else (
    echo [%DATE% %TIME%] Preparing HSX PDFs and images... >> "%LOG%"
    venv\Scripts\python.exe hsx_prepare_pdfs.py >> "%LOG%" 2>&1
    if errorlevel 1 (
        echo [%DATE% %TIME%] WARNING: HSX PDF/image preparation failed. >> "%LOG%"
    )
    for /f "delims=" %%F in ('dir /b /o-d hsx_insider_trading_*_extracted.json 2^>nul') do (
        venv\Scripts\python.exe format_hsx_trading_news.py "%%F" >> "%LOG%" 2>&1
        goto :morning_hsx_done
    )
)
:morning_hsx_done

REM Step 3: Upload to Google Sheets
echo [%DATE% %TIME%] Uploading to Sheets... >> "%LOG%"
cd /d "%PROJECT_ROOT%\phases\02_curate"
node upload-to-sheets.js morning >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] ERROR: Upload failed. >> "%LOG%"
    exit /b 1
)

REM Write sentinel so re-runs are blocked for the rest of the day
echo done > "%DONE_FLAG%"

echo [%DATE% %TIME%] === Morning Run Complete === >> "%LOG%"
endlocal
