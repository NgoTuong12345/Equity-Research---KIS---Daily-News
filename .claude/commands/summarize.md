End-to-end pipeline: reads TAKE-selected articles from Google Sheets, fetches full content, pulls macro sheet data, classifies and summarizes everything, then generates bilingual HTML reports. Run this once after marking TAKE in the sheet.

---

## Step 0 — Determine session

Parse `$ARGUMENTS`:

- `morning` or `mor` → session = `morning`
- `afternoon` or `after` → session = `afternoon`
- A file path ending in `_full.md` → skip to **Step 4**, use that file directly (re-run/debug mode)
- Empty → detect from current hour via Bash:

```powershell
(Get-Date).Hour
```

If hour < 12 → session = `morning`; otherwise → session = `afternoon`.

---

## Step 1 — Extract TAKE URLs from Google Sheets

Run via Bash:

```powershell
cd C:\Users\Administrator\Playwright-Daily-News\google-sheets-uploader
node generate-report.js morning
```

(substitute `afternoon` when applicable)

This opens Chrome via CDP, reads the active session tab, and writes the report file to `reports/`. On success the script prints the output file path — capture it. The file is named `reports/mor_DD_MM_YYYY.md` or `reports/after_DD_MM_YYYY.md`.

Derive `{base}` from the filename (e.g. `mor_04_06_2026`). Derive `{date}` in `DD/MM/YYYY` format from the base (e.g. `04/06/2026`).

If the script errors, stop and report the error to the user.

---

## Step 2 — Fetch full article content

Run via Bash:

```powershell
cd C:\Users\Administrator\Playwright-Daily-News
python fetch_full_articles.py reports/{base}/source/{base}.md
```

This fetches the full body text of each article and writes `reports/{base}/source/{base}_full.md`.

### Fetch Design & Fallback System
The fetching system is rate-limit aware and uses a robust shared session with retry fallbacks:
1. **Robust Requests Session:** Uses a shared `requests.Session` mounted with a `urllib3.util.Retry` strategy (configured for 3 retries with exponential-like backoff factor 1.0, handling status codes 429, 500, 502, 503, 504).
2. **Rate-Limit Aware Partitioning:**
   - Partitioned all article URLs into Standard and Sensitive/Rate-limited domains (`tinnhanhchungkhoan.vn`, `baodautu.vn`).
   - Standard URLs are fetched concurrently (`max_workers=8`) for maximum speed.
   - Sensitive/Rate-limited URLs are fetched sequentially with a built-in safety delay of `1.2s` between requests.
   - Failed fetches automatically fall back to a sequential retry loop with a `2.0s` delay.
3. **Resilient Scraper (main.py):**
   - Detail scraping for `tinnhanhchungkhoan` and `baodautu` runs with limited concurrency (`max_workers=2` instead of `10`), preventing anti-bot filters from blocking connections.
   - Added retry logic and backoff directly inside the core `get_soup()` function.

If the script errors, stop and report the error to the user.

---

## Step 3 — Read macro sheet data

Run this step for **morning reports only**. Afternoon reports must skip Macro and vin_bank Google Sheets data.

Run via Bash:

```powershell
cd C:\Users\Administrator\Playwright-Daily-News\google-sheets-uploader
node read-macro-sheet.js morning {date}
```

(e.g. `node read-macro-sheet.js 04/06/2026`)

This reads the **Macro** and **vin_bank** tabs of the Google Sheet and writes `reports/{base}/data/macro_sheet_DD_MM_YYYY.json`.

If this command is called with `afternoon`, it writes an empty skipped payload and does not read Macro/vin_bank.

Read the resulting JSON. Each item is pre-summarized (do not re-summarize) and has a `source_tab` field:
- **`source_tab: "macro"`**: These items route to `reports/{base}/data/{base}_macro.json` (under the `macro` category). Do not put them in `reports/{base}/data/{base}_economy_political_others.json`.
- **`source_tab: "vin_bank"`**: Route these items dynamically based on their `news_category`:
  - If the category is a listed company ticker (e.g., `VIC`, `VHM`, `ACB`, `MBB`, `BID` - check `ticker_index.json`), route it to `reports/{base}/data/{base}_corporate.json` under the correct sector. Look up the full company name and exchange as usual. Use `title_vn`/`title_en` and `body_vn`/`body_en` from the JSON item directly for the title and summary fields. Note: If the category is `TCBS`, map it to `TCX`.
  - If the category is `Commodities`, route it to `reports/{base}/data/{base}_economy_political_others.json` under the `commodities` subtype.
  - If the category is anything else, route it to `reports/{base}/data/{base}_economy_political_others.json` under the appropriate subtype (e.g., `economies_investments` or `others`).

