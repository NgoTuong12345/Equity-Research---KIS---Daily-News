# Scrape & Upload to Google Sheets

Use this skill when the user runs `/scrape-and-upload` or asks to start the scraping + Sheets upload process manually (outside of the Windows Task Scheduler).

## Purpose

Run the full data collection pipeline for a given session (morning or afternoon):
1. Scrape Vietnam financial news → CSV
2. Collect HSX insider trading data
3. Upload the CSV to the correct Google Sheets tab

---

## Step 0 — Confirm Session

Ask the user which session to run if not already stated:

```
Which session?
  morning   — use for the 08:00 run (covers last 24 h of news)
  afternoon — use for the 15:00 run (covers last 7 h from morning boundary)
```

Set `{SESSION}` = `morning` or `afternoon`.

---

## ⛔ Idempotency Guard — Check Before Running Anything

**This step is mandatory. Do not skip it.**

Derive today's sheet tab name:
- Morning → `mor_DD_MM_YYYY` (e.g. `mor_16_06_2026`)
- Afternoon → `after_DD_MM_YYYY` (e.g. `after_16_06_2026`)

Check the sentinel file:

```
phases\02_curate\logs\{session}_{YYYYMMDD}.done
```

- **If the file exists** → the upload already ran successfully today for this session.

  Stop immediately and show:
  ```
  ⛔ Upload already completed for {tab_name} today.
     Sentinel: phases\02_curate\logs\{session}_{YYYYMMDD}.done

  Re-running would overwrite the sheet tab and destroy any TAKE values
  already marked by the analyst.

  To force a re-run, the user must delete the sentinel file first:
    del "phases\02_curate\logs\{session}_{YYYYMMDD}.done"
  ```

  Do NOT proceed to Step 1 under any circumstances unless the user explicitly confirms they deleted the sentinel and wants to re-run.

- **If the file does not exist** → no upload has run yet. Proceed to Step 1.

---

## Step 1 — Run the News Scraper

```
cd phases\01_scrape
call run.bat
```

This:
- Creates / activates the Python venv automatically
- Installs dependencies if missing
- Runs `main.py` to scrape Vietnam financial news RSS feeds + web sources
- Outputs a timestamped CSV: `phases\01_scrape\vietnam_financial_news_combined_{YYYYMMDD}_{HHMM}.csv`

Wait for it to finish. Report the output CSV filename on success.

If it fails, show the error and stop — do not proceed to Step 2.

---

## Step 2 — Run HSX Insider Trading Pipeline

**2a — Scrape raw disclosures:**

```
cd phases\01_scrape
venv\Scripts\python.exe hsx_insider_scraper.py
```

**2b — Download PDFs and render to PNGs** (required for AI agent extraction):

```
venv\Scripts\python.exe hsx_prepare_pdfs.py
```

This downloads the PDF attachments from the latest `hsx_insider_trading_*.json`, renders each page to a PNG, and saves a manifest JSON at `phases\01_scrape\{timestamp}_manifest.json`. The PNG images are written to `phases\01_scrape\pdf_images\`.

**2c — Prepare unique transactions for agent formatting:**

```
for /f "delims=" %F in ('dir /b /o-d hsx_insider_trading_*_extracted.json') do (
    venv\Scripts\python.exe format_hsx_trading_news.py --prepare "%F"
    goto done
)
:done
```

This writes `*_to_format.json` with deduplicated transactions.

**2d — Agent reads `*_to_format.json` and writes `*_agent_formatted.json`:**

The agent (Claude) reads `phases\01_scrape\*_to_format.json`, translates each transaction into bilingual `summary_vn` and `summary_en` prose following KIS trading-item rules, and writes the result to `phases\01_scrape\*_agent_formatted.json`.

**2e — Merge agent output into final formatted file:**

```
for /f "delims=" %F in ('dir /b /o-d hsx_insider_trading_*_extracted.json') do (
    venv\Scripts\python.exe format_hsx_trading_news.py --merge "%F"
    goto done
)
:done
```

This writes `*_extracted_formatted.json`, `*_extracted_EN.txt`, and `*_extracted_VN.txt`.

If any sub-step of the HSX pipeline fails, log a warning and **continue** — this step is non-blocking for the upload.

---

## Step 3 — Upload to Google Sheets

```
cd phases\02_curate
node upload-to-sheets.js {SESSION}
```

This:
- Finds the most recently modified `vietnam_financial_news_combined_*.csv` in `phases\01_scrape\`
- Opens Chrome using the saved user profile (auto-authenticated with Google)
- Creates a new sheet tab named `mor_DD_MM_YYYY` (morning) or `after_DD_MM_YYYY` (afternoon), or reuses + clears it if it already exists
- Pastes the CSV data into columns A–H
- Adds IF formulas in columns I (`corp_url`) and J (`poli_url`) for all data rows
- Bolds the header row

Sheets URL: `https://docs.google.com/spreadsheets/d/1PPjukC3surCnTBPAjfotk_gSckeWQY24UJCWwFuEVtw/edit`

Log is written to: `phases\02_curate\logs\upload.log`

---

## Step 4 — Write Sentinel & Confirm

After the upload script exits successfully, write the sentinel file to prevent accidental re-runs:

```
echo done > "phases\02_curate\logs\{SESSION}_{YYYYMMDD}.done"
```

Then report:

```
✓ Scraper: {csv_filename}
✓ HSX insider: formatted (or: skipped — scraper failed)
✓ Sheets tab "{tab_name}" updated
  → https://docs.google.com/spreadsheets/d/1PPjukC3surCnTBPAjfotk_gSckeWQY24UJCWwFuEVtw/edit
✓ Sentinel written: phases\02_curate\logs\{SESSION}_{YYYYMMDD}.done
```

If upload fails, do NOT write the sentinel. Show the last 20 lines of `phases\02_curate\logs\upload.log` and ask the user how to proceed.

---

## Notes

- The full automated version of this pipeline runs via Windows Task Scheduler using `orchestration\run-morning.bat` and `orchestration\run-afternoon.bat`
- This skill is for **manual / on-demand** runs only
- The upload script kills and relaunches Chrome — warn the user to save any open Chrome work before proceeding
