"""
HSX Insider Trading — Automated Manifest Text Extractor

Extracts structured transaction data from the text layer of PDFs in manifest.json
and generates _agent_results.json cleanly without requiring image viewing.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys, io
import unicodedata
from pathlib import Path
from typing import Any, Optional, Dict, List

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def clean_str(val: Any) -> str:
    if not val:
        return ""
    val = str(val).strip()
    return unicodedata.normalize("NFC", val)


def parse_int(val: Any) -> Optional[int]:
    if not val:
        return None
    val_str = re.sub(r"[^\d]", "", str(val))
    return int(val_str) if val_str else None


def extract_dates(text: str) -> str:
    """Extract date range in MM/DD~MM/DD format."""
    m = re.search(r"(\d{1,2})/(\d{1,2})/(?:20)?\d{2}\s*(?:đến ngày/to:|đến ngày|đến|to|-|~)\s*(\d{1,2})/(\d{1,2})/(?:20)?\d{2}", text, re.IGNORECASE)
    if m:
        d1, m1, d2, m2 = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        return f"{m1:02d}/{d1:02d}~{m2:02d}/{d2:02d}"
    
    m_short = re.search(r"từ ngàylfrom\s*(\d{1,2})/(\d{1,2})/(?:20)?\d{2}\s*đến ngàylto\s*(\d{1,2})/(\d{1,2})/(?:20)?\d{2}", text, re.IGNORECASE)
    if m_short:
        d1, m1, d2, m2 = int(m_short.group(1)), int(m_short.group(2)), int(m_short.group(3)), int(m_short.group(4))
        return f"{m1:02d}/{d1:02d}~{m2:02d}/{d2:02d}"
    return ""


def extract_company_fullname(text: str, default_ticker: str) -> str:
    m = re.search(r"Công ty (?:CP|Cổ phần)[^\n\.,]+", text, re.IGNORECASE)
    if m:
        return clean_str(m.group(0))
    return ""


def clean_relationship(raw_rel: str) -> str:
    raw_rel = clean_str(raw_rel)
    if not raw_rel or raw_rel in ("/.", "-"):
        return ""
    if "/" in raw_rel:
        raw_rel = raw_rel.split("/")[0].strip()
    raw_rel = re.sub(r"^[-:\s]+", "", raw_rel)
    if "Mối quan hệ" in raw_rel:
        return ""
    return raw_rel


def parse_pdf_text(text: str, article_ticker: str, article_title: str) -> List[Dict[str, Any]]:
    if not text or len(text.strip()) < 50:
        return []

    full_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])

    # 1. Ticker
    m_ticker = re.search(r"Mã chứng khoán[^\n:]*[:\n]\s*([A-Z0-9]{3})", full_text, re.IGNORECASE)
    ticker = m_ticker.group(1).upper() if m_ticker else article_ticker

    # 2. Name
    m_name = (
        re.search(r"(?:Tên cá nhân/tổ chức|Name of individual|Họ và tên cá nhân/Tên tổ chức)[^\n:]*[:\n]\s*([^\n]+)", full_text, re.IGNORECASE)
        or re.search(r"Họ và tên cá nhân[^\n:]*[:\n]\s*([^\n]+)", full_text, re.IGNORECASE)
    )
    name = clean_str(m_name.group(1)) if m_name else ""
    if "/" in name:
        name = name.split("/")[0].strip()
    if "|" in name:
        name = name.split("|")[0].strip()

    if not name or name.lower() in ("cá nhân", "tổ chức", "/.", "người nội bộ", "tên cá nhân/tổ chức"):
        m_title_name = re.search(r"Người nội bộ\s+([^\n,]+)", article_title, re.IGNORECASE) or re.search(r"người có liên quan của Người nội bộ\s+([^\n,]+)", article_title, re.IGNORECASE)
        if m_title_name:
            name = clean_str(m_title_name.group(1))
        else:
            return []

    # 3. Position / Relationship
    m_pos = re.search(r"Chức vụ hiện nay[^\n:]*[:\n]\s*([^\n]+)", full_text, re.IGNORECASE)
    pos = clean_relationship(m_pos.group(1)) if m_pos else ""
    if "|" in pos:
        pos = pos.split("|")[0].strip()

    m_internal = re.search(r"Họ và tên người nội bộ[^\n:]*[:\n]\s*([^\n]+)", full_text, re.IGNORECASE)
    internal_name = clean_str(m_internal.group(1)) if m_internal else ""
    if "/" in internal_name:
        internal_name = internal_name.split("/")[0].strip()
    if "|" in internal_name:
        internal_name = internal_name.split("|")[0].strip()

    m_rel = re.search(r"Mối quan hệ[^\n:]*[:\n]\s*([^\n]+)", full_text, re.IGNORECASE)
    rel = clean_relationship(m_rel.group(1)) if m_rel else ""
    if "|" in rel:
        rel = rel.split("|")[0].strip()

    relationship = ""
    if pos:
        relationship = pos
    elif rel and internal_name:
        relationship = f"{rel} của {internal_name}"
    elif rel:
        relationship = rel
    elif internal_name:
        relationship = f"Người có liên quan đến {internal_name}"
    else:
        relationship = "Cổ đông"

    # 4. Action
    action = "buy"
    if "bán" in article_title.lower() or "chuyển nhượng" in article_title.lower() or "sale" in full_text.lower():
        if "mua" not in article_title.lower():
            action = "sell"

    # 5. Volume change
    m_eq = re.search(r"tương đương\s+([\d\.\,]+)\s+(?:CP|cổ phiếu)", full_text, re.IGNORECASE)
    if m_eq:
        change_volume = parse_int(m_eq.group(1))
    else:
        m_vol = (
            re.search(r"Số lượng[^\n]*đăng ký[^\n:]*[:\n]\s*([\d\.\,]+)", full_text, re.IGNORECASE)
            or re.search(r"registered for trading[:\n]\s*([\d\.\,]+)", full_text, re.IGNORECASE)
            or re.search(r"registered to [a-z]+[:\n]\s*([\d\.\,]+)", full_text, re.IGNORECASE)
            or re.search(r"([\d\.\,]{4,})\s*(?:cổ phiếu|shares)", full_text, re.IGNORECASE)
        )
        change_volume = parse_int(m_vol.group(1)) if m_vol else None

    # 6. After volume
    m_after = (
        re.search(r"nắm giữ sau khi[^\n:]*[:\n]\s*([\d\.\,]+)", full_text, re.IGNORECASE)
        or re.search(r"expected to hold after[^\n:]*[:\n]\s*([\d\.\,]+)", full_text, re.IGNORECASE)
    )
    after_volume = parse_int(m_after.group(1)) if m_after else None

    # 7. Date range
    date_range = extract_dates(full_text)

    # 8. Company fullname
    company_fullname = extract_company_fullname(full_text, ticker)

    return [{
        "ticker": ticker,
        "name": name,
        "relationship": relationship,
        "action": action,
        "change_volume": change_volume,
        "after_volume": after_volume,
        "after_percentage": None,
        "date_range": date_range,
        "company_fullname": company_fullname,
        "exchange": "HSX"
    }]


def process_manifest(manifest_path: Path) -> Path:
    log.info(f"Processing manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    results = {}
    for item in manifest:
        aid = item.get("article_id")
        ticker = item.get("ticker", "")
        title = item.get("title", "")
        pdfs = item.get("pdfs", [])

        article_txs = []
        for pdf in pdfs:
            text = pdf.get("text", "")
            if not text or len(text.strip()) < 50 or "THÔNG BÁO" not in text:
                pdf_p = Path(pdf.get("pdf_path", ""))
                if pdf_p.exists():
                    try:
                        import fitz
                        doc = fitz.open(pdf_p)
                        text = "\n".join(p.get_text() for p in doc)
                    except ImportError:
                        try:
                            import pdfplumber
                            with pdfplumber.open(pdf_p) as pdf_doc:
                                text = "\n".join(p.extract_text() or "" for p in pdf_doc.pages)
                        except Exception as e:
                            log.warning(f"Could not read {pdf_p} with pdfplumber: {e}")
                    except Exception as e:
                        log.warning(f"Could not read {pdf_p} with fitz: {e}")

            txs = parse_pdf_text(text, ticker, title)
            
            # Check if txs is a stub/missing core details (scanned PDF with digital signature text layer)
            is_stub = not txs or all(t.get("change_volume") is None and not t.get("date_range") for t in txs)
            if is_stub:
                log.info(
                    f"Text layer insufficient for article {aid} (scanned PDF). "
                    "Scanned documents require multimodal vision extraction directly from rendered images."
                )
                txs = []

            article_txs.extend(txs)

        results[aid] = {"transactions": article_txs}

    source_stem = manifest_path.stem.replace("_manifest", "")
    out_path = manifest_path.with_name(source_stem + "_agent_results.json")
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"Saved extraction results to {out_path}")
    return out_path



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract HSX insider trading transactions from manifest text")
    parser.add_argument("--manifest", type=Path, default=None, help="Path to manifest JSON")
    args = parser.parse_args()

    if not args.manifest:
        import glob
        matches = sorted(glob.glob(str(Path("phases/01_scrape/hsx_insider_trading_*_manifest.json"))))
        if matches:
            args.manifest = Path(matches[-1])
        else:
            log.error("No manifest found!")
            sys.exit(1)

    process_manifest(args.manifest)