If this step errors or returns `item_count: 0`, log a warning and continue — macro sheet data is additive, not required.

---

## Step 4 — Read the full article file

Read `reports/{base}/source/{base}_full.md` with the Read tool.

For each `### Article title` block, collect:
- Title, Source, Category, Published date (if present)
- Summary and Full Content sections

---

## Step 5 — Classify & tag

### Ticker lookup

Read `C:\Users\Administrator\Playwright-Daily-News\ticker_index.json` **once**. It contains 3,261 Vietnamese tickers with `company_en`, `company_vn`, `sector_key`, `exchange` pre-filled. Look up any corporate ticker here first — do not guess.

If a ticker is not found:
- `exchange`: use `"Unlisted"` for unlisted/private or foreign companies (e.g. AeonMall, VinSpeed), `"SOE"` for state-owned not on any exchange
- `sector_key`: infer from business type

### Category assignment

Assign each article from the batch feed exactly **one** category:

| Category key | Route here when… |
|---|---|
| `corporate` | Article appears under `## Corporate News` in `_full.md`, OR concerns a specific listed company |
| `economy_political_others` | Govt projects, legislation, social, commodity prices, international relations, macro aggregates (monetary policy, CPI, GDP, FX, bond yields, credit growth, trade balance, FDI aggregates), trading sessions, everything else |

> **CRITICAL ROUTING RULE:** The categories `macro` and `trading` must NOT be assigned to batch feed articles. 
> - Any macro/economic-looking articles in the feed (CPI, FDI, budget, GDP, etc.) must be categorized under `economy_political_others` -> subtype `economies_investments`.
> - Any market trading-session or index-move articles in the feed must be categorized under `economy_political_others` -> subtype `economies_investments` (or `others` if unrelated to macro/investment).

> **HARD OVERRIDE:** If an article is under `## Corporate News` in `_full.md`, it is `corporate` — no reclassification.

**Corporate articles** — also extract:
- `ticker` — from `ticker_index.json` first, then from article text (e.g. `APSC` from "Chứng khoán Alpha (APSC)"). Note: If the ticker is `TCBS`, it must be mapped to `TCX` (exchange `HSX`, company `Chứng khoán TCBS`).
- `exchange` — from index, or exactly one of: `HSX`, `HNX`, `UPCoM`, `OTC`, `Unlisted`. If the company is unlisted/private/foreign and not listed on any stock exchange (e.g. AeonMall, Aeon Mall, Vinpearl, Thaispace, Green SM, VinSpeed, Vinspeed), you MUST use the exchange value `Unlisted` (do NOT classify them as UPCoM/UPCOM/HNX/HSX).
- `company_vn` / `company_en` — from index, or extracted from article text
- `sector_key` — from index, or inferred. MUST be exactly one of: `banking`, `financials`, `consumers`, `industrials`, `materials`, `real_estate`, `technologies`, `pharma`, `utilities`, `oil_gas`. NEVER use `others` for corporate news; always map to a specific sector (e.g. VNM -> consumers).

**Economy/political/others** — assign a subtype:
- `economies_investments` — FDI totals, investment zones, capital flows, economic aggregates
- `political` — leadership decisions, state resolutions, government directives
- `policies` — legislation, decrees, circulars, regulatory/admin reform
- `social` — housing, health, education, welfare, citizen-facing infrastructure
- `commodities` — commodity prices (sugar, steel, oil, agricultural products)
- `international_relation` — diplomatic events, bilateral meetings, trade agreements
- `others` — anything else

---

## Step 6 — Write summaries

Write ALL Vietnamese summaries first, then ALL English summaries in the same article order.

**Macro sheet items (from Step 3): copy `body_vn`/`body_en` directly — do not rewrite.**

### KIS institutional style

**Voice & tone**
- Active voice: "HPG will expand capacity" — never passive
- Possessives: "VCB's NIM" not "the NIM of VCB"
- No contractions: "do not", "will not", "it is"
- Confident, forward-looking, sell-side institutional tone

