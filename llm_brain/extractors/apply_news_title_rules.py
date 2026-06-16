#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core_tools" / "paths"))
from report_paths import find_data_file, find_latest_base

CATEGORIES = ("macro", "trading", "economy_political_others")


def prepare_titles(base: str) -> Path:
    items_to_title = []
    
    for category in CATEGORIES:
        path = find_data_file(base, category)
        if not path.exists():
            continue
            
        data = json.loads(path.read_text(encoding="utf-8"))
        
        # Helper to extract items
        def extract_items(item_list):
            for item in item_list:
                items_to_title.append({
                    "category": category,
                    "order": item.get("order"),
                    "ticker": item.get("ticker", ""),
                    "company_vn": item.get("company_vn", ""),
                    "company_en": item.get("company_en", ""),
                    "exchange": item.get("exchange", ""),
                    "title_vn_orig": item.get("title_vn", ""),
                    "title_en_orig": item.get("title_en", ""),
                    "summary_vn": item.get("summary_vn", ""),
                    "summary_en": item.get("summary_en", "")
                })

        if category in ("macro", "trading"):
            extract_items(data.get("items", []))
        elif category == "economy_political_others":
            for subtype in data.get("subtypes", []):
                extract_items(subtype.get("items", []))
                
    out_path = Path(__file__).resolve().parent.parent / "scratch" / f"{base}_to_title.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(items_to_title, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Prepared {len(items_to_title)} items for agent title generation at: {out_path}")
    return out_path


def merge_titles(base: str, agent_file: Path) -> list[Path]:
    if not agent_file.exists():
        print(f"ERROR: Agent title file not found: {agent_file}")
        sys.exit(1)
        
    agent_titles = json.loads(agent_file.read_text(encoding="utf-8"))
    
    # Build lookup dictionary: (category, order) -> {title_en, title_vn}
    title_lookup = {}
    for item in agent_titles:
        cat = item.get("category")
        order = item.get("order")
        if cat and order is not None:
            title_lookup[(cat, order)] = {
                "title_en": item.get("title_en", ""),
                "title_vn": item.get("title_vn", "")
            }
            
    changed = []
    
    for category in CATEGORIES:
        path = find_data_file(base, category)
        if not path.exists():
            continue
            
        original = path.read_text(encoding="utf-8")
        data = json.loads(original)
        
        def update_items(item_list):
            for item in item_list:
                key = (category, item.get("order"))
                if key in title_lookup:
                    item["title_en"] = title_lookup[key]["title_en"]
                    item["title_vn"] = title_lookup[key]["title_vn"]
                    
        if category in ("macro", "trading"):
            update_items(data.get("items", []))
        elif category == "economy_political_others":
            for subtype in data.get("subtypes", []):
                update_items(subtype.get("items", []))
                
        updated = json.dumps(data, ensure_ascii=False, indent=2)
        if updated != original.strip():
            path.write_text(updated + "\n", encoding="utf-8")
            changed.append(path)
            
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent-based news title standardization")
    parser.add_argument("base", nargs="?", default=None, help="Report base, e.g. mor_05_06_2026")
    parser.add_argument("--prepare", action="store_true", help="Extract titles to a JSON for the agent")
    parser.add_argument("--merge", action="store_true", help="Merge agent-generated titles back into reports")
    parser.add_argument("--agent-file", type=Path, default=None, help="Path to the agent generated titles JSON")
    args = parser.parse_args()

    base = args.base or find_latest_base()
    
    if args.prepare:
        prepare_titles(base)
    elif args.merge:
        agent_path = args.agent_file or Path(__file__).resolve().parent.parent / "scratch" / f"{base}_agent_titles.json"
        changed = merge_titles(base, agent_path)
        if changed:
            print(f"Applied title rules for {base}:")
            for path in changed:
                print(f"  {path}")
        else:
            print(f"No title changes needed for {base}.")
    else:
        print("ERROR: Deterministic title rules have been replaced by the agent workflow.")
        print(f"Run: python {Path(__file__).name} --prepare {base}")
        print("Then have the agent format the titles, and run again with --merge.")
        sys.exit(1)


if __name__ == "__main__":
    main()
