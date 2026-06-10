"""
Format HSX NotebookLM extraction JSON into company trading-news prose.

Input:
    hsx_insider_trading_YYYYMMDD_HHMM_extracted.json

Outputs by default:
    hsx_insider_trading_YYYYMMDD_HHMM_extracted_formatted.json
    hsx_insider_trading_YYYYMMDD_HHMM_extracted_EN.txt
    hsx_insider_trading_YYYYMMDD_HHMM_extracted_VN.txt

Usage:
    python format_hsx_trading_news.py hsx_insider_trading_20260605_1113_extracted.json
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
import sys
import io
from pathlib import Path
from typing import Any

# Force stdout to UTF-8 to support Vietnamese characters on Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


COMPANY_EN = {
    "Công ty Cổ phần Dịch vụ Hàng hóa Sài Gòn": "Saigon Cargo Service",
    "Công ty Cổ Phần Dịch Vụ Hàng Hóa Sài Gòn": "Saigon Cargo Service",
    "Công ty Cổ phần Đầu tư Sài Gòn VRG": "Sai Gon VRG Investment Joint Stock Company",
    "Công ty Cổ phần Chứng khoán SSI": "SSI Securities Corporation",
    "Công ty CP Tàu cao tốc Superdong Kiên Giang": "Superdong Fast Ferry Kien Giang Joint Stock Company",
    "Công ty cổ phần Đầu tư phát triển nhà và đô thị IDICO": "IDICO Urban and House Development Investment Joint Stock Company",
}

RELATIONSHIP_EN = {
    "Thành viên Hội đồng quản trị độc lập": "Independent Member of the Board of Directors",
    "Thành viên Hội đồng Quản trị": "Member of the Board of Directors",
    "Thành viên Hội đồng quản trị": "Member of the Board of Directors",
    "Chủ tịch Hội đồng quản trị": "Chairman of the Board of Directors",
    "Chủ tịch HĐQT": "Chairman of the Board of Directors",
    "Con của Chủ tịch Hội đồng Quản trị": "Child of the Chairman of the Board of Directors",
    "Thành viên HĐQT": "Member of the Board of Directors",
    "Tổng Giám Đốc": "General Director",
    "Tổng Giám đốc": "General Director",
    "Kế toán trưởng": "Chief Accountant",
    "Giám đốc Tài chính": "Chief Financial Officer",
    "Người Phụ trách quản trị Công ty": "Person in charge of Corporate Governance",
    "Người phụ trách quản trị Công ty": "Person in charge of Corporate Governance",
    "Người được ủy quyền CBTT": "Authorized person to disclose information",
    "Người có liên quan của người nội bộ": "Related person of insider",
    "Cha ruột": "Father",
    "Cha": "Father",
    "Mẹ ruột": "Mother",
    "Mẹ": "Mother",
    "Vợ": "Wife",
    "Chồng": "Husband",
    "Con ruột": "Child",
    "Con": "Child",
    "Em ruột": "Sibling",
    "Anh ruột": "Sibling",
    "Chị ruột": "Sibling",
    "Người ủy quyền công bố thông tin": "Authorized person to disclose information",
    "Người phụ trách quản trị công ty": "Person in charge of Corporate Governance",
    "Người phụ trách Quản trị công ty": "Person in charge of Corporate Governance",
    "Phó Tổng giám đốc cấp cao": "Senior Deputy General Director",
    "Phó Tổng Giám đốc": "Deputy General Director",
    "Phó Tổng giám đốc": "Deputy General Director",
    "Thành viên HĐQT, Tổng Giám Đốc": "Member of the Board of Directors, General Director",
    "Giám đốc Kiểm toán nội bộ": "Director of Internal Audit",
    "Giám đốc Tài chính kiêm Kế toán trưởng": "Chief Financial Officer and Chief Accountant",
    "Công ty mẹ đồng thời là người có liên quan của người nội bộ": "Parent company and related person of insider",
    "Công ty mẹ, tổ chức có liên quan của Người nội bộ của Công ty cổ phần Vinhomes": "Parent company, related organization of Vinhomes's insider",
    "Công đoàn": "Trade Union",
    "Bố ruột": "Father",
    "Bố": "Father",
    "Em vợ": "Brother-in-law",
    "Chủ tịch Hội đồng Quản trị": "Chairman of the Board of Directors",
    "Cổ đông lớn, cổ đông nội bộ": "Major and internal shareholder",
}

NAME_EN = {
    "Tạ Thu Hà": "Ta Thu Ha",
    "Bùi Thị Thu Hương": "Bui Thi Thu Huong",
    "Trần Lê An": "Tran Le An",
    "Trần Mạnh Hùng": "Tran Manh Hung",
}

NAME_VN = {
    "ta thu ha": "Tạ Thu Hà",
    "bui thi thu huong": "Bùi Thị Thu Hương",
    "tran le an": "Trần Lê An",
    "tran manh hung": "Trần Mạnh Hùng",
}


def ascii_fold(text: str) -> str:
    text = unicodedata.normalize("NFD", text or "")
    text = text.replace("Đ", "D").replace("đ", "d")
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


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


def exchange_for(record: dict[str, Any], tx: dict[str, Any]) -> str:
    exchange = normalize_text(tx.get("exchange") or record.get("source") or "HSX")
    return exchange or "HSX"


def english_company(company_vn: str) -> str:
    return COMPANY_EN.get(company_vn, ascii_fold(company_vn))


def english_name(name_vn: str) -> str:
    return NAME_EN.get(name_vn, ascii_fold(name_vn))


def canonical_vn_name(name_vn: str) -> str:
    folded = ascii_fold(name_vn).lower()
    return NAME_VN.get(folded, name_vn)


def english_relationship(relationship_vn: str) -> str:
    if relationship_vn in RELATIONSHIP_EN:
        return RELATIONSHIP_EN[relationship_vn]

    translated = relationship_vn
    # Replace known phrases inside longer relationship strings.
    for vn, en in sorted(RELATIONSHIP_EN.items(), key=lambda item: len(item[0]), reverse=True):
        translated = translated.replace(vn, en)
    return ascii_fold(translated)


def action_words(action: str) -> dict[str, str]:
    action = (action or "").lower()
    if action == "sell":
        return {
            "en_action": "sell",
            "en_delta": "decreasing",
            "vn_action": "bán",
            "vn_delta": "giảm",
            "vn_direction": "xuống",
        }
    return {
        "en_action": "buy",
        "en_delta": "increasing",
        "vn_action": "mua",
        "vn_delta": "tăng",
        "vn_direction": "lên",
    }


def format_transaction(record: dict[str, Any], tx: dict[str, Any], order: int) -> dict[str, Any]:
    ticker = normalize_text(tx.get("ticker") or record.get("ticker"))
    company_vn = normalize_text(tx.get("company_fullname"))
    company_en = english_company(company_vn)
    exchange = exchange_for(record, tx)
    date_range = normalize_text(tx.get("date_range"))
    name_vn = canonical_vn_name(normalize_text(tx.get("name")))
    name_en = english_name(name_vn)
    rel_vn = normalize_text(tx.get("relationship"))
    rel_en = english_relationship(rel_vn)
    words = action_words(normalize_text(tx.get("action")))
    change_volume = format_number(tx.get("change_volume"))
    after_volume = format_number(tx.get("after_volume"))
    after_percentage = clean_percentage(tx.get("after_percentage"))

    summary_en = (
        f"{ticker} ({company_en}) {exchange}: {date_range}. "
        f"{name_en} ({rel_en}) announced to {words['en_action']} {change_volume} shares, "
        f"{words['en_delta']} total shares to {after_volume} shares ({after_percentage});"
    )
    summary_vn = (
        f"{ticker} ({company_vn}) {exchange}: {date_range}. "
        f"{name_vn} ({rel_vn}) thông báo đăng ký {words['vn_action']} {change_volume} cổ phiếu, "
        f"{words['vn_delta']} tổng số lượng cổ phiếu nắm giữ {words['vn_direction']} "
        f"{after_volume} cổ phiếu ({after_percentage});"
    )

    return {
        "order": order,
        "ticker": ticker,
        "exchange": exchange,
        "company_vn": company_vn,
        "company_en": company_en,
        "source": exchange,
        "url": record.get("url", ""),
        "published": record.get("date", ""),
        "title_vn": f"{ticker}. ({company_vn}. {exchange})" if ticker and company_vn else f"{company_vn}. {exchange}",
        "title_en": f"{ticker}. ({company_en}. {exchange})" if ticker and company_en else f"{company_en}. {exchange}",
        "summary_vn": summary_vn,
        "summary_en": summary_en,
        "relationship_vn": rel_vn,
        "relationship_en": rel_en,
        "raw_transaction": tx,
    }


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


def format_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for record in records:
        for tx in record.get("transactions") or []:
            key = transaction_key(record, tx)
            if key in seen:
                continue
            seen.add(key)
            items.append(format_transaction(record, tx, len(items) + 1))
    return items


def default_outputs(input_path: Path) -> tuple[Path, Path, Path]:
    stem = re.sub(r"_formatted$", "", input_path.stem)
    return (
        input_path.with_name(f"{stem}_formatted.json"),
        input_path.with_name(f"{stem}_EN.txt"),
        input_path.with_name(f"{stem}_VN.txt"),
    )


def double_check_extracted_data(items: list[dict[str, Any]]) -> None:
    print("\n=== DOUBLE-CHECKING EXTRACTED TRADING DATA ===")
    has_warnings = False
    for item in items:
        ticker = item.get("ticker", "N/A")
        rel_vn = item.get("relationship_vn", "")
        rel_en = item.get("relationship_en", "")
        
        # Check for untranslated relationship words
        # If rel_en is just the ascii-folded version of rel_vn, and rel_vn contains Vietnamese words
        folded_vn = ascii_fold(rel_vn).lower().strip()
        folded_en = ascii_fold(rel_en).lower().strip()
        
        if rel_vn and folded_vn == folded_en and any(c.isalpha() for c in rel_vn):
            # Known English words that might be identical to folded Vietnamese or standard abbreviations
            known_en_words = {"ceo", "cfo", "director", "manager", "bod", "chairman", "assistant", "member", "independent", "accountant", "officer", "insider", "relative", "deputy", "vice"}
            words_en = set(folded_en.split())
            if not words_en.intersection(known_en_words):
                print(f"WARNING: Untranslated relationship for {ticker}: '{rel_vn}' -> '{rel_en}'")
                print("  Please update RELATIONSHIP_EN in format_hsx_trading_news.py with this term.")
                has_warnings = True
                
        # Check for missing critical fields
        for field in ("ticker", "company_vn", "summary_vn", "summary_en"):
            if not item.get(field):
                print(f"ERROR: Missing field '{field}' in item order {item.get('order')}")
                has_warnings = True
                
    if not has_warnings:
        print("All trading items passed verification successfully!")
    print("=============================================\n")


def run(input_path: Path, output_json: Path | None = None) -> Path:
    records = json.loads(input_path.read_text(encoding="utf-8"))
    items = format_records(records)
    double_check_extracted_data(items)
    default_json, en_txt, vn_txt = default_outputs(input_path)
    output_json = output_json or default_json

    payload = {
        "source_file": str(input_path),
        "category": "trading",
        "item_count": len(items),
        "items": items,
    }
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    en_txt.write_text("\n".join(item["summary_en"] for item in items), encoding="utf-8")
    vn_txt.write_text("\n".join(item["summary_vn"] for item in items), encoding="utf-8")
    return output_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Format HSX NLM extracted JSON into trading-news prose")
    parser.add_argument("input", type=Path, help="Path to *_extracted.json")
    parser.add_argument("--output", type=Path, default=None, help="Optional formatted JSON output path")
    args = parser.parse_args()

    output = run(args.input, args.output)
    print(f"Formatted trading news saved to: {output}")


if __name__ == "__main__":
    main()