**Numbers & units**
- bn / tn / mn (not bln / trn / mln)
- Approximate: `~12%`, `~VND1,100tn`
- Ranges: `10%–15%`, `2024–2026` (hyphens)
- Spell out 1–9 in prose; digits for 10+
- EN→VN terms: NHNN, TPCP, LNST, LNTT, n/n, q/q, đcb, đpt, svđn
- VN→EN terms: NPAT, EBT, yoy, qoq, %p, YTD, VND2bn, 8mn shares
- Unchanged: USD, VND, FDI, PMI, VNINDEX, HSX, HNX, UPCoM, KIS, Bloomberg

**Per paragraph**
- 35–45 words maximum (must be strictly under 300 characters to avoid truncation)
- Titles: Generate objective, fact-based descriptive titles driven from the full content. Do not rely on the raw fetched title. Avoid question marks, personal opinions, quotes, or clickbait (e.g. BAD: "Russia makes a statement", GOOD: "Russia's real income surges 24% over 3 years"). Keep them concise (max 70 chars / 12 words) in VN and EN to avoid truncation.
- Start with date: VN → `Ngày D/M,` | EN → `On D Month,` (omit if no date)
- Prioritize data, figures, numbers
- No bullet points — plain paragraphs only

---

## Step 7 — Save summary files

Save to:
- `C:\Users\Administrator\Playwright-Daily-News\reports\{base}\summaries\{base}_summary_vn.md`
  Header: `# Tóm tắt tin tức — {base} (Tiếng Việt)`. Under the `## GIAO DỊCH` section, list each transaction summary directly in the new NLM-extracted format, one per line, ending with a semicolon `;`.
- `C:\Users\Administrator\Playwright-Daily-News\reports\{base}\summaries\{base}_summary_en.md`
  Header: `# News Summary — {base} (English)`. Under the `## TRADING` section, list each transaction summary directly in the new NLM-extracted format, one per line, ending with a semicolon `;`.

Use the Write tool. Confirm both file paths.

---

## Step 8 — Emit 4 category JSON files

Save to:
- `reports/{base}/data/{base}_macro.json`
- `reports/{base}/data/{base}_trading.json`
- `reports/{base}/data/{base}_corporate.json`
- `reports/{base}/data/{base}_economy_political_others.json`

**Macro report (`reports/{base}/data/{base}_macro.json`):** Contains the pre-written macro sheet items read in **Step 3** from `reports/{base}/data/macro_sheet_*.json`. It does NOT contain any batch-summarized articles from `_full.md`.

**Trading report (`reports/{base}/data/{base}_trading.json`):** Contains the HSX insider trading transactions extracted from the latest `vietnam_news_scraper/hsx_insider_trading_*_extracted.json`.
- It does NOT contain any batch-summarized articles from `_full.md`.
- Bilingual titles and summaries must be generated in KIS Style from the extracted PDF transaction parameters using these strict templates:
  - **`title_vn`**: `<ticker>. (<company_fullname_vn>. <exchange>)` (e.g. `SSI. (Công ty Cổ phần Chứng khoán SSI. HSX)`)
  - **`title_en`**: `<ticker>. (<company_fullname_en>. <exchange>)` (e.g. `SSI. (SSI Securities Corporation. HSX)`. Use standard English translations for the full company name, appending 'Joint Stock Company' or 'Corporation' where appropriate).
  - **`summary_vn`**: `<ticker> (<company_fullname_vn>) <exchange>: <date_range>. <name> (<relationship>) thông báo đăng ký [mua/bán] <change_volume> cổ phiếu, [tăng/giảm] tổng số lượng cổ phiếu nắm giữ lên/xuống <after_volume> cổ phiếu (<after_percentage>);`
    *(Example: `SIP (Công ty Cổ phần Đầu tư Sài Gòn VRG) HSX: 06/10~07/09. Trần Lê An (Con của Chủ tịch Hội đồng Quản trị) thông báo đăng ký mua 3,700,000 cổ phiếu, tăng tổng số lượng cổ phiếu nắm giữ lên 6,003,174 cổ phiếu (2.48%);`)*
  - **`summary_en`**: `<ticker> (<company_fullname_en>) <exchange>: <date_range>. <name_en> (<relationship_en>) announced to [buy/sell] <change_volume> shares, [increasing/decreasing] total shares to <after_volume> shares (<after_percentage>);`
    *(Example: `SIP (Sai Gon VRG Investment Joint Stock Company) HSX: 06/10~07/09. Tran Le An (Child of the Chairman of the Board of Directors) announced to buy 3,700,000 shares, increasing total shares to 6,003,174 shares (2.48%);`)*
  - If an article has multiple transacting parties, split them into separate items, incrementing the `"order"` field accordingly.
  - Apply standard translations for relationships (e.g. `Con của` -> `Child of`, `Chủ tịch HĐQT` -> `Chairman of the Board of Directors`, `Thành viên HĐQT` -> `Member of the Board of Directors`, `Kế toán trưởng` -> `Chief Accountant`, `Người có liên quan` -> `Related person of insider`, etc.) and ensure English names have accents stripped.

