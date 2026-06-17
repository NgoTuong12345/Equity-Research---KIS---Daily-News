# Summarize News Articles - KIS Style

Use this skill when the user asks to summarize a selected batch of Vietnamese financial news.

## Workflow

1. Read `reports/{base}/source/{base}.md` — this file is produced by `/curate-news` (`node phases\02_curate\generate-report.js {SESSION}`). If it does not exist, stop and invoke `/curate-news` first.
2. **Morning sessions only — Read Macro + vin_bank tabs from Google Sheets:**
   ```
   node phases\02_curate\read-macro-sheet.js DD/MM/YYYY
   ```
   Replace `DD/MM/YYYY` with today's date (e.g. `16/06/2026`).
   This saves `reports\{base}\data\macro_sheet_DD_MM_YYYY.json` with all items from the `Macro` tab and `vin_bank` tab that match today's date.
   **If this file is missing or empty, stop and warn the user** — macro and vin_bank content will be absent from the report.
   For afternoon sessions, skip this step (macro/vin_bank are morning-only inputs).
2b. **Extract and Format HSX Insider Trading disclosures:**
   Since the downloader step runs automatically via Windows Scheduled Tasks, the latest raw JSON `phases\01_scrape\hsx_insider_trading_*.json` and its `*_manifest.json` will already be present in `phases\01_scrape\`.
   
   Identify the latest `hsx_insider_trading_{timestamp}.json` and its matching `*_manifest.json` for the current session.
   
   - **Case A: The manifest has 0 PDFs (empty list)**:
     1. Write an empty JSON array `[]` directly to `phases\01_scrape\hsx_insider_trading_{timestamp}_extracted.json`.
     2. Run preparation to generate an empty `*_to_format.json`:
        ```powershell
        phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\format_hsx_trading_news.py --prepare phases\01_scrape\hsx_insider_trading_{timestamp}_extracted.json
        ```
     3. Write an empty JSON array `[]` directly to `phases\01_scrape\hsx_insider_trading_{timestamp}_agent_formatted.json`.
     4. Merge to write an empty `*_extracted_formatted.json`:
        ```powershell
        phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\format_hsx_trading_news.py --merge phases\01_scrape\hsx_insider_trading_{timestamp}_extracted.json
        ```
        
   - **Case B: The manifest contains PDFs to extract**:
     1. Read the rendered page PNGs in `phases\01_scrape\pdf_images\{article_id}\` using the agent's vision capabilities, or read the text layer in the manifest if `has_text_layer` is true.
     2. Extract all transactions according to the **Extraction Contract** in `GEMINI.md` (capturing fields: `ticker`, `name`, `relationship`, `action`, `change_volume`, `after_volume`, `after_percentage`, `date_range`, `company_fullname`, `exchange`).
     3. Save the results as a JSON mapping `article_id` to `{"transactions": [...]}` at `phases\01_scrape\hsx_insider_trading_{timestamp}_agent_results.json`.
     4. Merge the extracted transactions into `_extracted.json`:
        ```powershell
        phases\01_scrape\venv\Scripts\python.exe llm_brain\extractors\hsx_agent_extractor.py --manifest phases\01_scrape\hsx_insider_trading_{timestamp}_manifest.json --results phases\01_scrape\hsx_insider_trading_{timestamp}_agent_results.json
        ```
     5. Prepare unique transactions for prose formatting:
        ```powershell
        phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\format_hsx_trading_news.py --prepare phases\01_scrape\hsx_insider_trading_{timestamp}_extracted.json
        ```
        This creates `phases\01_scrape\hsx_insider_trading_{timestamp}_to_format.json`.
     6. Read `*_to_format.json` and translate/format each unique transaction into bilingual prose (`summary_vn` and `summary_en`) adhering to KIS trading writing rules.
     7. Save these formatted transactions to `phases\01_scrape\hsx_insider_trading_{timestamp}_agent_formatted.json`.
     8. Merge agent formatted output into final outputs:
        ```powershell
        phases\01_scrape\venv\Scripts\python.exe phases\01_scrape\format_hsx_trading_news.py --merge phases\01_scrape\hsx_insider_trading_{timestamp}_extracted.json
        ```
        This saves `phases\01_scrape\hsx_insider_trading_{timestamp}_extracted_formatted.json` which `combine_chunks.py` will read.
3. Summarize every selected article in Vietnamese first, then English (TAKE articles from step 1 only — not macro/vin_bank items, which are verbatim).
4. Classify feed articles into `corporate` or `economy_political_others`.
5. Run the combine script to compile summarized chunks, macro sheet items, and the formatted trading news into the final 4 category JSONs:
   ```powershell
   phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\combine_chunks.py {base}
   ```
   This writes the summary JSONs and bilingual markdown files into `reports/{base}/data/` and `reports/{base}/summaries/`. Items from `macro_sheet_*.json` are distributed as follows:
   - `source_tab = "macro"` → verbatim into `{base}_macro.json`
   - `source_tab = "vin_bank"` + `news_category` is a known ticker → verbatim into `{base}_corporate.json` (correct sector)
   - `source_tab = "vin_bank"` + `news_category` is non-ticker (e.g. Commodities, Macro) → verbatim into `{base}_economy_political_others.json` (correct subtype)
6. After writing each JSON file, run the harness to validate output (see **Harness Validation** below).
7. When all items pass (or retries are exhausted), automatically invoke the `/dedup-news` skill.

## Writing Rules

### LLM-generated summaries (corporate, economy_political_others non-vin_bank)
- **Up to 60 words per summary paragraph (max cap enforced by harness — no minimum)**
- **Start with date**: Vietnamese → `Ngày D/M,`  |  English → `On D Month,`
- **Prioritize data/figures/numbers** from the source
- Active voice. No contractions. Confident, institutional tone.
- **Facts only.** Every sentence must be directly stated in the source. Do NOT add interpretation, implied significance, or editorial commentary not in the source.
- Banned patterns: *"reflecting X"*, *"marking a milestone"*, *"strengthening X"*, *"aimed at improving X"*, *"amid a broader"*, *"supporting Vietnam's push to"*, *"raising concerns among"*, *"this proves"*, *"this shows that"*, *"this remarks"*. If the source does not state it, do not write it.
- Do not mix Vietnamese and English inside the same section.

### Google Sheets verbatim content (macro, commodities/vin_bank)
- **Source**: `reports\{base}\data\macro_sheet_DD_MM_YYYY.json` — produced by step 2 above (`read-macro-sheet.js`).
- **Do NOT rephrase.** Copy `body_vn` → `summary_vn` and `body_en` → `summary_en` exactly as-is.
- Word count rules **do not apply** — harness skips enforcement for `category: macro` and `source: vin_bank`.
- These items are written by analysts upstream; your only role is to place them in the JSON with correct field names.

### Trading items (insider transactions)
- **Concise facts only.** State: who, relationship, action (buy/sell), volume, post-trade holding, date range.
- **No forced padding** — do not add filler sentences to hit a word floor.
- Harness enforces only a 10-word minimum (each language) — no upper limit.
- Keep EN and VN structurally parallel but not identical word-for-word.

### All items
- **Titles**: Objective, fact-based, derived from full content. Max 70 chars / 12 words. No question marks, quotes, or clickbait.

## Classification

- `corporate`: ONLY listed-company news with a specific stock ticker (e.g., VIC, VHM, FPT). Include ticker, exchange (must be exactly one of: HSX, HNX, UPCoM, OTC, Unlisted), company names, and sector. If the company is unlisted/private/foreign and not listed on any stock exchange (e.g. AeonMall, Aeon Mall, Vinpearl, Thaispace, Green SM, VinSpeed, Vinspeed), you MUST use the exchange value `Unlisted` (do NOT classify them as UPCoM/UPCOM/HNX/HSX). NEVER use `others` for the sector; always map to a specific sector (e.g. VNM -> consumers).
- `economy_political_others`: ALL non-ticker news. This includes: policy, macro aggregates, public projects, social issues, commodities, international relations, AND any associations, labor unions, exchanges, or unlisted entities (e.g., Vietnam Blockchain Association, Labor Union, Mercantile Exchange).
- Do not assign feed articles to `macro` or `trading`; those come from deterministic/non-feed sources.

## Style

- Use `bn`, `tn`, `mn`; avoid `bln` and `trn`.
- Use `~12%` for approximate values.
- Use hyphen ranges such as `10%-15%`.
- Keep market acronyms unchanged: USD, VND, FDI, PMI, VNINDEX, HSX, HNX, UPCoM, KIS, Bloomberg.
- Use local financial terms naturally: NHNN, TPCP, LNST, LNTT, yoy, qoq, NPAT, EBT, PM, BOD.

## Output Shape

Create four JSON files:

- `{base}_macro.json`
- `{base}_trading.json`
- `{base}_corporate.json`
- `{base}_economy_political_others.json`

Create two markdown files:

- `{base}_summary_vn.md`
- `{base}_summary_en.md`

The exact category keys, section titles, subtype names, sector names, required fields, and count validation are defined in `llm_brain/prompts_and_rules/summary_rules.py` and enforced by `core_tools/validation/validate_summary_data.py`.

## Precision Rules (must follow to avoid audit failures)

- **Numbers must be identical in EN and VN.** Copy figures verbatim from the macro sheet input (`body_en` / `body_vn`). Do NOT round independently in each language — divergence (e.g. `+17.89%` EN vs `+17,985%` VN) is an error.
- **Organisation full names in `company_vn` must be complete and typo-free.** Always write the full Vietnamese name (e.g. `Hiệp hội Blockchain và Tài sản số Việt Nam`, not `Tá sản`). When only an English name is available, copy it to `company_vn` unchanged.
- **Government agency names must be translated in full.** `Bảo hiểm xã hội Việt Nam` → `Vietnam Social Security` (never drop `Social`). Use the EN-VN term mapping in `skills/KIS_Writing_Style_Guide_final.md` as reference.
- **`company_vn` for listed banks and institutions must use the full name**, not just the ticker (e.g. `Asia Commercial Bank`, not `ACB`).
- **`title_en` / `title_vn` in macro JSON must match the label `news_title_rules.py` will render.** The script derives macro titles from content keywords (`interbank`, `G-bond`, etc.). Set JSON titles to the canonical label the script will show (e.g. `Government bond yield`, not `Money market`).

---

## Harness Validation

After writing each JSON file to `reports/{base}/data/`, run:

```
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\harness.py reports\{base}\data\{filename}.json
```

**If any item fails:**
- Re-summarize only the failing item(s)
- Include the exact error in your re-prompt, e.g.:
  - "summary_vn word count is 32, must be 40–60 — please rewrite to hit that range"
  - "numbers not preserved: ['12%', '500bn'] missing from summary — include them"
- Retry up to **3 times** per item
- After 3 failures, log the item title and error, skip it, and continue

The harness checks:
1. Schema — `title`, `summary_vn`, `summary_en`, `source`, `category` all present
2. Word count — max 60 words for LLM-generated items (corporate + economy_political_others with non-vin_bank source); 10-word floor only for trading; **skipped entirely** for macro and vin_bank-sourced items
3. Both languages — each ≥ 20 words, not identical (skipped for macro/vin_bank/trading)
4. Numbers preserved — key figures from source must appear in the summary

---

## Auto-Chain

When all JSON files are written and validated (or retries exhausted), **automatically invoke the `/dedup-news` skill** without waiting for user input.
