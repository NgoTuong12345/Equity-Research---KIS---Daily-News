"""
Summarize chunks for report mor_11_08_2026 following KIS Vietnam Securities rules.
"""
import json
import os
import re
import sys
import io
from pathlib import Path

# Force stdout to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_DIR = Path("V:/KIS-DAILY-NEWS")
BASE_NAME = "mor_11_08_2026"
SOURCE_DIR = BASE_DIR / "reports" / BASE_NAME / "source"
SUMMARIES_DIR = BASE_DIR / "reports" / BASE_NAME / "summaries"
SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

# Load ticker index
ticker_index_path = BASE_DIR / "ticker_index.json"
with open(ticker_index_path, "r", encoding="utf-8") as f:
    ticker_index = json.load(f)
tickers_dict = ticker_index.get("tickers", {})

def detect_ticker_and_info(title, body):
    text = f"{title} {body[:500]}"
    # Look for explicitly parenthesized ticker e.g. (MSH), (AFX), (BAF), (TDH)
    m = re.search(r"\b([A-Z0-9]{3,4})\b", title)
    # Check against tickers_dict
    words = re.findall(r"\b[A-Z]{3,4}\b", title)
    for w in words:
        if w in tickers_dict:
            tinfo = tickers_dict[w]
            return w, tinfo.get("exchange", "HSX"), tinfo.get("company_vn", ""), tinfo.get("company_en", ""), tinfo.get("sector", "financials")
    
    # Check body for ticker matching
    for w in re.findall(r"\b[A-Z]{3,4}\b", text[:300]):
        if w in tickers_dict:
            tinfo = tickers_dict[w]
            return w, tinfo.get("exchange", "HSX"), tinfo.get("company_vn", ""), tinfo.get("company_en", ""), tinfo.get("sector", "financials")
            
    return None, None, None, None, None

def get_sector_for_ticker(ticker, company_name, title):
    if ticker in tickers_dict:
        return tickers_dict[ticker].get("sector", "financials")
    
    t = f"{ticker} {company_name} {title}".lower()
    if any(k in t for k in ["ngân hàng", "bank", "ncb", "vietcombank", "vietabank", "bidv", "agribank", "nvb", "tpb", "vietinbank", "techcombank", "seabank"]):
        return "banking"
    if any(k in t for k in ["chứng khoán", "securities", "vnx", "dịch vụ tài chính"]):
        return "financials"
    if any(k in t for k in ["đường", "sữa", "may", "dệt", "baf", "thiên long", "tiêu dùng", "bánh", "kẹo", "thực phẩm", "heo", "lợn", "nông nghiệp"]):
        return "consumers"
    if any(k in t for k in ["bất động sản", "saigonres", "thuduc house", "tdh", "sgr", "phú quốc", "nhà ở"]):
        return "real_estate"
    if any(k in t for k in ["thép", "hóa chất", "đạm", "ninh bình", "nguyên vật liệu", "vinmetal"]):
        return "materials"
    if any(k in t for k in ["fecon", "pc1", "xây dựng", "hạ tầng", "cơ khí", "coma 18", "cig", "afiex", "sonadezi", "vietjet"]):
        return "industrials"
    if any(k in t for k in ["công nghệ", "fpt", "viettel", "vinspace"]):
        return "technologies"
    if any(k in t for k in ["dược", "y tế", "pharma"]):
        return "pharma"
    if any(k in t for k in ["điện", "nước", "tiện ích", "nbw"]):
        return "utilities"
    return "financials"

def clean_word_count(text, max_words=58):
    words = text.split()
    if len(words) > max_words:
        # Cut gracefully at last period/sentence or max_words
        truncated = " ".join(words[:max_words])
        last_dot = truncated.rfind(".")
        if last_dot > 100:
            return truncated[:last_dot + 1]
        return truncated + "."
    return text

print("Generate all summaries script initialized.")
