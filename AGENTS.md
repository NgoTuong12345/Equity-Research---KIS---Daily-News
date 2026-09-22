# AGENTS.md

Repository guide for Antigravity (AGY) sessions in KIS-DAILY-NEWS. Follow exactly — all paths are verified against the current codebase.
For deep-dive architectural diagrams, data flows, and component models, refer to [ARCHITECTURE.md](file:///W:/KIS-DAILY-NEWS/ARCHITECTURE.md) and [DESIGN.md](file:///W:/KIS-DAILY-NEWS/DESIGN.md).

---

## Directory Map

```
phases/
  01_scrape/          ← scraper scripts + venv (Python interpreter for ALL scripts)
    venv/Scripts/python.exe   ← ALWAYS use this Python interpreter
    main.py                   ← news scraper → CSV (output: vietnam_financial_news_combined_*.csv)
    hsx_insider_scraper.py    ← fetches HSX disclosure items & PDF links
    hsx_prepare_pdfs.py       ← downloads PDFs & renders pages to PNG
    format_hsx_trading_news.py← LLM translation orchestrator (--prepare / agent / --merge)
    extract_hsx_from_manifest.py ← extracts HSX data from manifest JSON
    format_agent_helper.py    ← helper for agent formatting
    pdf_images/               ← rendered PDF page images for vision extraction
    pdfs/                     ← downloaded HSX PDF attachments
    run.bat / run.sh          ← scrape-only runner (batch + shell)
  02_curate/          ← Node.js curate scripts (Sheets + Heyzine)
    upload-to-sheets.js       ← uploads scraped CSV to Google Sheets session tab
    generate-report.js        ← reads human TAKE rows → reports/{base}/source/{base}.md
    read-macro-sheet.js       ← reads Macro + vin_bank tabs (morning session)
    run-upload.js             ← uploads final PDFs to Heyzine flipbooks
    logs/                     ← sentinel files & upload logs
  03_summarize/       ← Python summarize & editorial validation scripts
    fetch_full_articles.py    ← fetches full article text from URLs
    prepare_chunks.py         ← chunks articles for LLM summarization
    combine_chunks.py         ← merges chunk summaries + macro + HSX trading into 4 JSONs
    harness.py                ← validates editorial constraints & KIS writing style
    run_summarize_pipeline.py ← pipeline orchestrator for summarization
    generate_all_summaries.py ← batch summary generator
    (Deterministic dedup scripts & index archived to archive/deprecated_dedup/ — superseded by agentic /dedup-news)
  04_publish/         ← report generators
    generate_html_report_standard.py ← CANONICAL production A4 HTML generator
    generate_html_report.py   ← baseline/legacy HTML generator
    generate_pdf_report.py    ← converts HTML to print A4 PDF via Playwright
    generate_docx_report.py   ← compiles Word .docx report
    coversheet.py             ← coversheet layout and metadata configuration
orchestration/        ← automated runner scripts & Windows Task Scheduler
  run_morning.bat             ← automated morning pipeline runner
  run_afternoon.bat           ← automated afternoon pipeline runner
  install_tasks.bat           ← installs Windows scheduled tasks
core_tools/           ← shared path helpers, templates & validation
  paths/report_paths.py       ← Python path helpers (import, do not copy)
  paths/report-paths.js       ← Node path helpers
  paths/project_root.py       ← project root resolver
  templates/                  ← static assets (company-logo.jpg, image_library/)
  validation/
    validate_summary_data.py  ← schema validation before publish
    benchmark_html_against_pdf.py ← visual benchmark (HTML vs PDF layout)
llm_brain/            ← LLM prompts & extraction rules
  extractors/                 ← extraction logic
  prompts_and_rules/          ← prompt templates & rules
docs/                 ← pipeline visualization (pipeline.mmd / .svg / .html)
tests/                ← test suite (coversheet, imports, contracts, tickers)
archive/              ← archived & cleaned-up files
.agents/              ← Antigravity configuration
  hooks.json                  ← lifecycle hooks config (Opus 4.6 Thinking + Gemini 3.8 Flash)
  hooks/                      ← lifecycle hook scripts (orchestrator_subagent_hook.py)
  rules/                      ← persistent agent rules
  skills/                     ← 8 registered AGY skills
skills/               ← markdown reference skill definitions (mirrors .agents/skills/)
reports/{base}/       ← ALL generated output lives here (root-level reports/)
  source/                     ← raw curated markdown source
  data/                       ← 4 category JSONs + macro data
  summaries/                  ← chunked & intermediate summaries
  exports/html/               ← final HTML reports (VN / EN)
  exports/pdf/                ← final PDF reports (VN / EN)
  exports/docx/               ← final DOCX reports (VN / EN)
  testing/                    ← temporary test & debug artifacts
tmp/                  ← organized temporary/scratch files & debug dumps (never clutter project root)
ticker_index.json     ← master ticker lookup index (~693KB, used by scripts)
```

**Never reference old paths**: `vietnam_news_scraper/`, `google-sheets-uploader/`, `scripts/`. Those directories no longer exist — they were reorganized into `phases/`.

---

## Pipeline Overview

```
01_scrape → 02_curate → (human marks TAKE) → 03_summarize → 04_publish
```

1. **Scheduled run**: `phases\01_scrape\run.bat` (or `orchestration\run_morning.bat` / `run_afternoon.bat`) scrapes news → CSV.
2. `phases\02_curate\upload-to-sheets.js` uploads CSV to Google Sheets.
3. Human marks `TAKE` rows in the session tab AND fills the `Macro` + `vin_bank` tabs.
4. `phases\02_curate\generate-report.js` reads TAKE rows → `reports/{base}/source/{base}.md`.
5. `phases\02_curate\read-macro-sheet.js DD/MM/YYYY` reads `Macro` + `vin_bank` tabs → `reports/{base}/data/macro_sheet_DD_MM_YYYY.json` (morning only).
6. Agent executes skills auto-chain: `/summarize-news` → `/dedup-news` → `/publish-news`.

### ⛔ Upload Idempotency — NEVER re-upload if today's session already ran

Before running `upload-to-sheets.js` for any session, check for the sentinel file:

```
phases\02_curate\logs\morning_{YYYYMMDD}.done    ← morning session
phases\02_curate\logs\afternoon_{YYYYMMDD}.done  ← afternoon session
```

**If the sentinel exists → stop. Do not run the upload.**

Re-running `upload-to-sheets.js` when the sheet tab already exists will clear it and paste fresh CSV data, destroying all `TAKE` values the analyst has already marked. The sentinel is written by the batch runners and by `/scrape-and-upload` after a successful upload. To force a legitimate re-run, the user must manually delete the sentinel file first.

### Registered AGY Skills

The following 8 skills are registered for Antigravity sessions:
- `/scrape-and-upload`: Run news scraper, HSX insider trading pipeline, and upload CSV to Google Sheets.
- `/curate-news`: Read human TAKE rows from Google Sheets into markdown source report.
- `/summarize-news`: Summarize TAKE articles & process Macro/VinBank/HSX into 4 JSON categories.
- `/dedup-news`: Perform agentic deduplication (intra-session & cross-session) with HITL review.
- `/publish-news`: Schema validation, generate HTML/PDF/DOCX, and upload to Heyzine.
- `/paste-news`: Process ad-hoc pasted text directly into news reports.
- `/delta-summarize`: Summarize newly added TAKE rows without re-processing existing articles.
- `/kis-writing-style`: KIS Vietnam financial writing style, terminology, and translation reference.

### Skills Auto-Chain

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

## Manual Commands (Verified Paths)

All commands run from the **project root** (`W:\KIS-DAILY-NEWS` or active workspace root).  
Python interpreter: `phases\01_scrape\venv\Scripts\python.exe` — use this for every `.py` script.

### Phase 01 — Scrape & HSX Extraction

```powershell
# 1. Run news scraper (RSS + financial portals + FireAnt API)
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\main.py

# 2. HSX insider trading workflow:
# Step A: Scrape disclosure items and find PDFs
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\hsx_insider_scraper.py

# Step B: Download PDFs and render pages to PNG images
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\hsx_prepare_pdfs.py

# Step C: Prepare records for LLM translation
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\format_hsx_trading_news.py --prepare phases\01_scrape\hsx_insider_trading_DD_MM_YYYY_extracted.json

# Step D: Multimodal agent reads rendered PNG images, translates fields, and produces *_agent_formatted.json

# Step E: Merge agent formatting into final trading JSON
phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\format_hsx_trading_news.py --merge phases\01_scrape\hsx_insider_trading_DD_MM_YYYY_extracted.json
```

### Phase 02 — Curate (Sheets + Heyzine)

```powershell
# Upload CSV to Google Sheets
node phases\02_curate\upload-to-sheets.js morning
node phases\02_curate\upload-to-sheets.js afternoon

# Generate source .md from TAKE rows
node phases\02_curate\generate-report.js morning
node phases\02_curate\generate-report.js afternoon

# Read macro sheet (after human fills it; morning session only)
node phases\02_curate\read-macro-sheet.js DD/MM/YYYY
```

### Phase 03 — Summarize & Dedup

```powershell
# Fetch full article text
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\fetch_full_articles.py reports\{base}\source\{base}.md

# Split into chunks for agent summarization
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\prepare_chunks.py {base}

# Combine agent chunk outputs + macro + trading → 4 category JSONs
# (Includes automatic morning-to-afternoon corporate ticker deduplication)
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\combine_chunks.py {base}

# Validate a specific JSON file (run after writing each)
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\harness.py reports\{base}\data\{filename}.json

# Deduplication & HITL Review:
# Handled agentically in /dedup-news (pure LLM reasoning context; no external vector index)
```

### Phase 04 — Validate + Publish

```powershell
# 1. Schema validation (must pass before report generation)
phases\01_scrape\venv\Scripts\python.exe core_tools\validation\validate_summary_data.py {base}

# 2. Generate production HTML reports (Canonical standard script)
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_html_report_standard.py {base}

# 3. Generate PDF reports via Playwright
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_pdf_report.py {base}

# 4. Generate DOCX reports
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_docx_report.py {base}

# 5. Visual benchmark (HTML vs PDF comparison)
phases\01_scrape\venv\Scripts\python.exe core_tools\validation\benchmark_html_against_pdf.py --html reports\{base}\exports\html\{base}_report_vn.html reports\{base}\exports\html\{base}_report_en.html

# 6. Upload to Heyzine flipbook (EN first, then VN)
node phases\02_curate\run-upload.js "reports\{base}\exports\pdf\{base}_report_en.pdf"
node phases\02_curate\run-upload.js "reports\{base}\exports\pdf\{base}_report_vn.pdf"
```

---

## Front-Page Cover (Intro) Typography & Diacritics Rules

- **Header & Session Titles (`.cover-company`, `.cover-session`)**: Always use `'Segoe UI Black', 'Segoe UI', Arial, sans-serif` with `font-weight: 900;` to ensure full, consistent glyph weight across all Vietnamese uppercase diacritics (e.g. `Ả`, `Ổ`, `Ề`, `Ứ`, `Á`). Standard Arial (`font-weight: 800/900`) must be avoided on titles with Vietnamese diacritics as it causes synthetic/inconsistent font fallback.
- **Top-Left Header**:
  - Morning: `BẢN TIN BUỔI SÁNG` (VN) / `MORNING NEWS` (EN)
  - Afternoon: `BẢN TIN BUỔI CHIỀU` (VN) / `AFTERNOON NEWS` (EN)
- **Bottom-Right Session Title**:
  - Morning: `CAFE CHỨNG KHOÁN` (VN) / `MARKET ESPRESSO` (EN)
  - Afternoon: `TRÀ CHIỀU CHỨNG KHOÁN` (VN) / `THE POST-MARKET TEA` (EN)
- **Tagline**: `Trung tâm Phân Tích - Bản Tin Tổng Hợp` (VN) / `Research Division - Comprehensive Bulletin` (EN)
- **Date**: Bolded (`font-weight: bold;`)
- **Disclaimer Note**: Standard bilingual AI & research disclaimer across bottom margin.

---

## Outpage (Outro / Back Cover) Standard Rules

- **Top Company Title (`.outro-company`)**:
  - VN: `CTCP CHỨNG KHOÁN KIS VIỆT NAM`
  - EN: `KIS VIETNAM SECURITIES CORPORATION`
- **Center Thanks Row (`.outro-ty`)**:
  - VN: `TRÂN TRỌNG CẢM ƠN`
  - EN: `THANK YOU`
- **Bottom Copyright (`.outro-copy`)**:
  - VN: `Bản quyền © 2026 thuộc về CTCP Chứng khoán KIS Việt Nam.<br>Bảo lưu mọi quyền.`
  - EN: `Copyright © 2026 by KIS Vietnam Securities Corporation.<br>All rights reserved.`

---

## HSX Insider Trading Extraction & Vision Rules

- **Preferred: Text-Layer Extraction via Scripts**: For most HSX insider trading PDFs, use `extract_hsx_from_manifest.py` to extract structured data from the PDF text layer, then `llm_brain/extractors/hsx_agent_extractor.py` to merge agent results. This is the primary, reliable pipeline.
- **Fallback: Multimodal Vision Extraction**: Reserve direct vision inspection of rendered PNG images (from `hsx_prepare_pdfs.py`) **only** for scanned PDFs that have no usable text layer. Check for a text layer before falling back to vision.
- **Do Not Use Local OCR**: Avoid local OCR scripts or OCR libraries. Use either the text-layer extractor or multimodal vision capabilities.
- **⚠️ Agent Safety**: **NEVER call `view_file` on `.png` image files in `pdf_images/`** in the summarize pipeline. Calling `view_file` on large binary PNG images will exhaust context and crash the agent environment.
- **Extraction Contract**:
  - Capture: issuer ticker/name, insider name, insider role/relationship, transaction type, registered volume, executed volume, ownership before/after, transaction dates, disclosure dates, source news ID, source PDF URL/path.
  - Classify only relevant insider-trading items. Do not merge bond disclosures, governance resolutions, or general corporate actions.
  - Prefer explicit PDF table values. If a field is absent, leave it empty/null — do not fabricate.
  - Keep insider identity separate from issuer identity.
  - Preserve traceability: final report item → scrape JSON → extracted JSON → PDF attachment.

---

## Commodities News Titles Standard Rule

- **Descriptive & Dynamic Titles**: Commodities news titles (e.g. Gold, Silver, Live Hogs, Agriculture, Energy) under `economy_political_others` must always be descriptive, specific, and accurately reflect actual price movements, current price ranges, and market direction (e.g. `SJC gold prices drop VND300,000 to VND142.3-145.3mn/tael`, `Phu Quy silver prices listed around VND1.88-1.95mn/tael`, `Live hog prices steady across three regions at VND57,000-60,000/kg`).
- **Never Use Generic or Misleading Placeholders**: Avoid static or generic placeholder titles (e.g. "prices listed at X" or stating "downward trend" when prices are actually steady or slightly increasing).

---

## Working Rules

- **NEVER run `upload-to-sheets.js` if the sentinel file for today's session exists** (`phases\02_curate\logs\{morning|afternoon}_{YYYYMMDD}.done`). Re-uploading overwrites the sheet tab and destroys TAKE values. The user must delete the sentinel to force a re-run.
- Always use `phases\01_scrape\venv\Scripts\python.exe` — never `python`, `py`, or another venv.
- Route new output-producing code through the shared path helpers (`core_tools/paths/report_paths.py` / `report-paths.js`).
- **Opus 4.6 Thinking Orchestrator & Subagents**: When Opus 4.6 Thinking is used as the main orchestrator, subagents (file search, exploring, research, scraping, etc.) run on Gemini 3.8 Flash (`Model: "flash"`). This is enforced via `.agents/hooks.json` (`PreToolUse` on `invoke_subagent`) and guided by `.agents/rules/subagent-orchestrator.md`.
- All report artifacts belong in `reports/{base}/` — never write them to project root, `phases/`, or any other location.
- **Temporary Files Convention (`/tmp`)**: Any temporary, scratch, or intermediate working files created during development, research, debugging, testing, or script runs MUST be placed into an organized `tmp/` folder (at project root: `W:\KIS-DAILY-NEWS\tmp` or `/tmp`). Never create loose temporary files in the repository root or arbitrary directories. Organize files inside `tmp/` using descriptive names or subfolders (e.g. `tmp/debug/`, `tmp/scrapes/`).
- Keep `core_tools/templates/` for templates and static assets only.
- Keep `phases\02_curate\logs\` for small text logs only.
- Put temporary browser/debug artifacts in `reports/{base}/testing/`, `tmp/`, or an OS temp directory.
- Prefer overwriting stale files inside a run-specific testing folder over creating timestamped clutter.
- Use `127.0.0.1` for Chrome CDP connections; `localhost` may resolve to IPv6.
- Put HSX insider runtime JSON, downloaded PDFs, and debug artifacts under `reports/{base}/testing/` or `phases/01_scrape/pdfs/`.

### Chrome Automation Pattern

- Scripts connect to Chrome over CDP on port `9222`.
- If Chrome is stuck: close Chrome, clear profile singleton lock files (`SingletonLock`, `SingletonCookie`, `SingletonSocket`), then reconnect with `chromium.connectOverCDP('http://127.0.0.1:9222')`.

---

## Tool Schema Guidelines (Prevents Retry Loops)

- **Integer Parameters**: When calling tools with integer arguments (e.g. `ContentOffset` in `view_file`), always pass as a raw **integer** (e.g. `51200`), NEVER as a string (`"51200"`). Schema validation fails on strings and causes agents to loop.
- **Subagent Prompts**: If spawning a subagent that reads files, explicitly instruct it in the system prompt to pass integer arguments as integers.

---

## Karpathy Reasoning Guidelines

- Think before coding: state the expected input shape, inspect evidence, then change the smallest useful piece.
- Do not assume PDF layouts. Check representative PDFs, text layers, rendered PNG images, or extracted JSON before changing parser behavior.
- Prefer simple, direct implementations using existing helpers and standard Python.
- Keep changes surgical — preserve existing style, file layout, imports, and output conventions.
- Define concrete success criteria before changing parsers.
- If requirements are vague or document layouts are ambiguous, pause and clarify instead of guessing.
- Use diacritic-robust matching for Vietnamese classification and joins. Preserve final Vietnamese text with NFC normalization.
- Vietnamese `đ` and `Đ` must be replaced with `d` and `D` **before** NFD decomposition. Always use NFC for output Vietnamese text — never NFKC/NFKD.

---

## Google Sheets

Session tabs use `mor_DD_MM_YYYY` or `after_DD_MM_YYYY`. The UI is Vietnamese.

- Add Sheet button: `[aria-label="Thêm trang tính"]`
- Active tab: `.docs-sheet-active-tab`
- Tab names: `.docs-sheet-tab-name`
- Name box: `.waffle-name-box`; use `{ force: true }` when a modal overlay intercepts pointer events.
