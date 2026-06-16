"""
Format HSX agent extraction JSON into company trading-news prose.

This script acts as an orchestrator for the agent-driven translation workflow.
Deterministic dictionaries have been removed to allow the LLM agent to handle
long-tail unique names, organizations, and relationships reliably.

Workflow:
1. PREPARE: python format_hsx_trading_news.py --prepare hsx_insider_trading_*_extracted.json
   -> Deduplicates transactions and writes *_to_format.json

2. AGENT: The agent reads *_to_format.json, translates the fields, and generates 
   summary_vn and summary_en. It writes the result to *_agent_formatted.json.

3. MERGE: python format_hsx_trading_news.py --merge hsx_insider_trading_*_extracted.json
   -> Merges the agent's translations and writes the final outputs:
      *_extracted_formatted.json
      *_extracted_EN.txt
      *_extracted_VN.txt
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import io
import unicodedata
from pathlib import Path
from typing import Any

# Force stdout to UTF-8 to support Vietnamese characters on Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def normalize_text(value: Any) -> str:
    return unicodedata.normalize("NFC", str(value or "").strip())


def format_number(value: Any) -> str:
    if value in (None, ""):
        return "0"
    try:
        return f"{int(float(str(value).replace(',', ''))):,}"
    except (TypeError, ValueError):
        return str(value)


def clean_percentage(value: Any) -> str:
    text = normalize_text(value)
    if not text:
        return "0%"
    return text if text.endswith("%") else f"{text}%"


def transaction_key(record: dict[str, Any], tx: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        normalize_text(value).casefold()
        for value in (
            tx.get("ticker") or record.get("ticker"),
            tx.get("company_fullname"),
            tx.get("exchange") or record.get("source"),
            tx.get("date_range"),
            tx.get("name"),
            tx.get("relationship"),
            tx.get("action"),
            format_number(tx.get("change_volume")),
            format_number(tx.get("after_volume")),
            clean_percentage(tx.get("after_percentage")),
        )
    )


def prepare_for_agent(input_path: Path) -> Path:
    """Read extracted JSON, deduplicate transactions, and write _to_format.json."""
    records = json.loads(input_path.read_text(encoding="utf-8"))
    
    items_to_format = []
    seen = set()
    order = 1
    
    for record in records:
        for tx in record.get("transactions") or []:
            key = transaction_key(record, tx)
            if key in seen:
                continue
            seen.add(key)
            
            items_to_format.append({
                "order": order,
                "ticker": normalize_text(tx.get("ticker") or record.get("ticker")),
                "exchange": normalize_text(tx.get("exchange") or record.get("source") or "HSX"),
                "company_vn": normalize_text(tx.get("company_fullname")),
                "name_vn": normalize_text(tx.get("name")),
                "relationship_vn": normalize_text(tx.get("relationship")),
                "action": normalize_text(tx.get("action")),
                "change_volume": format_number(tx.get("change_volume")),
                "after_volume": format_number(tx.get("after_volume")),
                "after_percentage": clean_percentage(tx.get("after_percentage")),
                "date_range": normalize_text(tx.get("date_range")),
                "url": record.get("url", ""),
                "published": record.get("date", ""),
                "raw_transaction": tx
            })
            order += 1
            
    out_path = input_path.with_name(input_path.stem.replace("_extracted", "") + "_to_format.json")
    out_path.write_text(json.dumps(items_to_format, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Prepared {len(items_to_format)} unique transactions for agent formatting: {out_path}")
    return out_path


def merge_agent_results(input_path: Path):
    """Read agent's formatted JSON and write final formatted output and TXT files."""
    agent_file = input_path.with_name(input_path.stem.replace("_extracted", "") + "_agent_formatted.json")
    if not agent_file.exists():
        print(f"ERROR: Agent output file not found: {agent_file}")
        print("Please run the agent formatter workflow first.")
        sys.exit(1)
        
    formatted_items = json.loads(agent_file.read_text(encoding="utf-8"))
    
    # Reconstruct the final list with correct keys
    final_items = []
    for item in formatted_items:
        ticker = item.get("ticker", "")
        company_vn = item.get("company_vn", "")
        company_en = item.get("company_en", "")
        exchange = item.get("exchange", "HSX")
        
        # Ensure title fields exist
        if "title_vn" not in item:
            item["title_vn"] = f"{ticker}. ({company_vn}. {exchange})" if ticker and company_vn else f"{company_vn}. {exchange}"
        if "title_en" not in item:
            item["title_en"] = f"{ticker}. ({company_en}. {exchange})" if ticker and company_en else f"{company_en}. {exchange}"
        
        # Ensure source field exists for downstream
        if "source" not in item:
            item["source"] = exchange
            
        final_items.append(item)
        
    # Write final outputs
    payload = {
        "source_file": str(input_path),
        "category": "trading",
        "item_count": len(final_items),
        "items": final_items,
    }
    
    stem = re.sub(r"_extracted$", "", input_path.stem)
    json_out = input_path.with_name(f"{stem}_extracted_formatted.json")
    en_txt = input_path.with_name(f"{stem}_extracted_EN.txt")
    vn_txt = input_path.with_name(f"{stem}_extracted_VN.txt")
    
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    en_txt.write_text("\n".join(item.get("summary_en", "") for item in final_items), encoding="utf-8")
    vn_txt.write_text("\n".join(item.get("summary_vn", "") for item in final_items), encoding="utf-8")
    
    print(f"Formatted trading news saved to: {json_out}")
    print(f"Saved text files: {en_txt.name}, {vn_txt.name}")


def run_legacy_bypass(input_path: Path):
    """
    If no flags are provided, assume legacy behavior.
    If the agent formatted file exists, merge it. Otherwise, print an error instructing
    the user/agent to run --prepare.
    """
    agent_file = input_path.with_name(input_path.stem.replace("_extracted", "") + "_agent_formatted.json")
    if agent_file.exists():
        merge_agent_results(input_path)
    else:
        print("ERROR: Deterministic formatting has been removed.")
        print(f"Run: python {Path(__file__).name} --prepare {input_path.name}")
        print("Then have the agent format the data, and run again with --merge.")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Format HSX agent extraction JSON into trading-news prose")
    parser.add_argument("input", type=Path, help="Path to *_extracted.json")
    parser.add_argument("--prepare", action="store_true", help="Prepare deduplicated JSON for the agent")
    parser.add_argument("--merge", action="store_true", help="Merge agent-formatted JSON into final outputs")
    args = parser.parse_args()

    if args.prepare:
        prepare_for_agent(args.input)
    elif args.merge:
        merge_agent_results(args.input)
    else:
        run_legacy_bypass(args.input)


if __name__ == "__main__":
    main()
