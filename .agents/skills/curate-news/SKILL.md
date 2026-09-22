---
name: curate-news
description: Pull human TAKE selections from Google Sheets to build the source markdown report file, then auto-chain to summarize-news.
---

# Curate News — Pull TAKE Selections from Google Sheets

Use this skill after the user has finished marking TAKE rows in Google Sheets, OR when the user runs `/curate-news` directly.

This is the **mandatory bridge** between human curation (Step 1) and LLM summarization (Step 2). It must run before `/summarize-news`.

---

## Purpose

1. Open the dated sheet tab (e.g. `mor_16_06_2026`) in Google Sheets
2. Read all rows where column E (`news_corp_select`) or column F (`news_poli_select`) = TAKE
3. Build a structured source markdown file that the summarizer reads
4. Auto-chain to `/summarize-news`

---

## Step 0 — Confirm Session & Base

Confirm `{SESSION}` = `morning` or `afternoon`.

Derive `{base}` from today's date and session:
- Morning → `mor_DDMMYYYY` → e.g. `mor_20260616`
- Afternoon → `after_DDMMYYYY` → e.g. `after_20260616`

Sheet tab name format: `mor_DD_MM_YYYY` or `after_DD_MM_YYYY` (with underscores between day/month/year).

---

## Step 1 — Run Generate-Report

```powershell
cd phases\02_curate
node generate-report.js {SESSION}
```

This script:
- Kills and relaunches Chrome using the saved user profile (auto-authenticated with Google)
- Navigates to the spreadsheet and clicks the matching tab
- Copies all rows (A1:J{lastRow}) via Ctrl+C
- Parses column I (`corp_url`) and column J (`poli_url`) — these hold TAKE-selected URLs
- Builds a markdown source file with two sections: **Corporate News** and **Political / Macro News**
- Saves to: `reports\{base}\source\{base}.md`

Warn the user before running: **Chrome will be killed and relaunched** — save any open Chrome work first.

---

## Step 2 — Verify Output

After the script exits, confirm the source file was created:

```
reports\{base}\source\{base}.md
```

Show the user a summary:
```
✓ Source file: reports\{base}\source\{base}.md
  Corporate articles: {N}
  Political/Macro articles: {M}
```

If the script logged a `⚠️ DROPPED` section (TAKE rows with no URL formula output), surface those titles — the user may want to check columns H/I/J in the sheet before proceeding.

If the file is empty or both sections have 0 articles, stop and ask the user to verify that TAKE was entered correctly in columns E or F of the sheet.

---

## Step 3 — Auto-chain to Summarize

Automatically invoke the `/summarize-news` skill, passing `{base}` as the session identifier.

---

## Notes

- The Google Sheets URL is: `https://docs.google.com/spreadsheets/d/1PPjukC3surCnTBPAjfotk_gSckeWQY24UJCWwFuEVtw/edit`
- Log is written to: `phases\02_curate\logs\upload.log`
- `generate-report.js` reads the **current state** of the sheet at run time — run it only after all TAKE marks are final
- **TAKE values** live in the session tab (e.g. `mor_16_06_2026`), columns E (`news_corp_select`) and F (`news_poli_select`). Only those rows end up in the source `.md`.
- **Macro tab + vin_bank tab** are read separately in `/summarize-news` step 2 via `read-macro-sheet.js`. Ensure the analyst has filled those tabs before invoking `/summarize-news`.
- Trading items are sourced from `hsx_insider_trading_*_extracted_formatted.json` — not from TAKE rows.
