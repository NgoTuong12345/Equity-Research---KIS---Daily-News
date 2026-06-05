# CLAUDE.md

Repository guide for Claude Code sessions in the HNX Insider Trading scraper workspace. Keep this file short; put repeatable behavior in scripts and tests.

## Role

Claude is the implementation and review agent for this project. Focus on insider trading extraction accuracy, parser correctness, database integrity, and careful maintenance of the PDF extraction pipeline.

Before starting substantive work:

1. Read the tail of `wiki/log.md` if it exists to catch recent handoffs.
2. Inspect representative PDFs, extracted JSON, database rows, or tests before changing parser behavior.
3. Confirm whether the task affects ingestion, PDF extraction, database loading, wiki generation, or test coverage.

After meaningful project work, append a short ledger entry to `wiki/log.md`:

```markdown
## [YYYY-MM-DD] [claude] <verb> | <slug> - <short description>
```

## Project

This project builds and maintains a scraper for insider trading disclosures from image-scanned and text-based PDFs.

The extraction goal is to turn Vietnamese disclosure PDFs into structured insider trading records: issuer ticker/name, insider name, insider role or relationship, transaction type, registered and executed share volumes, ownership before/after, transaction dates, disclosure dates, source PDF identifiers, and any notes needed to explain partial or failed transactions.

Operational layers:

- `raw/`: immutable local PDF disclosures, organized by year and issuer ticker.
- `raw/cbis/latest.sqlite`: SQLite database for extracted structured records. Important tables include `hsx_bond_news` and `bond_xref`.
- `wiki/`: Obsidian-compatible markdown profiles for issuers, instruments, and source-analysis notes.

## Pipeline

```text
Raw PDFs
  -> cbis/pipelines/pdf_extraction.py
  -> extracted JSON
  -> cbis/pipelines/disclosure_extract_load.py
  -> raw/cbis/latest.sqlite
  -> python -m cbis ingest-wiki
  -> wiki/
```

Core components:

- `cbis/hsx/client.py`: HSX API client for listed items and raw news feeds.
- `cbis/hsx/news_classifier.py`: classifies disclosures as `insider_trading`, `convertible_bond`, `public_bond`, or `other_bond`.
- `cbis/pipelines/pdf_extraction.py`: sends PDFs for extraction and writes JSON/database outputs.
- `cbis/pipelines/notebooklm_pdf_worker.py`: Playwright worker pool for bulk PDF extraction.
- `cbis/pipelines/disclosure_extract_load.py`: parses extraction JSON into normalized database rows.
- `cbis/cascade/hsx_xref.py`: links classified news items with extracted database records.
- `cbis/storage/db.py`: SQLite connection helpers.
- `cbis/storage/schema.sql`: database schema.

## Insider Trading Extraction

When working on extraction, preserve the chain from source document to structured record:

- Classify only relevant disclosure/news items as `insider_trading`; do not fold unrelated bond or corporate-action disclosures into insider records.
- Prefer explicit table values from the PDF over inferred values. If a field is missing, keep it null/empty rather than fabricating it.
- Track both registered and actual transaction volumes when present; many Vietnamese disclosures report planned volume, executed volume, and reason for non-completion separately.
- Keep insider identity fields separate from issuer identity fields. Names, roles, relationship labels, and ticker/company names should not be merged into one text blob.
- Preserve source traceability: every extracted row should be traceable to a source news item, attachment, PDF, or extracted JSON artifact.
- For scanned PDFs, check whether a text layer exists before assuming OCR is required. For OCR-heavy documents, validate against at least one visual sample or extracted text sample.
- Normalize dates and numeric volumes consistently before loading them into SQLite.

## Commands

Set up the environment:

```powershell
uv venv --python 3.11
uv pip install -e .
uv pip install pytest websockets
```

Run tests:

```powershell
uv run pytest
```

Regenerate wiki files after sync or database-loading work:

```powershell
python -m cbis ingest-wiki
```

## Karpathy Reasoning Guidelines

- Do not assume PDF layouts. Check sample documents, text layers, OCR output, or existing extracted JSON before changing parsing logic.
- Prefer simple, direct implementations: SQLite, standard-library parsing, and existing local helpers before adding new dependencies.
- Keep changes surgical. Preserve existing file layout, import style, and naming unless the task requires otherwise.
- Treat generated extraction outputs and local PDFs as data artifacts; avoid broad rewrites unless explicitly requested.
- For parser changes, define a concrete success case and verify with focused samples plus `uv run pytest`.
- Think before coding: state the expected input shape, inspect evidence, then change the smallest useful piece.
- If requirements are vague or document layouts are ambiguous, pause and ask for clarification instead of encoding guesses.
- Keep success criteria concrete, such as "all insider transactions from this sample PDF are captured with correct dates and volumes."
- Use diacritic-robust matching for Vietnamese text where classification or joins depend on text equality.
- Preserve Vietnamese output with NFC normalization. Replace Vietnamese lowercase/uppercase d-with-stroke characters as `d`/`D` before NFD decomposition when ASCII folding is required.

## Wiki Memory

Wiki structure:

- `wiki/issuers/<TICKER>.md`: issuer profiles.
- `wiki/instruments/<CODE>.md`: transaction metrics, insider names, volumes, and dates.
- `wiki/analysis/source-docs/`: probing notes, PDF pattern documentation, and technical logs.

Keep wiki updates derived from structured pipeline data where possible. If manual notes are added, make the source document and reasoning explicit.
