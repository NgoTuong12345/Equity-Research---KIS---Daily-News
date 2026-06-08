#!/usr/bin/env python3
"""
Deduplicate KIS Daily News Report JSONs

Calculates Jaccard similarity across corporate, political, and policies news items
and removes semantic duplicates, keeping the one with the most detailed summary.

Usage:
    python scripts/deduplicate_reports.py mor_08_06_2026
"""
from __future__ import annotations

import json
import os
import re
import sys
import io
from pathlib import Path
from datetime import datetime

# Force stdout to UTF-8 to support Vietnamese characters on Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

def clean_text(text: str) -> set[str]:
    if not text:
        return set()
    text = re.sub(r"[^\w\s\-\.]", "", text.lower())
    words = [w.strip(".") for w in text.split() if w.strip(".")]
    return set(words)

def jaccard_similarity(set1: set[str], set2: set[str]) -> float:
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union

def get_duplicates_graph(items: list[dict], is_corporate: bool = True) -> list[set[int]]:
    """
    Returns groups of indices that are duplicates.
    """
    n = len(items)
    adj = {i: set() for i in range(n)}
    
    for i in range(n):
        for j in range(i + 1, n):
            item1 = items[i]
            item2 = items[j]
            
            # Clean summaries
            vn1 = clean_text(item1.get("summary_vn", ""))
            vn2 = clean_text(item2.get("summary_vn", ""))
            en1 = clean_text(item1.get("summary_en", ""))
            en2 = clean_text(item2.get("summary_en", ""))
            
            sim_vn = jaccard_similarity(vn1, vn2)
            sim_en = jaccard_similarity(en1, en2)
            avg_sim = (sim_vn + sim_en) / 2.0
            
            is_dup = False
            if is_corporate:
                t1 = item1.get("ticker", "N/A").strip().upper()
                t2 = item2.get("ticker", "N/A").strip().upper()
                
                # Check if tickers are valid and same (exclude generic unlisted/na/otc placeholders)
                is_valid_ticker = t1 != "N/A" and t1 != "" and t1 != "UNLISTED" and t1 != "OTC"
                same_ticker = is_valid_ticker and (t1 == t2)
                
                # Check if company names have significant token overlap
                c1 = clean_text(item1.get("company_vn", "") or item1.get("company_en", ""))
                c2 = clean_text(item2.get("company_vn", "") or item2.get("company_en", ""))
                # Remove generic stopwords from company names before comparison
                company_stopwords = {"công", "ty", "cổ", "phần", "tập", "đoàn", "trách", "nhiệm", "hữu", "hạn", "tnhh", "jsc", "corporation", "company", "group", "limited", "and", "vn"}
                c1_clean = {w for w in c1 if w not in company_stopwords}
                c2_clean = {w for w in c2 if w not in company_stopwords}
                
                # If they share at least 2 non-generic words in company name, they are likely the same company
                same_company = len(c1_clean.intersection(c2_clean)) >= 2 and len(c1_clean) > 0 and len(c2_clean) > 0
                
                if same_ticker or same_company:
                    # Same company/ticker: lower threshold is acceptable to merge redundant news (e.g. STB, VNZ)
                    if avg_sim >= 0.20 or sim_vn >= 0.24:
                        is_dup = True
                else:
                    # Different tickers: must be extremely high similarity to merge
                    if avg_sim >= 0.45 or sim_vn >= 0.50:
                        is_dup = True
            else:
                # Political/policies: compare within the same subtype or generally
                sub1 = item1.get("subtype_key", item1.get("subtype", ""))
                sub2 = item2.get("subtype_key", item2.get("subtype", ""))
                if sub1 == sub2:
                    if avg_sim >= 0.33 or sim_vn >= 0.38:
                        is_dup = True
                        
            if is_dup:
                adj[i].add(j)
                adj[j].add(i)
                
    # Find connected components (duplicate groups)
    visited = set()
    components = []
    for i in range(n):
        if i not in visited:
            comp = set()
            queue = [i]
            visited.add(i)
            while queue:
                curr = queue.pop(0)
                comp.add(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            if len(comp) > 1:
                components.append(comp)
    return components

def deduplicate_list(items: list[dict], is_corporate: bool) -> tuple[list[dict], list[str]]:
    if not items:
        return [], []
        
    components = get_duplicates_graph(items, is_corporate=is_corporate)
    
    # Map from index to keep / remove
    remove_indices = set()
    kept_items = []
    removed_logs = []
    
    # For each group of duplicates, find the best one to keep
    for comp in components:
        # Sort indices by summary length descending, keep the longest/most descriptive
        sorted_indices = sorted(list(comp), key=lambda idx: len(items[idx].get("summary_vn", "")), reverse=True)
        keep_idx = sorted_indices[0]
        
        for idx in sorted_indices[1:]:
            remove_indices.add(idx)
            removed_logs.append(
                f"Removed duplicate of {items[keep_idx].get('ticker', 'N/A')}: "
                f"'{items[idx].get('title_vn')}' (replaced by '{items[keep_idx].get('title_vn')}')"
            )
            
    for idx, item in enumerate(items):
        if idx not in remove_indices:
            kept_items.append(item)
            
    return kept_items, removed_logs

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/deduplicate_reports.py <base_name>")
        sys.exit(1)
        
    base = sys.argv[1]
    print(f"Running semantic deduplication on: {base}")
    
    corp_path = BASE_DIR / "reports" / base / "data" / f"{base}_corporate.json"
    epo_path = BASE_DIR / "reports" / base / "data" / f"{base}_economy_political_others.json"
    
    total_removed = 0
    
    # 1. Deduplicate Corporate News
    if corp_path.exists():
        with open(corp_path, "r", encoding="utf-8") as f:
            corp_data = json.load(f)
            
        # Flatten sectors to deduplicate globally or by sector
        # Globally is safer for different sector classifications of same ticker
        flat_corp_items = []
        for sector in corp_data.get("sectors", []):
            for item in sector.get("items", []):
                # Keep sector mapping in case we keep the item
                item["_sector_key"] = sector["sector_key"]
                flat_corp_items.append(item)
                
        cleaned_corp_items, removed_logs = deduplicate_list(flat_corp_items, is_corporate=True)
        
        if removed_logs:
            print(f"\n[CORPORATE] Removed {len(removed_logs)} duplicate items:")
            for log in removed_logs:
                print(f"  - {log}")
            total_removed += len(removed_logs)
        else:
            print("\n[CORPORATE] No duplicate items found.")
            
        # Re-group cleaned items by sector
        from collections import defaultdict
        corp_by_sector = defaultdict(list)
        for idx, item in enumerate(cleaned_corp_items):
            sec_key = item.pop("_sector_key")
            corp_by_sector[sec_key].append(item)
            
        # Reconstruct corporate structure
        new_sectors = []
        order_idx = 1
        for sector in corp_data.get("sectors", []):
            sec_key = sector["sector_key"]
            if sec_key in corp_by_sector:
                items_list = corp_by_sector[sec_key]
                for item in items_list:
                    item["order"] = order_idx
                    order_idx += 1
                new_sectors.append({
                    "sector_key": sec_key,
                    "section_title_vn": sector["section_title_vn"],
                    "section_title_en": sector["section_title_en"],
                    "items": items_list
                })
                
        corp_data["sectors"] = new_sectors
        corp_data["item_count"] = order_idx - 1
        corp_data["generated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")
        
        with open(corp_path, "w", encoding="utf-8") as f:
            json.dump(corp_data, f, ensure_ascii=False, indent=2)
            
    # 2. Deduplicate Economy/Political/Others News
    if epo_path.exists():
        with open(epo_path, "r", encoding="utf-8") as f:
            epo_data = json.load(f)
            
        flat_epo_items = []
        for subtype_data in epo_data.get("subtypes", []):
            subtype_key = subtype_data.get("subtype_key", subtype_data.get("subtype"))
            for item in subtype_data.get("items", []):
                item["_subtype_key"] = subtype_key
                flat_epo_items.append(item)
                
        cleaned_epo_items, removed_logs = deduplicate_list(flat_epo_items, is_corporate=False)
        
        if removed_logs:
            print(f"\n[ECONOMY/POLITICAL/OTHERS] Removed {len(removed_logs)} duplicate items:")
            for log in removed_logs:
                print(f"  - {log}")
            total_removed += len(removed_logs)
        else:
            print("\n[ECONOMY/POLITICAL/OTHERS] No duplicate items found.")
            
        # Re-group cleaned items by subtype
        from collections import defaultdict
        epo_by_subtype = defaultdict(list)
        for item in cleaned_epo_items:
            sub_key = item.pop("_subtype_key")
            epo_by_subtype[sub_key].append(item)
            
        # Reconstruct subtypes structure
        new_subtypes = []
        order_idx = 1
        for subtype_data in epo_data.get("subtypes", []):
            sub_key = subtype_data.get("subtype_key", subtype_data.get("subtype"))
            if sub_key in epo_by_subtype:
                items_list = epo_by_subtype[sub_key]
                for item in items_list:
                    item["order"] = order_idx
                    order_idx += 1
                new_subtypes.append({
                    "subtype": sub_key,
                    "subtype_key": sub_key,
                    "section_title_vn": subtype_data["section_title_vn"],
                    "section_title_en": subtype_data["section_title_en"],
                    "items": items_list
                })
                
        epo_data["subtypes"] = new_subtypes
        epo_data["item_count"] = order_idx - 1
        epo_data["generated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")
        
        with open(epo_path, "w", encoding="utf-8") as f:
            json.dump(epo_data, f, ensure_ascii=False, indent=2)
            
    print(f"\nDeduplication complete. Total duplicates removed: {total_removed}")

if __name__ == "__main__":
    main()
