# CLAUDE.md

Repository guide for Claude Code sessions. Keep this file short; put repeatable rules in scripts.

## Pipeline

1. Scheduled jobs run `run-morning.bat` or `run-afternoon.bat`.
2. `vietnam_news_scraper/` collects news and writes scraper outputs, including HSX insider trading disclosures.
3. `google-sheets-uploader/upload-to-sheets.js` creates the Google Sheets session tab.
4. A human marks `TAKE` rows and updates the Macro tab.
5. `/summarize morning` or `/summarize afternoon` generates source markdown, fetched full articles, summary JSON, bilingual summaries, and final HTML/PDF/DOCX reports.

## HSX Insider Trading

The imported HNX/HSX insider-trading work is part of the main `vietnam_news_scraper/` workflow. Do not create a second project-local agent guide; keep this root `CLAUDE.md` as the only Claude instruction file.

Core files:

- `vietnam_news_scraper/hsx_insider_scraper.py`: fetches HSX disclosure/news items, filters insider-trading announcements, finds PDF attachments, and writes raw scrape JSON.
- `vietnam_news_scraper/hsx_nlm_extractor.py`: downloads PDFs and extracts structured insider/related-party transaction records with NotebookLM.
- `vietnam_news_scraper/format_hsx_trading_news.py`: formats extracted transaction JSON into bilingual trading-news prose.

Extraction contract:

- Capture issuer ticker/name, insider name, insider role or relationship, transaction type, registered volume, executed volume when present, ownership before/after, transaction dates, disclosure dates, source news ID, source PDF URL/path, and notes for partial or failed transactions.
- Classify only relevant disclosure/news items as insider trading. Do not merge unrelated bond disclosures, governance resolutions, or general corporate actions into insider records.
- Prefer explicit PDF table values over inferred values. If a field is absent, keep it empty/null rather than fabricating it.
- Keep insider identity separate from issuer identity; do not collapse names, roles, ticker, and company names into a single blob.
- Preserve traceability from final report item back to scrape JSON, extracted JSON, and PDF attachment.
- For scanned PDFs, check whether a text layer exists before assuming OCR is required. Validate OCR-heavy changes against representative extracted text or visual samples.

## Output Layout

Use shared path helpers for generated files:

- Python: `scripts/report_paths.py`
- Node: `google-sheets-uploader/report-paths.js`

Report artifacts belong under `reports/{base}/`, where `{base}` is `mor_DD_MM_YYYY` or `after_DD_MM_YYYY`.

```text
reports/{base}/
  source/
  data/
  summaries/
  exports/html/
  exports/pdf/
  exports/docx/
  testing/playwright-images/
  testing/diffs/
```

Do not write new generated reports, screenshots, summary files, data files, or visual diff files into the project root, `reports/`, `news_html_template/`, or `google-sheets-uploader/logs/`.

## Manual Commands

```powershell
.\run-morning.bat
.\run-afternoon.bat

cd google-sheets-uploader
node upload-to-sheets.js morning
node upload-to-sheets.js afternoon
node generate-report.js morning

cd ..
python fetch_full_articles.py reports/{base}/source/{base}.md

cd google-sheets-uploader
node read-macro-sheet.js DD/MM/YYYY

cd ..
python scripts/validate_summary_data.py {base}
python scripts/generate_html_report.py {base}
python scripts/generate_pdf_report.py {base}
python scripts/generate_docx_report.py {base}
python scripts/benchmark_html_against_pdf.py --html reports/{base}/exports/html/{base}_report_vn.html reports/{base}/exports/html/{base}_report_en.html
```

Scheduled Windows tasks:

- `VietnamNews-Morning`: daily morning run, calls `run-morning.bat`.
- `VietnamNews-Afternoon`: daily afternoon run, calls `run-afternoon.bat`.

## Working Rules

- Route new output-producing code through the shared path helpers.
- Keep `news_html_template/` for templates and static assets only.
- Keep `google-sheets-uploader/logs/` for small text logs only.
- Put temporary browser/debug artifacts in `reports/{base}/testing/` or an OS temp directory.
- Prefer overwriting stale files inside a run-specific testing folder over creating timestamped clutter.
- Use `127.0.0.1` for Chrome CDP connections; `localhost` may resolve to IPv6.
- Put HSX insider runtime JSON, downloaded PDFs, extraction text, and debug browser artifacts under a run-specific report/testing folder or `vietnam_news_scraper/pdfs/`; do not re-import `HNX_insider_trading-20260605T020139Z-3-001/` as a parallel project.

Chrome automation pattern:

- Existing scripts connect to the user's Chrome profile over CDP on port `9222`.
- If Chrome is stuck, close Chrome, clear profile singleton lock files, then reconnect with `chromium.connectOverCDP('http://127.0.0.1:9222')`.
- Keep generated logs in `google-sheets-uploader/logs/`; keep report artifacts under `reports/{base}/`.

## Karpathy Reasoning Guidelines

- Think before coding: state the expected input shape, inspect evidence, then change the smallest useful piece.
- Do not assume PDF layouts. Check representative PDFs, text layers, OCR output, extracted JSON, or current scraper output before changing parser behavior.
- Prefer simple, direct implementations using existing helpers, standard Python, and clear data transformations before adding dependencies.
- Keep changes surgical. Preserve existing style, file layout, imports, and output conventions unless the task requires otherwise.
- Define concrete success criteria for parser changes, such as all transactions in a sample PDF being captured with correct dates and volumes.
- If requirements are vague or document layouts are ambiguous, pause and clarify instead of encoding guesses.
- Use diacritic-robust matching for Vietnamese classification and joins. Preserve final Vietnamese text with NFC normalization.

## Google Sheets

Session tabs use `mor_DD_MM_YYYY` or `after_DD_MM_YYYY`. The UI is Vietnamese.

- Add Sheet button: `[aria-label="Thêm trang tính"]`
- Active tab: `.docs-sheet-active-tab`
- Tab names: `.docs-sheet-tab-name`
- Name box: `.waffle-name-box`; use `{ force: true }` when a modal overlay intercepts pointer events.
