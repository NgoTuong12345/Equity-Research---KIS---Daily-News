---
name: dedup-news
description: Perform agentic review and deduplication on news items, prompt human review/editing, and auto-chain to publish-news.
---

# Dedup & Edit News — Agentic Post-Summarization Review

Use this skill after `/summarize-news` completes, OR when the user runs `/dedup-news` directly.

## Purpose

1. **Intra-session Deduplication**: Detect news items within the current session that duplicate coverage (e.g., multiple portals reporting the same dividend, earnings release, contract, or policy decree).
2. **Cross-session Deduplication**: Detect stories that duplicate coverage already published in recent reports (e.g., this morning's bulletin or the previous day's report).
3. **Pure Agentic Review**: The LLM agent inspects news items directly within its reasoning context window (eliminating fragile vector embedding libraries, broken DLLs, and stale NPZ index files).
4. **Human-in-the-Loop (HITL) Editing**: Present the full numbered item list with descriptive `⚠` flags, letting the editor add, drop, edit, or merge stories.
5. **Auto-chain to `/publish-news`**.

---

## Step 1 — Locate Current Session & Recent Context

Identify the current report base directory:

```
BASE = reports/{base}/          e.g. reports/mor_21_09_2026/ or reports/after_21_09_2026/
DATA = reports/{base}/data/     contains corporate.json, economy_political_others.json, macro.json, trading.json
```

Identify the most recent prior report for cross-session comparison:
- If current is `after_DD_MM_YYYY`, inspect `reports/mor_DD_MM_YYYY/data/` (earlier today).
- If current is `mor_DD_MM_YYYY`, inspect the previous business day's most recent report directory under `reports/`.

Read the items from all 4 current category JSON files:
- `{base}_corporate.json` (flatten across `sectors[].items`)
- `{base}_economy_political_others.json` (flatten across `subtypes[].items`)
- `{base}_trading.json` (`items`)
- `{base}_macro.json` (`items`)

Also read items from the prior report's corporate and economy/political JSONs for cross-session awareness.

---

## Step 2 — Agentic Semantic & Entity Deduplication

Using your LLM reasoning context, analyze all current items and cross-check them against each other and against the prior session:

### 1. Corporate News Deduplication
- **Same Ticker Check**: Flag if two items share the same stock ticker (or parent entity, e.g. VIC vs VHM/VinSpeed) and describe the same corporate development (same dividend rate, same earnings figures, same bond issuance, same AGM resolution).
- **Same Company Check**: For unlisted/OTC companies sharing company names (ignoring legal stopwords like `Công ty`, `Cổ phần`, `Tập đoàn`), check if they report identical events.

### 2. Economy / Politics / Others News Deduplication
- **Policy & Decree Check**: Flag if multiple articles cover the same government decree, circular, Prime Minister directive, or ministry regulation.
- **Commodity / Market Check**: Flag redundant price reports covering the same commodity with duplicate numbers.

### 3. Cross-Session Recurrence Check
- Flag any current item that merely repeats a story already published in the previous edition (e.g. morning report) without substantial new facts or developments.

For each flagged item, record:
- The item number and category
- Confidence score (e.g. `85%`, `92%`, `100%`)
- Comparison match (e.g. `Matches Item 4 [corporate]` or `Matches previous report mor_21_09_2026`)
- Concise reason explaining the overlap (e.g. *"Both report Novaland 3rd public share offering"*)

---

## Step 3 — Present the Numbered List

Show a numbered list of ALL items across all categories (1…N). Highlight flagged items with clear callouts:

```
📋 {N} items ready — {F} flagged as potential duplicates

 1. [corporate]   VIB. (VIBBank. HSX) — VIB to pay 5% interim cash dividend
 2. [corporate]   ⚠ 90% — Novaland: Thông báo chào bán cổ phiếu ra công chúng đợt 3
                  Matches previous report (mor_21_09_2026, corporate item 14): Same public offering announcement
 3. [corporate]   FPT lands $50M cloud deal with MoIT
 4. [economy]     Giá vàng miếng SJC duy trì ở mức 144,6 - 147,6 triệu đồng/lượng
 5. [economy]     ⚠ 85% — Giá vàng SJC đi ngang quanh mức 147 triệu đồng
                  Matches Item 4: Redundant gold price update from different news portal
 6. [trading]     HSX: SSB insider sells 1,500,000 shares
...
```

Then prompt the user:
```
Duplicate review options:
  drop-all   — remove all ⚠ flagged items automatically
  review     — go through each flagged item one by one
  keep-all   — keep everything (you can edit below)

Your choice:
```

---

## Step 4 — Apply Duplicate Decisions

- **drop-all**: Automatically remove all `⚠` flagged items from their respective category JSON files.
- **review**: Prompt the user for each flagged item:
  ```
  ⚠ Item 2: "Novaland: Thông báo chào bán cổ phiếu ra công chúng đợt 3"
     Reason: Matches previous report mor_21_09_2026 (same offering details)
     Keep or drop? (k/d):
  ```
  Apply each decision immediately.
- **keep-all**: Retain all items without changes.

After drops are applied, re-number the list.

---

## Step 5 — Interactive HITL Editing

Present the clean numbered list and offer interactive editing commands:

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

Accept commands in sequence:
- `drop N` → Remove item from its JSON file.
- `add <url>` → Fetch article via `fetch_full_articles.py`, summarize in KIS style, validate with `harness.py`, append to JSON.
- `paste` → Follow `/paste-news` skill flow to summarize, validate, and append.
- `edit N` → Show current `summary_vn` and `summary_en`; accept user corrections or rewrite per instructions; validate with `harness.py`; update JSON in place.
- `merge N M` → Synthesize the key facts from both items into a single consolidated bilingual summary; validate with `harness.py`; replace item N and drop item M.
- `done` → Finalize JSON structures (re-index `order` and `item_count`).

---

## Step 6 — Finalize & Auto-chain to Publish

1. Ensure each modified JSON file has valid structure:
   - Sequential `order` indices (1..k)
   - Correct `item_count` matching actual item count
   - Updated `generated_at` timestamp
2. Automatically invoke the `/publish-news` skill to run schema validation and generate HTML/PDF/DOCX reports.
