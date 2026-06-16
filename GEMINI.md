# GEMINI.md

Repository guide for Gemini Code sessions. Follow exactly — all paths are verified against the current codebase.

---

## Directory Map

```
phases/
  01_scrape/          ← scraper scripts + venv (Python interpreter for ALL scripts)
    venv/Scripts/python.exe   ← ALWAYS use this Python
    main.py                   ← news scraper → CSV
    hsx_insider_scraper.py
    hsx_prepare_pdfs.py
    format_hsx_trading_news.py
  02_curate/          ← Node.js curate scripts (Sheets + Heyzine)
    upload-to-sheets.js
    generate-report.js
    read-macro-sheet.js
    run-upload.js
  03_summarize/       ← Python summarize + dedup scripts
    fetch_full_articles.py
    prepare_chunks.py
    combine_chunks.py
    harness.py
    dedup_engine.py
    deduplicate_reports.py
  04_publish/         ← report generators
    generate_html_report.py
    generate_pdf_report.py
    generate_docx_report.py
core_tools/
  paths/report_paths.py     ← Python path helpers (import, do not copy)
  paths/report-paths.js     ← Node path helpers
  validation/
    validate_summary_data.py
    benchmark_html_against_pdf.py
skills/                     ← skill definitions (read before acting)
  summarize_news.md
  dedup_news.md
  publish_news.md
reports/{base}/             ← ALL generated output lives here (root-level reports/)
  source/
  data/
  summaries/
  exports/html/
  exports/pdf/
  exports/docx/
  testing/playwright-images/
  testing/diffs/
```

**Never reference old paths**: `vietnam_news_scraper/`, `google-sheets-uploader/`, `scripts/`. Those directories no longer exist — they were reorganized into `phases/`.

---

## Pipeline Overview

```
01_scrape → 02_curate → (human marks TAKE) → 03_summarize → 04_publish
```

1. Scheduled run: `phases\01_scrape\run.bat` scrapes news → CSV.
2. `phases\02_curate\upload-to-sheets.js` uploads CSV to Google Sheets.
3. `phases\02_curate\generate-report.js` reads TAKE rows → `reports/{base}/source/{base}.md`.
4. Human marks `TAKE` rows and fills the Macro tab.
5. Agent runs `/summarize-news` → `/dedup-news` → `/publish-news` (skills auto-chain).

### Skills auto-chain

```
/summarize-news  →  summarizes articles → writes JSON/MD → invokes /dedup-news
/dedup-news      →  semantic dedup + HITL editing   → invokes /publish-news
/publish-news    →  validate → HTML/PDF/DOCX → Heyzine upload
```

**Always read the skill file before executing any step in it.**

---

## Report Base

Format: `{mor|after}_DD_MM_YYYY`  
Example: `mor_16_06_2026`, `after_16_06_2026`

Report root: `reports\{base}\`  
Data files: `reports\{base}\data\{base}_{macro|trading|corporate|economy_political_others}.json`

---

## Manual Commands (verified paths)

All commands run from the **project root** (`C:\Users\Administrator\Playwright-Daily-News`).  
Python interpreter: `phases\01_scrape\venv\Scripts\python.exe` — use this for every `.py` script.

### Phase 01 — Scrape

```powershell
# Run news scraper
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\main.py

# HSX insider trading (run in order)
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\hsx_insider_scraper.py
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\hsx_prepare_pdfs.py
# Agent reads rendered PDF images, produces _agent_results.json
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\format_hsx_trading_news.py
```

### Phase 02 — Curate (Sheets + Heyzine)

```powershell
# Upload CSV to Google Sheets
node phases\02_curate\upload-to-sheets.js morning
node phases\02_curate\upload-to-sheets.js afternoon

# Generate source .md from TAKE rows
node phases\02_curate\generate-report.js morning
node phases\02_curate\generate-report.js afternoon

# Read macro sheet (after human fills it)
node phases\02_curate\read-macro-sheet.js DD/MM/YYYY
```

### Phase 03 — Summarize

```powershell
# Fetch full article text
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\fetch_full_articles.py reports\{base}\source\{base}.md

# Split into chunks for agent summarization
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\prepare_chunks.py {base}

# Combine agent chunk outputs + macro + trading → 4 category JSONs
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\combine_chunks.py {base}

# Validate a specific JSON file (run after writing each)
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\harness.py reports\{base}\data\{filename}.json

# Semantic dedup check
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\dedup_engine.py reports\{base}\data --threshold 0.75

# Add kept items to dedup index
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\dedup_engine.py reports\{base}\data --add-to-index --report-id {base}

# Cross-report deduplication
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\deduplicate_reports.py {base}
```

### Phase 04 — Validate + Publish

```powershell
# Schema validation (must pass before report generation)
phases\01_scrape\venv\Scripts\python.exe core_tools\validation\validate_summary_data.py {base}

