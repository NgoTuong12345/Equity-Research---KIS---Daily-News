# KIS Vietnam Daily News Report

This repository powers the automated daily news reporting pipeline for KIS Vietnam Securities Corporation. It orchestrates scraping news from Vietnamese financial sources, extracting data from scanned insider trading PDFs using multimodal AI agents, enabling human editorial curation via Google Sheets, and compiling selected stories into print-ready, fixed-layout daily bulletins (HTML, PDF, and DOCX).

## Overview

The system combines automated scrapers, multimodal AI agents, and editorial curation:
1. **Scrape**: News articles and HSX disclosure PDFs are scraped automatically via scheduled runners or manual commands.
2. **Extract**: Multimodal AI agents inspect rendered PDF page images to extract structured insider trading transactions without local OCR.
3. **Curate**: Scraped news is uploaded to a Google Sheets session tab where analysts mark stories with `TAKE` and complete the daily Macro summary.
4. **Summarize & Dedup**: Full articles are retrieved, summarized following KIS writing standards, and deduplicated against a 30-day index and cross-report coverage.
5. **Publish**: The system renders standardized branded A4 layouts and compiles HTML, print-quality PDF, and Word DOCX reports, with automatic Heyzine flipbook upload.

## System Architecture

```
phases/
  01_scrape/          ← news scraper + HSX insider trading pipeline
  02_curate/          ← Google Sheets curation + Heyzine upload
  03_summarize/       ← LLM summarization + 30-day semantic dedup
  04_publish/         ← HTML / PDF / DOCX report generators
orchestration/        ← automated batch scripts & Windows Task Scheduler
core_tools/           ← shared path helpers, templates, & validation scripts
.agents/              ← Antigravity (AGY) rules & registered skills
skills/               ← skill specification documents
reports/{base}/       ← all generated report artifacts (gitignored)
```

### Phase 01 — Scrape (`phases/01_scrape/`)
- **`main.py`**: Aggregates news from RSS feeds, financial portals, and FireAnt API → CSV.
- **`hsx_insider_scraper.py`**: Fetches HSX corporate disclosures and links to announcement PDFs.
- **`hsx_prepare_pdfs.py`**: Downloads PDFs and renders each page to PNG for agent inspection.
- **`format_hsx_trading_news.py`**: Orchestrates LLM translation and structured formatting of insider records (`--prepare`, Agent LLM, `--merge`).

### Phase 02 — Curate (`phases/02_curate/`)
- **`upload-to-sheets.js`**: Uploads scraped CSV data to Google Sheets (guarded by upload idempotency sentinels).
- **`generate-report.js`**: Pulls human `TAKE` selections from Sheets → `reports/{base}/source/{base}.md`.
- **`read-macro-sheet.js`**: Reads `Macro` and `vin_bank` tabs with dynamic commodity title generation.
- **`run-upload.js`**: Uploads generated PDF reports to the Heyzine flipbook platform.

### Phase 03 — Summarize (`phases/03_summarize/`)
- **`fetch_full_articles.py`**: Retrieves complete article text for selected stories.
- **`prepare_chunks.py`** / **`combine_chunks.py`**: Splits, processes, and combines summaries into 4 category JSON files with cross-report deduplication.
- **`harness.py`**: Validates category JSON schemas, editorial word count limits, and KIS house style rules.
- **Agentic Deduplication (`/dedup-news`)**: Intra-session and cross-session entity & semantic deduplication with human-in-the-loop review.

### Phase 04 — Publish (`phases/04_publish/`)
- **`generate_html_report_standard.py`**: Canonical production A4 HTML generator with Segoe UI Black diacritics support, branded coversheet, and standardized outro back cover.
- **`generate_pdf_report.py`**: Compiles pixel-perfect A4 PDF reports via headless Playwright.
- **`generate_docx_report.py`**: Generates Microsoft Word (.docx) bulletins.
- **`coversheet.py`**: Front-page coversheet metadata and layout configuration.

## Registered Antigravity (AGY) Skills

