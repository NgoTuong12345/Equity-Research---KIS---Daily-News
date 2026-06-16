# Dedup & Edit News — Post-Summarization Review

Use this skill after `/summarize-news` completes, OR when the user runs `/dedup-news` directly.

## Purpose

1. Detect news items that duplicate stories already published in the past 30 days (semantic similarity via sentence-transformers)
2. Present the full item list with ⚠ flags on suspected duplicates
3. Let the user add, drop, or keep items (HITL editing)
4. Update the dedup index with confirmed items
5. Auto-chain to `/publish-news`

---

## Step 1 — Locate Current Session Files

Identify the current report base directory. It is the most recently modified directory under `reports/` that contains a `data/` subfolder. Confirm with the user if ambiguous.

```
BASE = reports/{base}/          e.g. reports/mor_20260616/
DATA = reports/{base}/data/     contains corporate.json, economy_political_others.json, macro.json, trading.json
```

---

## Step 2 — Run Semantic Dedup

```
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\dedup_engine.py reports\{base}\data --threshold 0.75
```

Parse the output. Collect:
- Total item count
- List of all items (numbered 1…N)
- Flagged items: their number, similarity score, matching past title, matching past date

---

## Step 3 — Present the List

Show a numbered list of ALL items across all JSON files. Format:

```
📋 {N} items ready — {F} flagged as potential duplicates

 1. [corporate]   VPB raises Q2 provision buffer by 12%
 2. [corporate]   ⚠ 88% — FPT wins cloud contract with MoIT
                  Past match: "FPT lands MoIT cloud deal worth $50M" (2026-06-15)
 3. [economy]     SBV holds benchmark rate at 4.5%
 4. [trading]     HSX: NVL insider buys 500,000 shares
...
```

Then ask:
```
Duplicate review options:
  drop-all   — remove all ⚠ flagged items automatically
  review     — go through each flagged item one by one
  keep-all   — keep everything (you'll edit below)

Your choice:
```

---

## Step 4 — Apply Duplicate Decisions

**drop-all**: Remove all flagged items from their respective JSON files.

**review**: For each flagged item, show:
```
⚠ Item 2: "FPT wins cloud contract with MoIT"
   Similarity: 88% match to "FPT lands MoIT cloud deal worth $50M" (2026-06-15)
   Keep or drop? (k/d):
```
Apply decision immediately before moving to next.

**keep-all**: No changes from dedup step.

After this step, re-number the list.

---

## Step 5 — HITL Editing

Show the current (post-dedup) numbered list and prompt:

```
✏️  Edit the list before publishing.
Commands:
  drop N            — remove item N
  add <url>         — fetch and summarize a new article, append to the list
  paste             — summarize raw text pasted directly into chat (no URL)
  edit N            — rewrite the summary for item N inline
  merge N M         — combine items N and M into one consolidated item
  done              — finalize and publish

>
```

Accept multiple commands in sequence. Apply each immediately and confirm:

- `drop 3` → "Dropped: [title]"
- `add https://...` → fetch article, summarize using KIS style rules, validate with harness, append to JSON, show as new item
- `paste` → prompt user to paste raw text; follow the `/paste-news` skill flow to classify, summarize, validate, and append
- `edit N` → show the current `summary_vn` and `summary_en` for item N; accept user's corrected text or ask the LLM to rewrite based on user instructions; validate the edited item with harness; update the JSON in place
- `merge N M` → show both items side by side; propose a merged bilingual summary combining the key facts from both; validate with harness; write merged item in place of item N; drop item M; re-number the list
- `done` → proceed to Step 6

---

## Step 6 — Update Dedup Index

After the user types `done`, add all remaining (kept) items to the index:

```
phases\01_scrape\venv\Scripts\python.exe phases\03_summarize\dedup_engine.py reports\{base}\data --add-to-index --report-id {base}
```

Confirm: "Index updated with {N} items."

---

## Step 7 — Auto-chain to Publish

Automatically invoke the `/publish-news` skill.
