#!/usr/bin/env python3
"""
Combine Subagent Chunks, Trading News, and Macro Sheet Data

This is a generic utility script that aggregates chunk news JSON files,
applies exchange mapping rules (such as defaulting unlisted companies to "Unlisted"),
incorporates macro and trading news, and generates the final 4 KIS category payloads.

Usage:
    python scripts/combine_chunks.py mor_08_06_2026
"""
from __future__ import annotations

import json
import os
import re
import sys
import io
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Force stdout to UTF-8 to support Vietnamese characters on Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Define directories
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
from summary_rules import SECTOR_TITLES, SUBTYPE_TITLES

def clean_ticker(ticker: str) -> str:
    return ticker.strip().upper() if ticker else ""

def get_recent_trading_items(base_dir: Path, current_base: str, count: int = 3) -> list:
    reports_dir = base_dir / "reports"
    if not reports_dir.exists():
        return []
    
    # List all subdirectories matching the pattern
    report_dirs = []
    for d in reports_dir.iterdir():
        if d.is_dir():
            m = re.match(r"^(mor|after)_(\d{2})_(\d{2})_(\d{4})$", d.name)
            if m:
                sess, dd, mm, yyyy = m.groups()
                try:
                    date_val = datetime(int(yyyy), int(mm), int(dd))
                    sess_val = 1 if sess == "after" else 0
                    report_dirs.append((date_val, sess_val, d.name))
                except ValueError:
                    continue
                    
    # Sort report dirs chronologically
    report_dirs.sort()
    
    # Find index of current_base
    curr_idx = -1
    for i, (_, _, name) in enumerate(report_dirs):
        if name == current_base:
            curr_idx = i
            break
            
    # Get up to `count` reports before current_base
    prev_reports = []
    if curr_idx != -1:
        prev_reports = [name for (_, _, name) in report_dirs[max(0, curr_idx - count):curr_idx]]
    else:
        # If current_base is not yet in the list, just take the last `count` reports
        prev_reports = [name for (_, _, name) in report_dirs[-count:]]
        
    recent_items = []
    for prev_base in prev_reports:
        trading_json_path = reports_dir / prev_base / "data" / f"{prev_base}_trading.json"
        if trading_json_path.exists():
            try:
                with open(trading_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    recent_items.extend(data.get("items", []))
            except Exception as e:
                print(f"WARNING: Failed to read previous trading report {trading_json_path}: {e}")
    return recent_items

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/combine_chunks.py <base_name> [session] [date]")
        print("Example: python scripts/combine_chunks.py mor_08_06_2026")
        sys.exit(1)
        
    base = sys.argv[1]
    
    # Auto-detect session and date from base name (e.g., mor_08_06_2026 or after_08_06_2026)
    session = "morning" if base.startswith("mor") else "afternoon"
    
    # Extract date in DD/MM/YYYY format
    date_match = re.search(r"(\d{2})_(\d{2})_(\d{4})", base)
    if date_match:
        date_str = f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}"
    else:
        date_str = datetime.now().strftime("%d/%m/%Y")
        
    # Allow command line overrides
    if len(sys.argv) > 2:
        session = sys.argv[2]
    if len(sys.argv) > 3:
        date_str = sys.argv[3]
        
    print(f"Combining chunks for report: {base}")
    print(f"  Detected Session: {session}")
    print(f"  Detected Date   : {date_str}")
    
    # 1. Load ticker index
    ticker_index_path = BASE_DIR / "ticker_index.json"
    if not ticker_index_path.exists():
        print(f"ERROR: Ticker index not found at {ticker_index_path}")
        sys.exit(1)
        
    with open(ticker_index_path, "r", encoding="utf-8") as f:
        ticker_index = json.load(f)
    tickers_dict = ticker_index.get("tickers", {})
    
    # 2. Load chunk files
    chunk_items = []
    source_dir = BASE_DIR / "reports" / base / "source"
    
    # Check both reports/{base}/source/ and root folder for chunks
    chunk_patterns = [
        source_dir / f"chunk_*.json",
        source_dir / f"{session[:3]}_chunk_*.json",
        source_dir / f"after_chunk_*.json",
        source_dir / f"mor_chunk_*.json",
        BASE_DIR / f"chunk_*.json",
        BASE_DIR / f"{session[:3]}_chunk_*.json",
        BASE_DIR / f"after_chunk_*.json",
        BASE_DIR / f"mor_chunk_*.json"
    ]
    
    found_chunk_files = []
    for pattern in chunk_patterns:
        matches = sorted(pattern.parent.glob(pattern.name))
        for m in matches:
            if m not in found_chunk_files:
                found_chunk_files.append(m)
                
    if not found_chunk_files:
        print("WARNING: No chunk files found. Only combining macro/trading if available.")
    else:
        print(f"Found chunk files to load:")
        for cf in found_chunk_files:
            print(f"  - {cf.relative_to(BASE_DIR) if cf.is_relative_to(BASE_DIR) else cf}")
            with open(cf, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    chunk_items.extend(data)
                elif isinstance(data, dict) and "items" in data:
                    chunk_items.extend(data["items"])
        print(f"Loaded {len(chunk_items)} items from chunks.")
        
    # 3. Load macro sheet data (morning runs only)
    macro_sheet_items = []
    if session == "morning":
        # Format date for filename
        date_file_str = date_str.replace("/", "_")
        macro_sheet_path = BASE_DIR / "reports" / base / "data" / f"macro_sheet_{date_file_str}.json"
        
        if macro_sheet_path.exists():
            with open(macro_sheet_path, "r", encoding="utf-8") as f:
                macro_sheet_items = json.load(f).get("items", [])
            print(f"Loaded {len(macro_sheet_items)} items from macro sheet.")
        else:
            print(f"WARNING: Macro sheet not found: {macro_sheet_path}")
            
    # Initialize category buckets
    macro_items = []
    trading_items = []
    corporate_items = []
    epo_items = []
    
    # 4. Load trading items from latest hsx_insider_trading_*_extracted_formatted.json
    trading_dir = BASE_DIR / "vietnam_news_scraper"
    trading_files = sorted(trading_dir.glob("hsx_insider_trading_*_extracted_formatted.json"))
    if trading_files:
        latest_trading_file = trading_files[-1]
        print(f"Loading trading items from: {latest_trading_file}")
        with open(latest_trading_file, "r", encoding="utf-8") as f:
            trading_data = json.load(f)
            raw_trading_items = trading_data.get("items", [])
            
        # Get recent trading items for deduplication
        recent_trading = get_recent_trading_items(BASE_DIR, base, count=3)
        trading_items = []
        for item in raw_trading_items:
            # Check if this item matches any recent transaction
            is_dup = False
            ticker = item.get("ticker", "").strip().upper()
            raw_tx = item.get("raw_transaction", {}) or {}
            tx_name = raw_tx.get("name", "").strip().lower()
            tx_action = raw_tx.get("action", "").strip().lower()
            tx_volume = raw_tx.get("change_volume")
            tx_range = raw_tx.get("date_range", "").strip()
            
            for prev in recent_trading:
                prev_ticker = prev.get("ticker", "").strip().upper()
                prev_raw = prev.get("raw_transaction", {}) or {}
                prev_name = prev_raw.get("name", "").strip().lower()
                prev_action = prev_raw.get("action", "").strip().lower()
                prev_volume = prev_raw.get("change_volume")
                prev_range = prev_raw.get("date_range", "").strip()
                
                # Check for equivalence
                if (ticker == prev_ticker and
                    tx_name == prev_name and
                    tx_action == prev_action and
                    tx_volume == prev_volume and
                    tx_range == prev_range):
                    print(f"Duplicate trading transaction detected and skipped: {ticker} | {tx_name} | {tx_action} | {tx_volume}")
                    is_dup = True
                    break
            if not is_dup:
                trading_items.append(item)
    else:
        print("WARNING: No formatted trading files found.")
        
    # 5. Process macro sheet items
    for item in macro_sheet_items:
        source_tab = item.get("source_tab", "")
        if source_tab == "macro":
            macro_items.append({
                "order": len(macro_items) + 1,
                "title_vn": item.get("title_vn", "").strip(),
                "title_en": item.get("title_en", "").strip(),
                "summary_vn": item.get("body_vn", "").strip(),
                "summary_en": item.get("body_en", "").strip(),
                "source": item.get("source", "Macro").strip() or "Macro",
                "url": "",
                "published": item.get("news_date", date_str)
            })
        elif source_tab == "vin_bank":
            news_cat = item.get("news_category", "").strip()
            if news_cat.upper() == "TCBS":
                news_cat = "TCX"
            # Check if news_cat is a listed ticker
            if news_cat in tickers_dict:
                ticker_info = tickers_dict[news_cat]
                co_vn = ticker_info.get("company_vn", "")
                co_en = ticker_info.get("company_en", "")
                exch = ticker_info.get("exchange", "")
                sec_key = ticker_info.get("sector_key", "")
                
                # Normalize exchange name spelling
                if exch.upper() == "UPCOM":
                    exch = "UPCoM"
                
                # Format corporate display titles
                title_vn = f"{news_cat}. ({co_vn}. {exch})"
                title_en = f"{news_cat}. ({co_en}. {exch})"
                
                corporate_items.append({
                    "ticker": news_cat,
                    "company_vn": co_vn,
                    "company_en": co_en,
                    "exchange": exch,
                    "sector_key": sec_key,
                    "title_vn": title_vn,
                    "title_en": title_en,
                    "summary_vn": item.get("body_vn", "").strip(),
                    "summary_en": item.get("body_en", "").strip(),
                    "source": item.get("source", "vin_bank").strip() or "vin_bank",
                    "url": "",
                    "published": item.get("news_date", date_str)
                })
            else:
                # Route non-ticker items
                subtype_key = "others"
                if news_cat.lower() in ("commodities", "commodity"):
                    subtype_key = "commodities"
                elif news_cat.lower() in ("macro", "economy"):
                    subtype_key = "economies_investments"
                    
                epo_items.append({
                    "subtype_key": subtype_key,
                    "title_vn": item.get("title_vn", "").strip(),
                    "title_en": item.get("title_en", "").strip(),
                    "summary_vn": item.get("body_vn", "").strip(),
                    "summary_en": item.get("body_en", "").strip(),
                    "source": item.get("source", "vin_bank").strip() or "vin_bank",
                    "url": "",
                    "published": item.get("news_date", date_str)
                })
                
    # 6. Process chunk items
    for item in chunk_items:
        cat = item.get("category", "")
        if cat == "corporate":
            ticker = item.get("ticker", "").strip()
            
            if ticker.upper() == "TCBS":
                ticker = "TCX"
                
            # Hard overrides for specific unlisted/private entities that have parent company mappings
            if ticker.lower() in ("vinspeed", "vin_speed"):
                ticker = "VIC"
                item["company_vn"] = "Vingroup"
                item["company_en"] = "Vingroup"
                item["exchange"] = "HSX"
                item["sector_key"] = "real_estate"
                
            ticker_info = tickers_dict.get(ticker, {})
            co_vn = ticker_info.get("company_vn", "") or item.get("company_vn", "")
            co_en = ticker_info.get("company_en", "") or item.get("company_en", "")
            exch = ticker_info.get("exchange", "") or item.get("exchange", "")
            sec_key = ticker_info.get("sector_key", "") or item.get("sector_key", "")
            
            # Normalize exchange name spelling
            if exch.upper() == "UPCOM":
                exch = "UPCoM"
                
            # Fallback exchange mapping rule for unlisted/private companies
            if ticker not in tickers_dict or ticker in ("VPL", "Vinpearl") or exch.upper() in ("UNLISTED", "OTC"):
                exch = "Unlisted"
                
            if not sec_key:
                sec_key = "financials"  # generic fallback
                
            title_vn = item.get("title_vn", "").strip()
            title_en = item.get("title_en", "").strip()
            
            corporate_items.append({
                "ticker": ticker,
                "company_vn": co_vn,
                "company_en": co_en,
                "exchange": exch,
                "sector_key": sec_key,
                "title_vn": title_vn,
                "title_en": title_en,
                "summary_vn": item.get("summary_vn", "").strip(),
                "summary_en": item.get("summary_en", "").strip(),
                "source": item.get("source", "").strip(),
                "url": item.get("url", "").strip(),
                "published": item.get("published", date_str)
            })
        elif cat == "economy_political_others":
            epo_items.append({
                "subtype_key": item.get("subtype_key", "others"),
                "title_vn": item.get("title_vn", "").strip(),
                "title_en": item.get("title_en", "").strip(),
                "summary_vn": item.get("summary_vn", "").strip(),
                "summary_en": item.get("summary_en", "").strip(),
                "source": item.get("source", "").strip(),
                "url": item.get("url", "").strip(),
                "published": item.get("published", date_str)
            })
            
    # 7. Group corporate by sector_key
    corp_by_sector = defaultdict(list)
    for idx, item in enumerate(corporate_items):
        sec_key = item["sector_key"]
        clean_item = {k: v for k, v in item.items() if k != "sector_key"}
        corp_by_sector[sec_key].append(clean_item)
        
    final_corp_sectors = []
    order_idx = 1
    for sec_key in sorted(corp_by_sector.keys()):
        items_list = corp_by_sector[sec_key]
        for it in items_list:
            it["order"] = order_idx
            order_idx += 1
        final_corp_sectors.append({
            "sector_key": sec_key,
            "section_title_vn": SECTOR_TITLES[sec_key]["vn"],
            "section_title_en": SECTOR_TITLES[sec_key]["en"],
            "items": items_list
        })
        
    # 8. Group EPO by subtype_key
    epo_by_subtype = defaultdict(list)
    for item in epo_items:
        sub_key = item["subtype_key"]
        clean_item = {k: v for k, v in item.items() if k != "subtype_key"}
        epo_by_subtype[sub_key].append(clean_item)
        
    final_epo_subtypes = []
    order_idx = 1
    subtype_order = ["commodities", "political", "policies", "economies_investments", "social", "international_relation", "others"]
    for k in epo_by_subtype.keys():
        if k not in subtype_order:
            subtype_order.append(k)
            
    for sub_key in subtype_order:
        if sub_key in epo_by_subtype:
            items_list = epo_by_subtype[sub_key]
            for it in items_list:
                it["order"] = order_idx
                order_idx += 1
            final_epo_subtypes.append({
                "subtype": sub_key,
                "subtype_key": sub_key,
                "section_title_vn": SUBTYPE_TITLES[sub_key]["vn"],
                "section_title_en": SUBTYPE_TITLES[sub_key]["en"],
                "items": items_list
            })
            
    generated_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")
    
    # 9. Create final JSON payloads
    macro_payload = {
        "report": base,
        "session": "mor" if session == "morning" else "after",
        "category": "macro",
        "section_title_vn": "KINH TẾ VĨ MÔ",
        "section_title_en": "Macroeconomics",
        "generated_at": generated_at,
        "item_count": len(macro_items),
        "items": macro_items
    }
    
    trading_payload = {
        "report": base,
        "session": "mor" if session == "morning" else "after",
        "category": "trading",
        "section_title_vn": "GIAO DỊCH",
        "section_title_en": "Trading",
        "generated_at": generated_at,
        "item_count": len(trading_items),
        "items": trading_items
    }
    
    corporate_payload = {
        "report": base,
        "session": "mor" if session == "morning" else "after",
        "category": "corporate",
        "section_title_vn": "DOANH NGHIỆP",
        "section_title_en": "Corporate News",
        "generated_at": generated_at,
        "item_count": len(corporate_items),
        "sectors": final_corp_sectors
    }
    
    epo_payload = {
        "report": base,
        "session": "mor" if session == "morning" else "after",
        "category": "economy_political_others",
        "section_title_vn": "KINH TẾ - CHÍNH TRỊ - KHÁC",
        "section_title_en": "Economy - Politics - Others",
        "generated_at": generated_at,
        "item_count": len(epo_items),
        "subtypes": final_epo_subtypes
    }
    
    # Save payloads
    data_dir = BASE_DIR / "reports" / base / "data"
    os.makedirs(data_dir, exist_ok=True)
    
    with open(data_dir / f"{base}_macro.json", "w", encoding="utf-8") as f:
        json.dump(macro_payload, f, ensure_ascii=False, indent=2)
        
    with open(data_dir / f"{base}_trading.json", "w", encoding="utf-8") as f:
        json.dump(trading_payload, f, ensure_ascii=False, indent=2)
        
    with open(data_dir / f"{base}_corporate.json", "w", encoding="utf-8") as f:
        json.dump(corporate_payload, f, ensure_ascii=False, indent=2)
        
    with open(data_dir / f"{base}_economy_political_others.json", "w", encoding="utf-8") as f:
        json.dump(epo_payload, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully saved KIS news reports to: {data_dir}")
    print(f"  Macro count   : {len(macro_items)}")
    print(f"  Trading count : {len(trading_items)}")
    print(f"  Corporate     : {len(corporate_items)}")
    print(f"  EPO News      : {len(epo_items)}")
    print(f"  Total news items combined: {len(macro_items) + len(trading_items) + len(corporate_items) + len(epo_items)}")

if __name__ == "__main__":
    main()