**Corporate report (`reports/{base}/data/{base}_corporate.json`):** Contains batch feed articles classified as `corporate`.

**Economy/Political/Others report (`reports/{base}/data/{base}_economy_political_others.json`):** Contains batch feed articles classified as `economy_political_others` (including macro-like articles routed here under subtype `economies_investments`). It does NOT contain macro sheet items.

Rendered report order must be: intro cover -> macro -> trading -> commodities -> corporate sector news -> political -> policies -> economic investments -> social -> international relations -> others -> outro. Afternoon reports normally omit macro and commodities because Macro/vin_bank Google Sheets data are morning-only.

Corporate and trading display titles must use `<ticker>. (<company_fullname>. <exchange>)`, for example `VIC. (Vingroup. HSX)`.

**Flat schema** (macro and trading):
```json
{
  "report": "{base}", "session": "mor or after",
  "category": "macro",
  "section_title_vn": "KINH TẾ VĨ MÔ", "section_title_en": "Macroeconomics",
  "generated_at": "<ISO-8601 +07:00>", "item_count": 3,
  "items": [
    { "order": 1, "title_vn": "...", "title_en": "...",
      "summary_vn": "Ngày D/M, ...", "summary_en": "On D Month, ...",
      "source": "...", "url": "...", "published": "DD/MM/YYYY" }
  ]
}
```
Trading: `"section_title_vn": "GIAO DỊCH"`, `"section_title_en": "Trading"`.

**Corporate schema** (grouped by sector):
```json
{
  "report": "{base}", "session": "...", "category": "corporate",
  "generated_at": "...", "item_count": 5,
  "sectors": [
    { "sector_key": "banking",
      "section_title_vn": "NGÂN HÀNG", "section_title_en": "Banking",
      "items": [
        { "order": 1, "ticker": "ACB",
          "company_vn": "Ngân hàng Á Châu", "company_en": "Asia Commercial Bank",
          "exchange": "HSX",
          "title_vn": "...", "title_en": "...",
          "summary_vn": "...", "summary_en": "...",
          "source": "...", "url": "...", "published": "..." }
      ]
    }
  ]
}
```

**Economy/political/others schema** (grouped by subtype):
```json
{
  "report": "{base}", "session": "...", "category": "economy_political_others",
  "generated_at": "...", "item_count": 20,
  "subtypes": [
    { "subtype_key": "economies_investments",
      "section_title_vn": "KINH TẾ & ĐẦU TƯ", "section_title_en": "Economies & Investments",
      "items": [
        { "order": 1, "title_vn": "...", "title_en": "...",
          "summary_vn": "...", "summary_en": "...",
          "source": "Macro Sheet", "url": "", "published": "DD/MM/YYYY" }
      ]
    }
  ]
}
```

**Subtype section titles:**
`economies_investments` → KINH TẾ & ĐẦU TƯ / Economies & Investments
`political` → CHÍNH TRỊ / Political
`policies` → CHÍNH SÁCH / Policies
`social` → XÃ HỘI / Social
`commodities` → HÀNG HÓA / Commodities
`international_relation` → QUAN HỆ QUỐC TẾ / International Relations
`others` → KHÁC / Others

Use the Write tool for each file. After saving all 4, confirm:
- All 4 file paths
- Item count per category (e.g. `macro: 4, trading: 1, corporate: 9, economy_political_others: 22 (incl. N from macro sheet)`)
- Total = articles from Step 4 + macro sheet items from Step 3