# Generate reports (run in order)
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_html_report.py {base}
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_pdf_report.py {base}
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_docx_report.py {base}

# Visual benchmark (HTML vs PDF comparison)
phases\01_scrape\venv\Scripts\python.exe core_tools\validation\benchmark_html_against_pdf.py --html reports\{base}\exports\html\{base}_report_vn.html reports\{base}\exports\html\{base}_report_en.html

# Upload to Heyzine (EN first, then VN)
node phases\02_curate\run-upload.js "reports\{base}\exports\pdf\{base}_report_en.pdf"
node phases\02_curate\run-upload.js "reports\{base}\exports\pdf\{base}_report_vn.pdf"
```

---

## HSX Insider Trading

Core files (all under `phases/01_scrape/`):

- `hsx_insider_scraper.py` — fetches HSX disclosure items, filters insider-trading, finds PDFs, writes raw scrape JSON.
- `hsx_prepare_pdfs.py` — downloads PDFs, renders to images for agent extraction.
- `format_hsx_trading_news.py` — formats extracted trading news (agent-driven LLM translation).

Extraction contract:

- Capture: issuer ticker/name, insider name, insider role/relationship, transaction type, registered volume, executed volume, ownership before/after, transaction dates, disclosure dates, source news ID, source PDF URL/path.
- Classify only relevant insider-trading items. Do not merge bond disclosures, governance resolutions, or general corporate actions.
- Prefer explicit PDF table values. If a field is absent, leave it empty/null — do not fabricate.
- Keep insider identity separate from issuer identity.
- Preserve traceability: final report item → scrape JSON → extracted JSON → PDF attachment.
- For scanned PDFs: check for a text layer before assuming OCR is required.

---

## Working Rules

- Always use `phases\01_scrape\venv\Scripts\python.exe` — never `python`, `py`, or another venv.
- Route new output-producing code through the shared path helpers (`core_tools/paths/report_paths.py` / `report-paths.js`).
- All report artifacts belong in `reports/{base}/` — never write them to project root, `phases/`, or any other location.
- Keep `news_html_template/` for templates and static assets only.
- Keep `phases\02_curate\logs\` for small text logs only.
- Put temporary browser/debug artifacts in `reports/{base}/testing/` or an OS temp directory.
- Prefer overwriting stale files inside a run-specific testing folder over creating timestamped clutter.
- Use `127.0.0.1` for Chrome CDP connections; `localhost` may resolve to IPv6.
- Put HSX insider runtime JSON, downloaded PDFs, and debug artifacts under `reports/{base}/testing/` or `phases/01_scrape/pdfs/`.

Chrome automation pattern:

- Scripts connect to Chrome over CDP on port `9222`.
- If Chrome is stuck: close Chrome, clear profile singleton lock files (`SingletonLock`, `SingletonCookie`, `SingletonSocket`), then reconnect with `chromium.connectOverCDP('http://127.0.0.1:9222')`.

---

## Tool Schema Guidelines (prevents infinite retry loops)

- **Integer Parameters**: When calling tools like `view_file` (`ContentOffset` argument), always pass as a raw **integer** (e.g. `51200`), NEVER as a string (`"51200"`). Schema validation will fail on strings, causing agents to loop.
- **Subagent Prompts**: If spawning a subagent that reads files, explicitly instruct it in the system prompt to pass `ContentOffset` as an integer.

---

## Karpathy Reasoning Guidelines

- Think before coding: state the expected input shape, inspect evidence, then change the smallest useful piece.
- Do not assume PDF layouts. Check representative PDFs, text layers, OCR output, or extracted JSON before changing parser behavior.
- Prefer simple, direct implementations using existing helpers and standard Python.
- Keep changes surgical — preserve existing style, file layout, imports, and output conventions.
- Define concrete success criteria before changing parsers.
- If requirements are vague or document layouts are ambiguous, pause and clarify instead of guessing.
- Use diacritic-robust matching for Vietnamese classification and joins. Preserve final Vietnamese text with NFC normalization.
- Vietnamese `đ` and `Đ` must be replaced with `d` and `D` **before** NFD decomposition. Always use NFC for output Vietnamese text — never NFKC/NFKD.

---

## Tool Schema Guidelines

- **Integer Parameters**: When calling tools with integer arguments (e.g. `ContentOffset`), always pass a raw integer (`51200`), never a string (`"51200"`). Schema validation fails on strings and causes agents to loop.
- **Subagent Prompts**: When spawning subagents that read files, explicitly instruct them to pass integer arguments as integers.

---

## Google Sheets

Session tabs use `mor_DD_MM_YYYY` or `after_DD_MM_YYYY`. The UI is Vietnamese.

- Add Sheet button: `[aria-label="Thêm trang tính"]`
- Active tab: `.docs-sheet-active-tab`
- Tab names: `.docs-sheet-tab-name`
- Name box: `.waffle-name-box`; use `{ force: true }` when a modal overlay intercepts pointer events.
