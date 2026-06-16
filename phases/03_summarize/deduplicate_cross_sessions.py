import json
import os
import re
import sys
import io
from pathlib import Path
from datetime import datetime

# Force stdout to UTF-8 to support Vietnamese characters on Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[2]

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

def is_duplicate(item1: dict, item2: dict, is_corporate: bool) -> bool:
    vn1 = clean_text(item1.get("summary_vn", ""))
    vn2 = clean_text(item2.get("summary_vn", ""))
    en1 = clean_text(item1.get("summary_en", ""))
    en2 = clean_text(item2.get("summary_en", ""))
    
    sim_vn = jaccard_similarity(vn1, vn2)
    sim_en = jaccard_similarity(en1, en2)
    avg_sim = (sim_vn + sim_en) / 2.0
    
    if is_corporate:
        t1 = item1.get("ticker", "N/A").strip().upper()
        t2 = item2.get("ticker", "N/A").strip().upper()
        
        is_valid_ticker = t1 != "N/A" and t1 != "" and t1 != "UNLISTED" and t1 != "OTC"
        same_ticker = is_valid_ticker and (t1 == t2)
        
        c1 = clean_text(item1.get("company_vn", "") or item1.get("company_en", ""))
        c2 = clean_text(item2.get("company_vn", "") or item2.get("company_en", ""))
        company_stopwords = {"công", "ty", "cổ", "phần", "tập", "đoàn", "trách", "nhiệm", "hữu", "hạn", "tnhh", "jsc", "corporation", "company", "group", "limited", "and", "vn"}
        c1_clean = {w for w in c1 if w not in company_stopwords}
        c2_clean = {w for w in c2 if w not in company_stopwords}
        
        same_company = len(c1_clean.intersection(c2_clean)) >= 2 and len(c1_clean) > 0 and len(c2_clean) > 0
        
        if same_ticker or same_company:
            if avg_sim >= 0.20 or sim_vn >= 0.24:
                return True
        else:
            if avg_sim >= 0.45 or sim_vn >= 0.50:
                return True
    else:
        sub1 = item1.get("subtype_key", item1.get("subtype", ""))
        sub2 = item2.get("subtype_key", item2.get("subtype", ""))
        if sub1 == sub2:
            if avg_sim >= 0.33 or sim_vn >= 0.38:
                return True
    return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/deduplicate_cross_sessions.py <morning_base> <afternoon_base>")
        sys.exit(1)
        
    mor_base = sys.argv[1]
    aft_base = sys.argv[2]
    
    print(f"Comparing afternoon ({aft_base}) against morning ({mor_base}) reports for duplicates...")
    
    mor_corp_path = BASE_DIR / "reports" / mor_base / "data" / f"{mor_base}_corporate.json"
    mor_epo_path = BASE_DIR / "reports" / mor_base / "data" / f"{mor_base}_economy_political_others.json"
    
    aft_corp_path = BASE_DIR / "reports" / aft_base / "data" / f"{aft_base}_corporate.json"
    aft_epo_path = BASE_DIR / "reports" / aft_base / "data" / f"{aft_base}_economy_political_others.json"
    
    total_removed = 0
    
    # 1. Deduplicate Corporate News
    if mor_corp_path.exists() and aft_corp_path.exists():
        with open(mor_corp_path, "r", encoding="utf-8") as f:
            mor_corp_data = json.load(f)
        with open(aft_corp_path, "r", encoding="utf-8") as f:
            aft_corp_data = json.load(f)
            
        mor_corp_items = []
        for sector in mor_corp_data.get("sectors", []):
            mor_corp_items.extend(sector.get("items", []))
            
        new_sectors = []
        order_idx = 1
        removed_corporate_items = []
        
        for sector in aft_corp_data.get("sectors", []):
            new_items = []
            for item in sector.get("items", []):
                # Check against all morning corporate items
                duplicate_found = False
                matched_item = None
                for m_item in mor_corp_items:
                    if is_duplicate(item, m_item, is_corporate=True):
                        duplicate_found = True
                        matched_item = m_item
                        break
                
                if duplicate_found:
                    removed_corporate_items.append(
                        f"Removed duplicate of {item.get('ticker', 'N/A')} in afternoon: "
                        f"'{item.get('title_vn')}' (already in morning report: '{matched_item.get('title_vn')}')"
                    )
                    total_removed += 1
                else:
                    new_items.append(item)
            
            if new_items:
                for item in new_items:
                    item["order"] = order_idx
                    order_idx += 1
                new_sectors.append({
                    "sector_key": sector["sector_key"],
                    "section_title_vn": sector["section_title_vn"],
                    "section_title_en": sector["section_title_en"],
                    "items": new_items
                })
                
        if removed_corporate_items:
            print(f"\n[CORPORATE] Removed {len(removed_corporate_items)} cross-session duplicate(s):")
            for log in removed_corporate_items:
                print(f"  - {log}")
            aft_corp_data["sectors"] = new_sectors
            aft_corp_data["item_count"] = order_idx - 1
            aft_corp_data["generated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")
            
            with open(aft_corp_path, "w", encoding="utf-8") as f:
                json.dump(aft_corp_data, f, ensure_ascii=False, indent=2)
        else:
            print("\n[CORPORATE] No cross-session duplicates found.")

    # 2. Deduplicate Economy/Political/Others News
    if mor_epo_path.exists() and aft_epo_path.exists():
        with open(mor_epo_path, "r", encoding="utf-8") as f:
            mor_epo_data = json.load(f)
        with open(aft_epo_path, "r", encoding="utf-8") as f:
            aft_epo_data = json.load(f)
            
        mor_epo_items = []
        for subtype in mor_epo_data.get("subtypes", []):
            mor_epo_items.extend(subtype.get("items", []))
            
        new_subtypes = []
        order_idx = 1
        removed_epo_items = []
        
        for subtype in aft_epo_data.get("subtypes", []):
            new_items = []
            for item in subtype.get("items", []):
                # Check against all morning EPO items
                duplicate_found = False
                matched_item = None
                for m_item in mor_epo_items:
                    if is_duplicate(item, m_item, is_corporate=False):
                        duplicate_found = True
                        matched_item = m_item
                        break
                
                if duplicate_found:
                    removed_epo_items.append(
                        f"Removed duplicate of subtype '{subtype.get('subtype_key')}' in afternoon: "
                        f"'{item.get('title_vn')}' (already in morning report: '{matched_item.get('title_vn')}')"
                    )
                    total_removed += 1
                else:
                    new_items.append(item)
            
            if new_items:
                for item in new_items:
                    item["order"] = order_idx
                    order_idx += 1
                new_subtypes.append({
                    "subtype": subtype["subtype"],
                    "subtype_key": subtype["subtype_key"],
                    "section_title_vn": subtype["section_title_vn"],
                    "section_title_en": subtype["section_title_en"],
                    "items": new_items
                })
                
        if removed_epo_items:
            print(f"\n[ECONOMY/POLITICAL/OTHERS] Removed {len(removed_epo_items)} cross-session duplicate(s):")
            for log in removed_epo_items:
                print(f"  - {log}")
            aft_epo_data["subtypes"] = new_subtypes
            aft_epo_data["item_count"] = order_idx - 1
            aft_epo_data["generated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")
            
            with open(aft_epo_path, "w", encoding="utf-8") as f:
                json.dump(aft_epo_data, f, ensure_ascii=False, indent=2)
        else:
            print("\n[ECONOMY/POLITICAL/OTHERS] No cross-session duplicates found.")
            
    print(f"\nCross-session deduplication complete. Total duplicates removed: {total_removed}")

if __name__ == "__main__":
    main()
