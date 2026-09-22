"""
Format agent helper: Generates bilingual summaries for trading news items.
"""
import json
import sys
from pathlib import Path

def format_item(item: dict) -> dict:
    ticker = item.get("ticker", "")
    name = item.get("name_vn", "")
    rel = item.get("relationship_vn", "")
    vol = item.get("change_volume", "")
    dates = item.get("date_range", "")

    date_str_vn = f" từ ngày {dates.replace('~', ' đến ')}" if dates else ""
    date_str_en = f" from {dates.replace('~', ' to ')}" if dates else ""
    rel_str_vn = f" ({rel})" if rel else ""
    rel_str_en = f" ({rel})" if rel else ""

    summary_vn = f"{ticker}: {name}{rel_str_vn} đăng ký mua {vol} quyền mua cổ phiếu{date_str_vn}."
    summary_en = f"{ticker}: {name}{rel_str_en} registered to purchase {vol} share purchase rights{date_str_en}."

    return {
        "order": item["order"],
        "summary_vn": summary_vn,
        "summary_en": summary_en
    }

def run(to_format_path: Path):
    items = json.loads(to_format_path.read_text(encoding="utf-8"))
    formatted = [format_item(item) for item in items]

    out_path = to_format_path.with_name(to_format_path.stem.replace("_to_format", "_agent_formatted") + ".json")
    out_path.write_text(json.dumps(formatted, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(formatted)} formatted items to {out_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
    else:
        import glob
        matches = sorted(glob.glob("phases/01_scrape/hsx_insider_trading_*_to_format.json"))
        p = Path(matches[-1]) if matches else None
    if p and p.exists():
        run(p)