The pipeline features 8 specialized agent skills registered in `.agents/skills/`:
- `/scrape-and-upload`: Run news scraper, HSX insider pipeline, and upload CSV to Sheets.
- `/curate-news`: Read human TAKE selections from Sheets into markdown source.
- `/summarize-news`: Summarize TAKE articles & compile Macro/VinBank/HSX into 4 JSON categories.
- `/dedup-news`: Perform agentic deduplication (intra-session & cross-session) and review.
- `/publish-news`: Validate schemas, generate HTML/PDF/DOCX, and upload flipbooks to Heyzine.
- `/paste-news`: Process ad-hoc pasted text directly into news reports.
- `/delta-summarize`: Summarize newly added TAKE rows without re-processing existing articles.
- `/kis-writing-style`: KIS Vietnam financial writing style and translation guidelines.

## Output & Design Standards

- **A4 Fixed Layout**: Reports use strict A4 canvas dimensions (`210mm × 297mm`) designed for print and digital flipbooks.
- **Editorial Typography**: Cover titles use `'Segoe UI Black', 'Segoe UI', Arial, sans-serif` (`font-weight: 900;`) to ensure full glyph support for uppercase Vietnamese diacritics (`Ả`, `Ổ`, `Ề`, `Ứ`, `Á`).
- **Regression Guard**: `core_tools/validation/benchmark_html_against_pdf.py` prevents layout shifting and footer overlaps.

## Setup

### Prerequisites
- Python 3.11+ (use `phases/01_scrape/venv/Scripts/python.exe` for all `.py` scripts)
- Node.js 18+
- Google Chrome (for Playwright CDP automation)

### Environment Variables
Copy `.env.example` to `.env` and configure required credentials:
```powershell
copy .env.example .env
```

### Node Dependencies
```powershell
npm install
cd phases\02_curate && npm install
```

## Usage

### Scheduled Automation
Automated pipeline runners are available under `orchestration/`:
- `orchestration\run_morning.bat`: Morning scrape, HSX extraction, and Sheets upload.
- `orchestration\run_afternoon.bat`: Afternoon scrape, HSX extraction, and Sheets upload.
- `orchestration\install_tasks.bat`: Installs automated Windows Task Scheduler jobs.

### Daily Editorial Workflow

```powershell
# Phase 01 — Scrape & Prepare
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\main.py
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\hsx_insider_scraper.py
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\hsx_prepare_pdfs.py
# Multimodal agent inspects rendered PNGs & translates trading records
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\format_hsx_trading_news.py --prepare <file>
# (Agent translation step)
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\format_hsx_trading_news.py --merge <file>

# Phase 02 — Upload to Sheets (morning or afternoon)
node phases\02_curate\upload-to-sheets.js morning

# [Human] Mark TAKE rows in Google Sheets & fill Macro tab (morning)

# Phase 02 — Generate Source Markdown from TAKE rows
node phases\02_curate\generate-report.js morning

# Phase 03–04 — Summarize and Publish via Agent Skills
# Run in Antigravity chat:
#   /summarize-news  →  /dedup-news  →  /publish-news
```

### Manual Phase 03–04 Commands

```powershell
# Summarize & Combine
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\fetch_full_articles.py reports\{base}\source\{base}.md
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\prepare_chunks.py {base}
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\combine_chunks.py {base}

# Validate & Publish
phases\01_scrape\venv\Scripts\python.exe core_tools\validation\validate_summary_data.py {base}
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_html_report_standard.py {base}
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_pdf_report.py {base}
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_docx_report.py {base}

# Upload to Heyzine
node phases\02_curate\run-upload.js "reports\{base}\exports\pdf\{base}_report_en.pdf"
node phases\02_curate\run-upload.js "reports\{base}\exports\pdf\{base}_report_vn.pdf"
```

## Development & Guidelines

- For system architecture, data models, and component workflows, refer to [ARCHITECTURE.md](file:///W:/KIS-DAILY-NEWS/ARCHITECTURE.md).
- For complete agent rules, manual commands, and workflow contracts, refer to [AGENTS.md](file:///W:/KIS-DAILY-NEWS/AGENTS.md).
- For UI layout rules, CSS styling, and typography specifications, refer to [DESIGN.md](file:///W:/KIS-DAILY-NEWS/DESIGN.md).
