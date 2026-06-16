# Delta Summarize — Summarize Only New TAKE Items

Use this skill when the user updates TAKE selections in Google Sheets **after** `/summarize-news` has already run for the current session, and only the new additions need to be summarized.

This prevents re-summarizing items that are already in the JSON data files.

---

## When to Use

- User marked more URLs as TAKE in the sheet after initial summarization ran
- User wants to add articles from an updated sheet without losing existing summaries
- Avoids full re-run of `/curate-news` + `/summarize-news` from scratch

---

## Step 0 — Confirm Base

Confirm `{base}` (e.g. `mor_20260616`). The JSON data files at `reports\{base}\data\` must already exist from a previous `/summarize-news` run.

---

## Step 1 — Build the "Already Processed" URL Set

Read all four existing JSON files:

```
reports\{base}\data\{base}_corporate.json
reports\{base}\data\{base}_economy_political_others.json
reports\{base}\data\{base}_macro.json
reports\{base}\data\{base}_trading.json
```

Collect every non-empty `url` value from all `items` arrays across all files → build a set `seen_urls`.

Report: `"Already summarized: {N} items with URLs ({M} with empty URLs — vin_bank/manual sources)"`

---

## Step 2 — Pull the Current Sheet Selections

Re-run generate-report to get the latest TAKE state from Google Sheets:

```
cd phases\02_curate
node generate-report.js {SESSION}
```

This overwrites `reports\{base}\source\{base}.md` with the current sheet state. Chrome will be killed and relaunched — warn the user first.

---

## Step 3 — Identify New URLs

Parse the freshly written `reports\{base}\source\{base}.md`. Extract all URLs from the Corporate and Political/Macro sections.

Filter to **new only**: keep URLs not in `seen_urls`.

Show the user:
```
New URLs to summarize: {N}
Already processed (skipping): {M}

New items:
  1. [corporate]  https://...
  2. [poli/macro] https://...
```

If there are 0 new URLs, stop: `"Nothing new to summarize — all TAKE items are already in the data files."` Ask whether they want to re-run `/dedup-news` or are done.

---

## Step 4 — Fetch & Summarize New Items Only

For each new URL, fetch the full article content (same as `/summarize-news` Step 2) and write a KIS-style bilingual summary:

- Follow all writing rules from `/summarize-news` (max 60 words, data-first, bilingual, date prefix)
- Classify each new item: `corporate` or `economy_political_others`
- Validate with harness after each item (up to 3 retries per item)

---

## Step 5 — Append to Existing JSON Files

**Do NOT overwrite the existing files.** For each new item:

1. Read the current JSON file
2. Insert the new item into the correct sector/subtype `items` array
3. Increment `item_count`
4. Update `generated_at`
5. Write back

Set `"order"` to the next sequential integer within that sector/subtype.

---

## Step 6 — Confirm and Chain

Report:
```
✓ Delta complete
  New items added: {N}
  Total items now: {T}
  Files updated:
    reports\{base}\data\{base}_corporate.json
    reports\{base}\data\{base}_economy_political_others.json
```

Automatically invoke the `/dedup-news` skill.

---

## Notes

- Items with `url: ""` (vin_bank, manual_paste, macro, trading) are **never re-processed** — they have no URL to match against
- If the same URL appears in both corporate and poli sections of the sheet (unusual), process it once and classify by content
- This skill does not touch `macro.json` or `trading.json` — those come from deterministic sources, not TAKE rows
