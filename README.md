# KIS Vietnam Daily News Report

This repository powers the automated daily news reporting pipeline for KIS Vietnam Securities Corporation. It orchestrates scraping news from Vietnamese financial sources, extracting data from scanned insider trading PDFs using AI agents, allowing human editorial review via Google Sheets, and compiling the selected content into a print-ready, fixed-layout daily bulletin.

## Overview

The system replaces manual editorial aggregation with a semi-automated pipeline:
1. **Scrape**: News articles and HSX/HNX disclosure PDFs are scraped automatically.
2. **Extract**: AI agents (and occasionally NotebookLM) read raw PDF images to extract structured insider trading data.
3. **Curate**: Extracted news is uploaded to a Google Sheet where a human editor marks stories to "TAKE" and writes the daily Macro summary.
4. **Publish**: The system fetches full text for the selected articles, summarizes them, generates standardized titles, and compiles everything into final HTML, PDF, and DOCX reports.

## System Architecture

The repository is organized into distinct sub-modules to handle different phases of the pipeline:

### 1. Web Scraper (`vietnam_news_scraper/`)
- Scrapes financial news sites and state exchange portals (HSX/HNX).
- **`hsx_insider_scraper.py`**: Monitors and downloads HSX disclosure PDFs specifically filtering for insider trading.
- **`hsx_prepare_pdfs.py` & `hsx_agent_extractor.py`**: Converts scanned PDFs into images and uses LLMs/Agents to robustly extract structured trading records (e.g., ticker, insider name, relationship, transaction volume, dates).

### 2. Google Sheets Uploader (`google-sheets-uploader/`)
- Connects to Google Sheets via Playwright/Puppeteer (CDP connection to an active Chrome profile).
- Pushes the morning or afternoon news scrapes into a newly created session tab (e.g., `mor_DD_MM_YYYY`).
- Allows human editors to visually review items, check "TAKE" boxes, and draft macroeconomic notes in the "Macro" tab.

### 3. Report Generation and Summarization (`scripts/`)
- Once curation is complete, `python fetch_full_articles.py` fetches the complete article content for stories marked "TAKE".
- Agent workflows summarize the text, standardizing language and deduplicating overlapping stories.
- **`generate_html_report.py` / `generate_pdf_report.py`**: Assembles the content into the final output format.

## Output and Design Requirements

The resulting HTML/PDF artifacts are strictly designed to match the legacy **KIS Vietnam PDF bulletin format**. 

- **A4 Fixed Layout**: The reports are fixed A4 pages (`210mm x 297mm`). This is not a responsive web app.
- **Editorial Typography**: Adheres strictly to the brand guidelines specified in `DESIGN.md` (brown primary text, exact font sizes, spacing, and strict overflow/pagination checks to avoid collisions with footers).
- **Testing**: A benchmark script (`benchmark_html_against_pdf.py`) strictly guards against visual regressions (such as content overlapping the footer logo).

## Usage & Automation

The pipeline is generally executed via Windows Scheduled Tasks using batch scripts:

- **`run-morning.bat`**: Triggers the morning run (scraper -> HSX pipeline -> Sheets upload).
- **`run-afternoon.bat`**: Triggers the afternoon run.

### Manual Pipeline Steps

If running manually or handling the summarization phase:

1. **Scrape & Upload**:
   ```powershell
   .\run-morning.bat
   ```
2. **Human Curation**: 
   - Editor goes to Google Sheets, reviews the new tab, checks the "TAKE" column for desired articles, and updates the Macro tab.
3. **Fetch & Summarize**: 
   - Uses the agent summarizer command (e.g., `/summarize morning` in Gemini Code, or manually running the Python extraction/fetch scripts).
4. **Compile Reports**:
   ```powershell
   # Example generation of final reports
   python scripts/generate_html_report.py mor_16_06_2026
   python scripts/generate_pdf_report.py mor_16_06_2026
   ```

## Development

For detailed agent guidelines and manual component execution steps, refer to `GEMINI.md`.
For UI layout constraints and CSS configurations, refer strictly to `DESIGN.md`.
