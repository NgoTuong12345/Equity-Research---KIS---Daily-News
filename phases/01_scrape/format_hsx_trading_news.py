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
    if isinstance(records, dict):
        records = list(records.values())
    
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
    to_format_file = input_path.with_name(input_path.stem.replace("_extracted", "") + "_to_format.json")
    if not agent_file.exists():
        print(f"ERROR: Agent output file not found: {agent_file}")
        print("Please run the agent formatter workflow first.")
        sys.exit(1)
        
    # Load ticker index for clean English company names
    tickers_dict = {}
    ticker_index_path = Path(__file__).resolve().parents[2] / "ticker_index.json"
    if ticker_index_path.exists():
        try:
            with open(ticker_index_path, "r", encoding="utf-8") as f:
                tickers_dict = json.load(f).get("tickers", {})
        except Exception as e:
            print(f"Warning: Failed to load ticker_index.json: {e}")

    formatted_items = json.loads(agent_file.read_text(encoding="utf-8"))
    to_format_map = {}
    if to_format_file.exists():
        to_format_items = json.loads(to_format_file.read_text(encoding="utf-8"))
        for tf in to_format_items:
            to_format_map[tf.get("order")] = tf
    
    # Reconstruct the final list with correct keys
    final_items = []
    for item in formatted_items:
        order_num = item.get("order")
        meta = to_format_map.get(order_num, {})
        
        ticker = (item.get("ticker") or meta.get("ticker", "")).strip().upper()
        exchange = item.get("exchange") or meta.get("exchange", "HSX")
        if exchange.upper() == "UPCOM":
            exchange = "UPCoM"

        ticker_info = tickers_dict.get(ticker, {})
        company_vn = item.get("company_vn") or ticker_info.get("company_vn") or meta.get("company_vn", "")
        company_en = item.get("company_en") or ticker_info.get("company_en")
        
        if not company_en:
            company_en = company_vn
            company_en = re.sub(r'Công ty CP|Công ty Cổ phần', 'JSC', company_en, flags=re.IGNORECASE)
            company_en = re.sub(r'Tổng Công ty', 'Corporation', company_en, flags=re.IGNORECASE)
            company_en = re.sub(r'Tập đoàn', 'Group', company_en, flags=re.IGNORECASE)
        
        item["ticker"] = ticker
        item["company_vn"] = company_vn
        item["company_en"] = company_en
        item["exchange"] = exchange
        
        # Build titles
        if ticker and company_vn:
            item["title_vn"] = f"{ticker}. ({company_vn}. {exchange})"
        elif ticker:
            item["title_vn"] = f"{ticker}. {exchange}"
        elif company_vn:
            item["title_vn"] = f"{company_vn}. {exchange}"
        else:
            item["title_vn"] = f"{exchange} Insider Trading"

        if ticker and company_en:
            item["title_en"] = f"{ticker}. ({company_en}. {exchange})"
        elif ticker:
            item["title_en"] = f"{ticker}. {exchange}"
        elif company_en:
            item["title_en"] = f"{company_en}. {exchange}"
        else:
            item["title_en"] = f"{exchange} Insider Trading"

        # Build clean bilingual summaries following canonical KIS trading prose rules
        raw_tx = meta.get("raw_transaction", {})
        name_vn = (meta.get("name_vn") or raw_tx.get("name") or "").strip()
        rel_raw = (meta.get("relationship_vn") or raw_tx.get("relationship") or "").strip()
        vol = str(meta.get("change_volume") or raw_tx.get("change_volume") or "0").strip()
        date_range = (meta.get("date_range") or raw_tx.get("date_range") or "").strip()
        action = (meta.get("action") or raw_tx.get("action") or "buy").strip().lower()

        # Helper translation functions
        def remove_diacritics(text):
            import unicodedata
            return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').replace('đ', 'd').replace('Đ', 'D')

        def format_date_vn(d_str):
            if not d_str: return ""
            m = re.match(r'(\d{2})/(\d{2})~(\d{2})/(\d{2})', d_str)
            if m: return f" từ ngày {m.group(1)}/{m.group(2)} đến ngày {m.group(3)}/{m.group(4)}"
            return f" từ ngày {d_str}"

        def format_date_en(d_str):
            if not d_str: return ""
            m = re.match(r'(\d{2})/(\d{2})~(\d{2})/(\d{2})', d_str)
            if m:
                months = {'01':'January','02':'February','03':'March','04':'April','05':'May','06':'June','07':'July','08':'August','09':'September','10':'October','11':'November','12':'December'}
                m1 = months.get(m.group(2), m.group(2))
                m2 = months.get(m.group(4), m.group(4))
                return f" from {m1} {m.group(1)} to {m2} {m.group(3)}"
            return f" from {d_str}"

        def get_salutation(name):
            if any(k in name for k in ['Công ty', 'Công đoàn', 'Tổ chức', 'Quỹ']):
                return '', ''
            if any(fn in name for fn in ['Thị', 'Lan', 'Diên', 'Thư']):
                return 'Bà ', 'Ms. '
            return 'Ông ', 'Mr. '

        def translate_rel(r):
            if not r: return 'người có liên quan đến người nội bộ', 'related person to internal person'
            if 'Giám đốc' in r and 'Phó' not in r and 'Tổng' not in r: return 'Giám đốc', 'Director'
            if 'Chủ tịch' in r: return 'Chủ tịch HĐQT', 'Chairman of the BOD'
            if 'TV HĐQT' in r or 'Thành viên HĐQT' in r: return 'Thành viên HĐQT', 'Board Member'
            if 'Trưởng' in r: return 'Trưởng BKS', 'Head of Supervisory Board'
            if 'Kế toán trưởng' in r: return 'Kế toán trưởng', 'Chief Accountant'
            if 'Người có liên quan' in r: return 'người có liên quan đến người nội bộ', 'related person to internal person'
            return r, remove_diacritics(r)

        def translate_entity_name(name):
            if 'Tân Thanh' in name: return 'Tan Thanh JSC'
            if 'Công đoàn' in name: return 'Company Trade Union'
            return remove_diacritics(name)

        sal_vn, sal_en = get_salutation(name_vn)
        name_en = translate_entity_name(name_vn)
        rel_vn_str, rel_en_str = translate_rel(rel_raw)

        act_vn = "đăng ký mua" if action in ["buy", "mua"] else "đăng ký bán"
        act_en = "registered to buy" if action in ["buy", "mua"] else "registered to sell"

        d_vn = format_date_vn(date_range)
        d_en = format_date_en(date_range)

        # Asset type
        asset_vn = "quyền mua cổ phiếu"
        asset_en = "share purchase rights"

        co_vn_full = company_vn or ticker_info.get("company_vn") or ticker
        co_en_full = company_en or ticker_info.get("company_en") or ticker

        if "summary_vn" not in item or not item["summary_vn"]:
            item["summary_vn"] = f"{sal_vn}{name_vn}, {rel_vn_str} {co_vn_full} ({ticker} - {exchange}), {act_vn} {vol} {asset_vn} {ticker}{d_vn}."
        if "summary_en" not in item or not item["summary_en"]:
            item["summary_en"] = f"{sal_en}{name_en}, {rel_en_str} of {co_en_full} ({ticker} - {exchange}), {act_en} {vol} {ticker} {asset_en}{d_en}."
        
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
