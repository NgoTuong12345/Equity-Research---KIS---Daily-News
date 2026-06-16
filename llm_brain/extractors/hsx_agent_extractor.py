"""
HSX Insider Trading — Agent-Based Extractor

Reads the manifest produced by hsx_prepare_pdfs.py (or auto-generates it),
then provides helpers for the AI agent to extract transaction data from
each PDF's rendered images and write the final _extracted.json.

The AI agent reads images directly using its vision capabilities.

Pipeline:
  1. phases/01_scrape/hsx_insider_scraper.py  → hsx_insider_trading_*.json
  2. phases/01_scrape/hsx_prepare_pdfs.py     → downloads PDFs, renders images, writes manifest
  3. hsx_agent_extractor.py                   → agent reads images, writes *_extracted.json
  4. phases/01_scrape/format_hsx_trading_news.py → --prepare → agent → --merge → *_extracted_formatted.json

Usage (from agent workflow — all paths relative to project root):
  Step 1: Run preparation
    phases/01_scrape/venv/Scripts/python.exe phases/01_scrape/hsx_prepare_pdfs.py

  Step 2: Agent reads each article's images and extracts transactions
    (The agent reads each PNG from phases/01_scrape/pdf_images/ using Read tool)

  Step 3: Write results (pass explicit --manifest and --results paths)
    phases/01_scrape/venv/Scripts/python.exe llm_brain/extractors/hsx_agent_extractor.py --manifest PATH --results PATH
"""
from __future__ import annotations

import argparse
import glob
import json
import logging
import sys
import unicodedata
import re
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

SCRAPE_DIR = Path(__file__).resolve().parents[2] / "phases" / "01_scrape"

# The extraction prompt — same fields as the old NLM extractor for compatibility
EXTRACTION_FIELDS = """
Extract ALL insider/related-party stock transaction notifications from this document.

For each transaction, extract these 10 fields:
1. "ticker"           - Stock symbol (e.g., "NAB")
2. "name"             - Full name of the transacting person
3. "relationship"     - Position/relationship IN VIETNAMESE exactly as written
4. "action"           - "buy" or "sell"
5. "change_volume"    - Number of shares to trade (integer)
6. "after_volume"     - Total shares after transaction (integer, or null if not stated)
7. "after_percentage" - Ownership % after transaction (e.g., "0.0%", or null)
8. "date_range"       - Transaction period in MM/DD~MM/DD format
9. "company_fullname" - Full company name in Vietnamese
10. "exchange"        - "HSX", "HNX", or "UPCoM"

Rules:
- Vietnamese text must be NFC-normalized
- Output JSON: {"transactions": [...]}
- If multiple people/transactions in one document, list them all
- For ESOP or group filings, extract each person's transaction separately
"""


def find_latest_json() -> Optional[Path]:
    """Find the latest hsx_insider_trading_*.json (excluding derived files)."""
    matches = [
        p for p in sorted(glob.glob(str(SCRAPE_DIR / "hsx_insider_trading_*.json")))
        if not p.endswith("_extracted.json")
        and not p.endswith("_formatted.json")
        and not p.endswith("_manifest.json")
    ]
    return Path(matches[-1]) if matches else None


def find_latest_manifest() -> Optional[Path]:
    """Find the latest manifest JSON."""
    matches = sorted(glob.glob(str(SCRAPE_DIR / "hsx_insider_trading_*_manifest.json")))
    return Path(matches[-1]) if matches else None


def clean_json(raw: str) -> Optional[dict]:
    """Parse JSON from agent response, handling markdown fences and noise."""
    raw = unicodedata.normalize("NFC", raw)
    # Remove citation brackets like [1], [2]
    raw = re.sub(r"\[\d+\]", "", raw)
    # Remove markdown fences
    raw = re.sub(r"```[a-z]*\n?", "", raw)

    # Find the first valid JSON object
    start_idx = 0
    while True:
        pos = raw.find("{", start_idx)
        if pos == -1:
            break
        count, end_pos = 0, -1
        in_string = escape = False
        for i in range(pos, len(raw)):
            c = raw[i]
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"':
                in_string = not in_string
                continue
            if not in_string:
                if c == '{':
                    count += 1
                elif c == '}':
                    count -= 1
                    if count == 0:
                        end_pos = i
                        break
        if end_pos != -1:
            try:
                return json.loads(raw[pos:end_pos + 1])
            except json.JSONDecodeError:
                pass
        start_idx = pos + 1
    return None


def save_extracted(source_json_path: Path, records: list, results: dict):
    """
    Merge extraction results into the original records and save _extracted.json.

    Args:
        source_json_path: Path to the original hsx_insider_trading_*.json
        records: Original scraper records
        results: Dict mapping article_id -> {"transactions": [...]}
    """
    for rec in records:
        aid = rec.get("article_id")
        # Try both int and str keys (JSON serialization converts int keys to strings)
        extracted = results.get(aid) or results.get(str(aid))
        if extracted:
            if isinstance(extracted, dict):
                rec["transactions"] = extracted.get("transactions", [])
            elif isinstance(extracted, list):
                # If agent returned a flat list of transactions
                rec["transactions"] = extracted
            else:
                rec["transactions"] = []
        elif "transactions" not in rec:
            rec["transactions"] = []

    out_path = source_json_path.with_name(source_json_path.stem + "_extracted.json")
    out_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    n_with_tx = sum(1 for r in records if r.get("transactions"))
    log.info(f"Saved {out_path} — {n_with_tx}/{len(records)} records have transactions")
    return out_path


def load_and_save(manifest_path: Path = None, results_path: Path = None):
    """
    Load extraction results from a JSON file and merge into the source data.
    Called after the agent has processed all images and saved results.
    """
    if not manifest_path:
        manifest_path = find_latest_manifest()
    if not manifest_path or not manifest_path.exists():
        log.error("No manifest found. Run hsx_prepare_pdfs.py first.")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Find the source JSON
    source_stem = manifest_path.stem.replace("_manifest", "")
    source_path = manifest_path.with_name(source_stem + ".json")
    if not source_path.exists():
        log.error(f"Source JSON not found: {source_path}")
        sys.exit(1)

    records = json.loads(source_path.read_text(encoding="utf-8"))

    # Load results
    if results_path and results_path.exists():
        results = json.loads(results_path.read_text(encoding="utf-8"))
    else:
        # Look for _agent_results.json next to manifest
        results_path = manifest_path.with_name(source_stem + "_agent_results.json")
        if results_path.exists():
            results = json.loads(results_path.read_text(encoding="utf-8"))
        else:
            log.error(f"No results file found. Expected: {results_path}")
            sys.exit(1)

    save_extracted(source_path, records, results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HSX agent extractor — merge results")
    parser.add_argument("--manifest", type=Path, default=None, help="Path to manifest JSON")
    parser.add_argument("--results", type=Path, default=None, help="Path to agent results JSON")
    args = parser.parse_args()
    load_and_save(manifest_path=args.manifest, results_path=args.results)
