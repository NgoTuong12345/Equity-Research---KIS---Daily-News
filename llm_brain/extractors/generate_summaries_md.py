import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core_tools" / "paths"))
from project_root import PROJECT_ROOT as BASE_DIR

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_summaries_md.py <base>")
        sys.exit(1)
        
    base = sys.argv[1]
    data_dir = BASE_DIR / "reports" / base / "data"
    summaries_dir = BASE_DIR / "reports" / base / "summaries"
    os.makedirs(summaries_dir, exist_ok=True)
    
    # Load JSON files
    try:
        with open(data_dir / f"{base}_macro.json", "r", encoding="utf-8") as f:
            macro = json.load(f)
        with open(data_dir / f"{base}_trading.json", "r", encoding="utf-8") as f:
            trading = json.load(f)
        with open(data_dir / f"{base}_corporate.json", "r", encoding="utf-8") as f:
            corporate = json.load(f)
        with open(data_dir / f"{base}_economy_political_others.json", "r", encoding="utf-8") as f:
            epo = json.load(f)
    except Exception as e:
        print(f"Error loading JSON data for base {base}: {e}")
        sys.exit(1)
        
    # Generate VN Summary
    vn_lines = [f"# Tóm tắt tin tức — {base} (Tiếng Việt)", ""]
    
    # Macro
    if macro.get("items"):
        vn_lines.append("## KINH TẾ VĨ MÔ")
        for item in macro["items"]:
            vn_lines.append(item.get("summary_vn", ""))
            vn_lines.append("")
            
    # Corporate (grouped by sector)
    corp_items_vn = []
    for sector in corporate.get("sectors", []):
        for item in sector.get("items", []):
            corp_items_vn.append(item.get("summary_vn", ""))
            
    if corp_items_vn:
        vn_lines.append("## DOANH NGHIỆP")
        for summary in corp_items_vn:
            vn_lines.append(summary)
            vn_lines.append("")
            
    # Trading
    if trading.get("items"):
        vn_lines.append("## GIAO DỊCH")
        for item in trading["items"]:
            vn_lines.append(item.get("summary_vn", ""))
            vn_lines.append("")
            
    # Economy / Political / Others (grouped by subtype)
    epo_items_vn = []
    active_subtypes_vn = []
    for subtype in epo.get("subtypes", []):
        if subtype.get("items"):
            active_subtypes_vn.append(subtype.get("section_title_vn", "").upper())
            for item in subtype["items"]:
                epo_items_vn.append(item.get("summary_vn", ""))
                
    if epo_items_vn:
        title = " / ".join(active_subtypes_vn) if active_subtypes_vn else "VĨ MÔ & KHÁC"
        vn_lines.append(f"## {title}")
        for summary in epo_items_vn:
            vn_lines.append(summary)
            vn_lines.append("")
            
    # Save VN Summary
    with open(summaries_dir / f"{base}_summary_vn.md", "w", encoding="utf-8") as f:
        f.write("\n".join(vn_lines))
        
    # Generate EN Summary
    en_lines = [f"# News Summary — {base} (English)", ""]
    
    # Macro
    if macro.get("items"):
        en_lines.append("## MACROECONOMICS")
        for item in macro["items"]:
            en_lines.append(item.get("summary_en", ""))
            en_lines.append("")
            
    # Corporate
    corp_items_en = []
    for sector in corporate.get("sectors", []):
        for item in sector.get("items", []):
            corp_items_en.append(item.get("summary_en", ""))
            
    if corp_items_en:
        en_lines.append("## CORPORATE")
        for summary in corp_items_en:
            en_lines.append(summary)
            en_lines.append("")
            
    # Trading
    if trading.get("items"):
        en_lines.append("## TRADING")
        for item in trading["items"]:
            en_lines.append(item.get("summary_en", ""))
            en_lines.append("")
            
    # Economy / Political / Others
    epo_items_en = []
    active_subtypes_en = []
    for subtype in epo.get("subtypes", []):
        if subtype.get("items"):
            active_subtypes_en.append(subtype.get("section_title_en", "").upper())
            for item in subtype["items"]:
                epo_items_en.append(item.get("summary_en", ""))
                
    if epo_items_en:
        title = " / ".join(active_subtypes_en) if active_subtypes_en else "MACRO & OTHERS"
        en_lines.append(f"## {title}")
        for summary in epo_items_en:
            en_lines.append(summary)
            en_lines.append("")
            
    # Save EN Summary
    with open(summaries_dir / f"{base}_summary_en.md", "w", encoding="utf-8") as f:
        f.write("\n".join(en_lines))
        
    print(f"Bilingual summaries written to {summaries_dir}")

if __name__ == "__main__":
    main()
