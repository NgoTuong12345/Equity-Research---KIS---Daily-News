---
name: paste-news
description: Process raw pasted article text directly into news reports, classify category/sector, summarize in KIS style, and append to JSON files.
---

# Paste News — Summarize Raw Text Content

Use this skill when the user pastes raw article text directly into the chat (no URL available), OR when the user runs `/paste-news` directly.

This handles content that cannot be fetched by URL — analyst notes, copied PDFs, WeChat/Telegram forwarded text, paywalled articles, or any ~400-word block pasted inline.

---

## Step 0 — Confirm Session & Base

Confirm `{base}` (e.g. `mor_20260616`). If not known, use the most recently modified directory under `reports/` that contains a `data/` subfolder.

---

## Step 1 — Receive the Content

The user pastes the raw text. Accept it as-is. Do not fetch any URL.

If the pasted text is under 20 words, ask the user to paste more context — it is too short to summarize meaningfully.

---

## Step 2 — Classify

Determine the correct JSON target based on content:

| Content type | Target file |
|---|---|
| Listed company with stock ticker (VIC, VHM, FPT, etc.) | `{base}_corporate.json` → correct sector |
| Policy, macro aggregate, association, unlisted entity, international | `{base}_economy_political_others.json` → correct subtype |
| Insider transaction (buy/sell shares, volume, holding) | `{base}_trading.json` |
| Interbank rate, G-bond yield, gold price, FX rate | `{base}_macro.json` |

State the classification to the user before writing: `"Classifying as: corporate / banking sector"`. Ask to confirm if ambiguous.

---

## Step 3 — Write the Summary

Follow all rules from `/summarize-news` (KIS style, data-first, bilingual):

- **`summary_vn`** and **`summary_en`** — max 60 words each; start with date (`Ngày D/M,` / `On D Month,`)
- **`title_vn`** and **`title_en`** — max 70 chars / 12 words, fact-based, no question marks
- For **trading items**: concise facts only — who, relationship, action, volume, post-trade holding, date range
- For **macro items**: do NOT rephrase — use the pasted text verbatim in each language

Set `"url": ""` and `"source": "manual_paste"` (or the source name if the user specifies it).

---

## Step 4 — Append to the JSON File

**Do NOT overwrite the file.** Read the existing JSON, insert the new item at the correct position (end of the appropriate sector/subtype `items` array), increment `item_count`, update `generated_at`, and write back.

For **corporate**: find the matching `sector_key` in the `sectors` array. If no matching sector exists, create it.

For **economy_political_others**: find the matching `subtype_key` in the `subtypes` array. If no matching subtype exists, create it.

Set `"order"` to the next sequential integer within that sector/subtype.

---

## Step 5 — Validate with Harness

```powershell
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\harness.py reports\{base}\data\{filename}.json
```

If validation fails, rewrite the failing item in the JSON and re-validate (up to 3 retries). After 3 failures, log the error, show it to the user, and ask whether to skip or try again.

---

## Step 6 — Confirm

```
✓ Added: "{title_en}"
  File: reports\{base}\data\{filename}.json
  Category: {category} / {sector or subtype}
  Validation: passed (or: passed after N retries)
```

Ask the user if they have more content to paste. If yes, repeat from Step 1. If no, the user can continue to `/dedup-news`.