---

## Step 8.5 — Perform semantic deduplication

After emitting the 4 category JSON files, run the deduplication script to clean up any duplicate news items in the corporate, political, and policies categories:

```powershell
cd C:\Users\Administrator\Playwright-Daily-News
C:\Users\Administrator\Playwright-Daily-News\vietnam_news_scraper\venv\Scripts\python.exe scripts/deduplicate_reports.py {base}
```

This script will read `{base}_corporate.json` and `{base}_economy_political_others.json`, detect duplicate announcements using a Jaccard word-set similarity metric, remove the duplicates (keeping the most descriptive summary version), reindex the item count and order, and save the updated payloads.

Verify that the validation script passes after deduplication:
```powershell
C:\Users\Administrator\Playwright-Daily-News\vietnam_news_scraper\venv\Scripts\python.exe scripts/validate_summary_data.py {base}
```

---

## Step 9 — Generate HTML reports

Run via Bash:

```powershell
cd C:\Users\Administrator\Playwright-Daily-News
C:\Users\Administrator\Playwright-Daily-News\vietnam_news_scraper\venv\Scripts\python.exe scripts/generate_html_report.py {base}
```

This reads the 4 JSON files and writes:
- `reports/{base}/exports/html/{base}_report_vn.html`
- `reports/{base}/exports/html/{base}_report_en.html`

Confirm both output file paths to the user.

---

## Step 10 — Generate PDF reports

Run via Bash:

```powershell
cd C:\Users\Administrator\Playwright-Daily-News
C:\Users\Administrator\Playwright-Daily-News\vietnam_news_scraper\venv\Scripts\python.exe scripts/generate_pdf_report.py {base}
```

This loads the generated HTML reports and renders them into custom dimension PDFs:
- `reports/{base}/exports/pdf/{base}_report_vn.pdf`
- `reports/{base}/exports/pdf/{base}_report_en.pdf`

Confirm both output file paths to the user.

---

## Step 10.5 — Upload English PDF to Heyzine Flipbook

Run via Bash:

```powershell
cd C:\Users\Administrator\Playwright-Daily-News\google-sheets-uploader
node run-upload.js C:\Users\Administrator\Playwright-Daily-News\reports\{base}\exports\pdf\{base}_report_en.pdf
node run-upload.js C:\Users\Administrator\Playwright-Daily-News\reports\{base}\exports\pdf\{base}_report_vn.pdf
```

This uploads both English and Vietnamese PDFs to Heyzine:
- It launches Chrome via CDP on port 9222 using the default profile
- Closes any open login backdrop overlays
- Sets the EN Title (`Morning News_KIS_RESEARCH_DD_MM_YYYY` or `Afternoon News_KIS_RESEARCH_DD_MM_YYYY`)
- Sets the VN Title (`Bản tin buổi sáng_KIS_RESEARCH_DD_MM_YYYY` or `Bản tin buổi chiều_KIS_RESEARCH_DD_MM_YYYY`)
- Sets the Page Effect to `Notebook`
- Opens the Share modal and extracts the unique flipbook link
- Saves extracted links to `reports/{base}/exports/heyzine_links.json`

Wait for the success console message and capture both URLs.

---

## Step 11 — Generate Word (DOCX) reports

Run via Bash:

```powershell
cd C:\Users\Administrator\Playwright-Daily-News
C:\Users\Administrator\Playwright-Daily-News\vietnam_news_scraper\venv\Scripts\python.exe scripts/generate_docx_report.py {base}
```

This generates the daily Word bulletin:
- `reports/{base}/exports/docx/Afternoon News_KIS RESEARCH_{date_dots}.docx` (if afternoon report, e.g. 04.06.2026)
- `reports/{base}/exports/docx/Morning News_KIS RESEARCH_{date_dots}.docx` (if morning report)

Confirm the output DOCX path to the user.

---

## Done

Report complete. Confirm to the user:
1. Session and date processed
2. Number of articles (from sheet + macro sheet)
3. Distribution: macro / trading / corporate / economy_political_others
4. Paths to the HTML, PDF, and DOCX reports (morning/afternoon session)
5. Heyzine Flipbook Share Links (English and Vietnamese reports)
