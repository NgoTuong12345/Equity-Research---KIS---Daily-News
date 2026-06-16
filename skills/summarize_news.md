# Summarize News Articles - KIS Style

Use this skill when the user asks to summarize a selected batch of Vietnamese financial news.

## Workflow

1. Generate or read `reports/{base}/source/{base}_full.md`.
2. Summarize every selected article in Vietnamese first, then English.
3. Classify feed articles into `corporate` or `economy_political_others`.
4. Write summary JSON and bilingual markdown into `reports/{base}/data/` and `reports/{base}/summaries/`.
5. After writing each JSON file, run the harness to validate output (see **Harness Validation** below).
6. When all items pass (or retries are exhausted), automatically invoke the `/dedup-news` skill.

## Writing Rules

- **35–45 words max per paragraph (must be strictly under 300 characters to avoid truncation)**
- **Titles**: Generate objective, fact-based descriptive titles driven from the full content. Do not rely on the raw fetched title. Avoid question marks, personal opinions, quotes, or clickbait. Keep them concise (max 70 chars / 12 words) in VN and EN to avoid truncation.
- **Start with date**: Vietnamese → `Ngày D/M,`  |  English → `On D Month,`
- **Prioritize data/figures/numbers** from the source
- Active voice. No contractions. Confident, institutional tone.
- Do not mix Vietnamese and English inside the same section.

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
2. Word count — both VN and EN must be 40–60 words
3. Both languages — each ≥ 20 words, not identical
4. Numbers preserved — key figures from source must appear in the summary

---

## Auto-Chain

When all JSON files are written and validated (or retries exhausted), **automatically invoke the `/dedup-news` skill** without waiting for user input.
