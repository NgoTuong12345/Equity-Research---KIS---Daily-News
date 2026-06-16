# KIS Vietnam Daily News Report

This repository powers the automated daily news reporting pipeline for KIS Vietnam Securities Corporation. It orchestrates scraping news from Vietnamese financial sources, extracting data from scanned insider trading PDFs using AI agents, allowing human editorial review via Google Sheets, and compiling the selected content into a print-ready, fixed-layout daily bulletin.

## Overview

The system replaces manual editorial aggregation with a semi-automated pipeline:
1. **Scrape**: News articles and HSX disclosure PDFs are scraped automatically.
2. **Extract**: AI agents read raw PDF images to extract structured insider trading data.
3. **Curate**: Extracted news is uploaded to a Google Sheet where a human editor marks stories to "TAKE" and writes the daily Macro summary.
4. **Publish**: The system fetches full text for selected articles, summarizes them, generates standardized titles, and compiles everything into final HTML, PDF, and DOCX reports.

## System Architecture

```
phases/
  01_scrape/          ← news scraper + HSX insider trading pipeline
  02_curate/          ← Google Sheets upload + report generation
  03_summarize/       ← LLM summarization + semantic dedup
  04_publish/         ← HTML / PDF / DOCX report generation
core_tools/           ← shared path helpers + validation scripts
skills/               ← agent skill definitions
reports/{base}/       ← all generated output (gitignored)
```

### Phase 01 — Scrape (`phases/01_scrape/`)
- **`main.py`**: Aggregates news from RSS feeds and Vietnamese financial portals → CSV.
- **`hsx_insider_scraper.py`**: Fetches HSX disclosure items, filters for insider trading, saves raw JSON.
- **`hsx_prepare_pdfs.py`**: Downloads PDFs and renders each page to PNG for agent extraction.
- **`format_hsx_trading_news.py`**: LLM-driven formatter that translates and structures extracted trading records.

### Phase 02 — Curate (`phases/02_curate/`)
- **`upload-to-sheets.js`**: Pushes scraped CSV data to a new Google Sheets session tab.
- **`generate-report.js`**: Reads TAKE-marked rows from Sheets → `reports/{base}/source/{base}.md`.
- **`read-macro-sheet.js`**: Reads the Macro tab after human fills it.
- **`run-upload.js`**: Uploads final PDF reports to Heyzine flipbook platform.

### Phase 03 — Summarize (`phases/03_summarize/`)
- **`fetch_full_articles.py`**: Fetches full article text for TAKE items.
- **`prepare_chunks.py`** / **`combine_chunks.py`**: Splits and merges article chunks for LLM summarization.
- **`harness.py`**: Validates per-article summary JSON.
- **`dedup_engine.py`** / **`deduplicate_reports.py`**: Semantic deduplication across and within reports.

### Phase 04 — Publish (`phases/04_publish/`)
- **`generate_html_report.py`** / **`generate_pdf_report.py`** / **`generate_docx_report.py`**: Assembles final A4-fixed-layout reports in all three formats.

## Output and Design Requirements

- **A4 Fixed Layout**: Reports are fixed A4 pages (`210mm × 297mm`), not responsive web pages.
- **Editorial Typography**: Adheres to KIS Vietnam brand guidelines in `DESIGN.md`.
- **Regression Guard**: `core_tools/validation/benchmark_html_against_pdf.py` prevents footer overlap regressions.

## Setup

### Prerequisites
- Python 3.11+ (use `phases/01_scrape/venv/Scripts/python.exe` for all `.py` scripts)
- Node.js 18+
- Google Chrome (for Playwright CDP automation)

### Environment Variables
Copy `.env.example` to `.env` and fill in the required values:
```powershell
copy .env.example .env
```

### Node Dependencies
```powershell
npm install
cd phases\02_curate && npm install
```

## Usage

### Daily Pipeline

```powershell
# Phase 01 — Scrape
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\main.py
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\hsx_insider_scraper.py
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\hsx_prepare_pdfs.py
# Agent reads rendered PDF images → _agent_results.json
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\format_hsx_trading_news.py

# Phase 02 — Upload to Sheets (morning or afternoon)
node phases\02_curate\upload-to-sheets.js morning

# [Human] Mark TAKE rows and fill Macro tab in Google Sheets

# Phase 02 — Generate source markdown from TAKE rows
node phases\02_curate\generate-report.js morning

# Phase 03–04 — Summarize and publish (via agent skills)
# Run /summarize-news → /dedup-news → /publish-news in Claude Code
```

### Manual Phase 03–04 Commands

```powershell
# Summarize
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\fetch_full_articles.py reports\{base}\source\{base}.md
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\prepare_chunks.py {base}
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\combine_chunks.py {base}

# Validate + Publish
phases\01_scrape\venv\Scripts\python.exe core_tools\validation\validate_summary_data.py {base}
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_html_report.py {base}
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_pdf_report.py {base}
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_docx_report.py {base}

# Upload to Heyzine
node phases\02_curate\run-upload.js "reports\{base}\exports\pdf\{base}_report_en.pdf"
node phases\02_curate\run-upload.js "reports\{base}\exports\pdf\{base}_report_vn.pdf"
```

## Development

For detailed agent guidelines and verified command paths, refer to `GEMINI.md`.  
For UI layout constraints and CSS configuration, refer to `DESIGN.md`.
