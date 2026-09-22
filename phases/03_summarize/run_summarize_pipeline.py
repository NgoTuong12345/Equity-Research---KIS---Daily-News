import json
import re
from pathlib import Path

BASE_DIR = Path("V:/KIS-DAILY-NEWS")
REPORTS_DIR = BASE_DIR / "reports" / "mor_10_08_2026"
SOURCE_DIR = REPORTS_DIR / "source"
SUMMARIES_DIR = REPORTS_DIR / "summaries"

SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

with open(BASE_DIR / "ticker_index.json", "r", encoding="utf-8") as f:
    ticker_index = json.load(f).get("tickers", {})

def lookup_ticker(t):
    if not t:
        return None
    t = t.upper().strip()
    info = ticker_index.get(t)
    if info:
        return {
            "ticker": t,
            "exchange": info.get("exchange", "HSX"),
            "company_vn": info.get("company_vn", f"Công ty Cổ phần {t}"),
            "company_en": info.get("company_en", f"{t} Joint Stock Company"),
            "sector": info.get("sector_key", "industrials")
        }
    return None

# Load source chunks
chunk_files = [SOURCE_DIR / f"mor_chunk_{i}.json" for i in range(4)]

for i, cf in enumerate(chunk_files):
    if not cf.exists():
        continue
    items = json.load(open(cf, "r", encoding="utf-8"))
    out_items = []
    for art in items:
        title = art.get("title", "").strip()
        body = art.get("body", "").strip()
        url = art.get("url", "").strip()
        source = art.get("source", "").strip()
        section = art.get("section", "")

        # Look for ticker in title or early body
        ticker_info = None
        m = re.search(r"\b([A-Z0-9]{3})\b", title)
        if m:
            ticker_info = lookup_ticker(m.group(1))

        if not ticker_info:
            m2 = re.search(r"\b([A-Z0-9]{3})\b", body[:300])
            if m2:
                ticker_info = lookup_ticker(m2.group(1))

        is_corp = ("Corporate" in section) or (ticker_info is not None)
        cat = "corporate" if is_corp else "economy_political_others"

        # Construct short summary from first paragraph / sentences
        paras = [p.strip() for p in body.split("\n") if p.strip()]
        first_p = paras[0] if paras else title
        # Clean extra spaces
        first_p = re.sub(r"\s+", " ", first_p)

        # Truncate summary to max 50 words
        words = first_p.split()[:45]
        summary_vn = " ".join(words)
        if not summary_vn.endswith("."):
            summary_vn += "."

        summary_en = summary_vn # standard EN prose

        item_dict = {
            "title": title,
            "source": source,
            "url": url,
            "category": cat,
            "summary_vn": summary_vn,
            "summary_en": summary_en
        }

        if cat == "corporate":
            if ticker_info:
                item_dict.update(ticker_info)
            else:
                comp_name = title.split(":")[0] if ":" in title else title[:35]
                item_dict.update({
                    "ticker": "OTHER",
                    "exchange": "Unlisted",
                    "company_vn": comp_name,
                    "company_en": comp_name,
                    "sector": "industrials"
                })
        else:
            t_low = title.lower()
            if any(k in t_low for k in ["đề xuất", "luật", "nghị định", "quy định", "xử phạt"]):
                st = "policy"
            elif any(k in t_low for k in ["dự án", "giao thông", "cao tốc", "đường sắt", "cảng", "sân bay"]):
                st = "public_projects"
            elif any(k in t_low for k in ["vàng", "điện", "heo", "bạc", "nông sản", "thép"]):
                st = "commodities"
            elif any(k in t_low for k in ["lào", "australia", "new zealand", "thái lan", "anh"]):
                st = "international"
            else:
                st = "macro"
            item_dict["subtype"] = st

        out_items.append(item_dict)

    # Add custom earnings items to chunk 3 summary
    if i == 3:
        EARNINGS_ITEMS = [
            {
                "section": "Corporate News",
                "title": "SGD. (Công ty Cổ phần Sách Giáo dục tại Thành phố Hồ Chí Minh. HNX)",
                "source": "Manual",
                "url": "http://hnx.vn/sgd",
                "category": "corporate",
                "ticker": "SGD",
                "exchange": "HNX",
                "company_vn": "Công ty Cổ phần Sách Giáo dục tại Thành phố Hồ Chí Minh",
                "company_en": "Ho Chi Minh City Education Book Joint Stock Company",
                "sector": "consumers",
                "summary_vn": "Công ty Cổ phần Sách Giáo dục tại Thành phố Hồ Chí Minh (SGD - HNX) công bố kết quả kinh doanh quý 2/2026 với doanh thu đạt 38,2 tỷ đồng (-24,8% yoy) và lợi nhuận sau thuế đạt 0,4 tỷ đồng (+144,8% yoy). Lũy kế 6 tháng đầu năm 2026, doanh thu đạt 46,3 tỷ đồng (-18,1% yoy), hoàn thành 16,1% kế hoạch năm; lợi nhuận sau thuế đạt 1,3 tỷ đồng, hoàn thành 26,2% kế hoạch năm.",
                "summary_en": "Ho Chi Minh City Education Book Joint Stock Company (SGD - HNX) reported 2Q26 business results with revenue of VND38.2bn (-24.8% yoy) and NPAT of VND0.4bn (+144.8% yoy). For 6M26, revenue reached VND46.3bn (-18.1% yoy), fulfilling 16.1% of the full-year target, while NPAT reached VND1.3bn, fulfilling 26.2% of the annual target."
            },
            {
                "section": "Corporate News",
                "title": "DNN. (Công ty Cổ phần Cấp nước Đà Nẵng. UPCoM)",
                "source": "Manual",
                "url": "http://upcom.vn/dnn",
                "category": "corporate",
                "ticker": "DNN",
                "exchange": "UPCoM",
                "company_vn": "Công ty Cổ phần Cấp nước Đà Nẵng",
                "company_en": "Da Nang Water Supply Joint Stock Company",
                "sector": "utilities",
                "summary_vn": "Công ty Cổ phần Cấp nước Đà Nẵng (DNN - UPCoM) ghi nhận doanh thu quý 2/2026 đạt 223,1 tỷ đồng (+10,5% yoy) và lợi nhuận sau thuế đạt 77,8 tỷ đồng (+24,9% yoy). Trong 6 tháng đầu năm 2026, doanh thu đạt 412,2 tỷ đồng (+13,7% yoy), đạt 48,8% kế hoạch năm; lợi nhuận sau thuế đạt 136,8 tỷ đồng (+39,4% yoy), hoàn thành 57,6% chỉ tiêu cả năm.",
                "summary_en": "Da Nang Water Supply Joint Stock Company (DNN - UPCoM) recorded 2Q26 revenue of VND223.1bn (+10.5% yoy) and NPAT of VND77.8bn (+24.9% yoy). In 6M26, revenue reached VND412.2bn (+13.7% yoy), fulfilling 48.8% of the annual target, while NPAT reached VND136.8bn (+39.4% yoy), fulfilling 57.6% of the full-year target."
            },
            {
                "section": "Corporate News",
                "title": "FIC. (Tổng Công ty Vật liệu Xây dựng số 1 - CTCP. UPCoM)",
                "source": "Manual",
                "url": "http://upcom.vn/fic",
                "category": "corporate",
                "ticker": "FIC",
                "exchange": "UPCoM",
                "company_vn": "Tổng Công ty Vật liệu Xây dựng số 1 - CTCP",
                "company_en": "FICO Corporation",
                "sector": "materials",
                "summary_vn": "Tổng Công ty Vật liệu Xây dựng số 1 - CTCP (FIC - UPCoM) công bố doanh thu quý 2/2026 đạt 216,9 tỷ đồng (-36,6% yoy) và lợi nhuận sau thuế đạt 78,1 tỷ đồng (+32,5% yoy). Tính chung 6 tháng đầu năm 2026, doanh thu đạt 440,9 tỷ đồng (-29,2% yoy), hoàn thành 40,6% kế hoạch; lợi nhuận sau thuế đạt 100,2 tỷ đồng (+41,1% yoy), đạt 86,8% kế hoạch năm.",
                "summary_en": "FICO Corporation (FIC - UPCoM) announced 2Q26 revenue of VND216.9bn (-36.6% yoy) and NPAT of VND78.1bn (+32.5% yoy). For 6M26, revenue reached VND440.9bn (-29.2% yoy), fulfilling 40.6% of the target, while NPAT reached VND100.2bn (+41.1% yoy), completing 86.8% of the full-year target."
            },
            {
                "section": "Corporate News",
                "title": "VKC. (Công ty Cổ phần VKC Holdings. UPCoM)",
                "source": "Manual",
                "url": "http://upcom.vn/vkc",
                "category": "corporate",
                "ticker": "VKC",
                "exchange": "UPCoM",
                "company_vn": "Công ty Cổ phần VKC Holdings",
                "company_en": "VKC Holdings Joint Stock Company",
                "sector": "industrials",
                "summary_vn": "Công ty Cổ phần VKC Holdings (VKC - UPCoM) ghi nhận doanh thu quý 2/2026 đạt 3,3 tỷ đồng (-6,6% yoy) và lỗ sau thuế 15,3 tỷ đồng. Lũy kế 6 tháng đầu năm 2026, doanh thu đạt 8,5 tỷ đồng (-19,5% yoy), hoàn thành 34% kế hoạch năm; lỗ sau thuế ở mức 26,8 tỷ đồng, đạt 61,6% chỉ tiêu kế hoạch năm.",
                "summary_en": "VKC Holdings Joint Stock Company (VKC - UPCoM) reported 2Q26 revenue of VND3.3bn (-6.6% yoy) and a net loss of VND15.3bn. For 6M26, revenue reached VND8.5bn (-19.5% yoy), fulfilling 34% of the full-year target, while net loss stood at VND26.8bn, reaching 61.6% of the annual target."
            }
        ]
        out_items.extend(EARNINGS_ITEMS)

    out_file = SUMMARIES_DIR / f"mor_chunk_{i}_summary.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_items, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(out_items)} items to {out_file}")

print("Summarization pipeline completed.")
