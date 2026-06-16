from __future__ import annotations

import re
from typing import Any


MACRO_TITLES = {
    "economic_indicators": {
        "en": "Economic indicators",
        "vn": "Chỉ số kinh tế",
    },
    "government_bond_yield": {
        "en": "Government bond yield",
        "vn": "Lợi suất trái phiếu Chính phủ",
    },
    "interbank_rate": {
        "en": "Interbank rate",
        "vn": "Lãi suất liên ngân hàng",
    },
}

NOISY_TITLE_MARKERS = ("|", "http", "www.", ".html", ".htm")

# Common 2-letter ASCII short words that are NOT mid-word cuts
_COMMON_SHORT_WORDS = {
    "of", "in", "at", "to", "on", "by", "an", "is", "as", "or",
}


def macro_title_key(item: dict[str, Any]) -> str:
    haystack = " ".join(
        str(item.get(key, ""))
        for key in ("title_en", "title_vn", "summary_en", "summary_vn")
    ).lower()

    if any(token in haystack for token in ("interbank", "liên ngân", "lien ngan", "overnight")):
        return "interbank_rate"
    if any(token in haystack for token in ("g-bond", "government bond", "trái phiếu chính phủ", "trai phieu chinh phu", "10yr")):
        return "government_bond_yield"
    return "economic_indicators"


def macro_title(item: dict[str, Any], lang: str) -> str:
    return MACRO_TITLES[macro_title_key(item)][lang]


def trading_title(item: dict[str, Any], lang: str) -> str:
    summary = str(item.get(f"summary_{lang}") or "").strip()
    ticker = str(item.get("ticker") or "").strip() or _ticker_from_summary(summary)
    exchange = str(item.get("exchange") or item.get("source") or "").strip()
    if ticker.casefold() in {"unlisted", "otc", "upcom", "soe"}:
        ticker = ""
    company = (
        str(item.get(f"company_{lang}") or "").strip()
        or _company_from_summary(summary, ticker)
        or str(item.get(f"title_{lang}") or "").strip()
    )
    if ticker and company:
        suffix = f". {exchange}" if exchange else ""
        return f"{ticker}. ({company}{suffix})"
    return ticker or company


def ticker_company_exchange_title(item: dict[str, Any], lang: str) -> str:
    ticker = str(item.get("ticker") or "").strip()
    company = str(item.get(f"company_{lang}") or "").strip()
    exchange = str(item.get("exchange") or item.get("source") or "").strip()
    if ticker.casefold() in {"unlisted", "otc", "upcom", "soe"}:
        ticker = ""
    if "sanofi" in company.lower():
        return f"Sanofi. {exchange}" if exchange else "Sanofi"
    if ticker and company:
        suffix = f". {exchange}" if exchange else ""
        return f"{ticker}. ({company}{suffix})"
    if ticker:
        return ticker
    return company or str(item.get(f"title_{lang}") or "").strip()


def epo_title(item: dict[str, Any], lang: str) -> str:
    title = str(item.get(f"title_{lang}") or "").strip()
    summary = str(item.get(f"summary_{lang}") or "").strip()

    # Prefer clean JSON title — only fall back to summary-derived lead
    # when the title is absent, noisy (URL etc.), or looks AI-truncated.
    if _is_clean_short_title(title):
        return title
    return _short_lead(summary or title, lang)


def normalized_item_title(item: dict[str, Any], category: str, lang: str) -> str:
    if category == "macro":
        return macro_title(item, lang)
    if category == "trading":
        return trading_title(item, lang)
    if category == "economy_political_others":
        return epo_title(item, lang)
    return str(item.get(f"title_{lang}") or "").strip()


def apply_titles_to_data(data: dict[str, Any], category: str) -> dict[str, Any]:
    if category in ("macro", "trading"):
        for item in data.get("items", []):
            _apply_item_title(item, category)
    elif category == "economy_political_others":
        for subtype in data.get("subtypes", []):
            for item in subtype.get("items", []):
                _apply_item_title(item, category)
    return data


def _apply_item_title(item: dict[str, Any], category: str) -> None:
    for lang in ("en", "vn"):
        item[f"title_{lang}"] = normalized_item_title(item, category, lang)


def _is_clean_short_title(title: str) -> bool:
    if not title:
        return False
    if any(marker in title.lower() for marker in NOISY_TITLE_MARKERS):
        return False
    if _looks_truncated(title):
        return False
    if len(title) > 110:
        return False
    return len(title.split()) <= 15


def _looks_truncated(title: str) -> bool:
    """Return True only when the title is genuinely cut off mid-word.

    Signals:
    - Trailing whitespace or backslash (AI hard-cut after N chars).
    - Last word is a single ASCII lowercase letter (e.g. "m", "p").
    - Last word is a 2-char ASCII-only lowercase fragment that is not a
      common English preposition/article.

    Vietnamese short syllables (1-3 chars with diacritics) are NOT flagged
    because they are grammatically complete words.  The .isascii() check
    reliably distinguishes them from ASCII truncation fragments.
    """
    # Trailing space or backslash = direct evidence of AI character-count truncation
    if title != title.rstrip() or title.endswith("\\"):
        return True
    words = title.rstrip().split()
    if not words:
        return False
    last = words[-1]
    # Vietnamese syllables contain diacritics / multi-byte chars → not ASCII
    # Only apply short-word heuristic to pure ASCII last words.
    if not last.isascii():
        return False
    # Single isolated ASCII lowercase letter → mid-word cut (e.g. "...downward m")
    if len(last) == 1 and last.isalpha() and last.islower():
        return True
    # 2-char ASCII lowercase that is not a known short English word → truncated
    if len(last) == 2 and last.isalpha() and last.islower() and last not in _COMMON_SHORT_WORDS:
        return True
    return False


def _short_lead(text: str, lang: str) -> str:
    # Strip leading date prefix ("On 5 June," / "Ngày 5/6,")
    text = re.sub(r"^\s*(On|Ngày)\s+\d{1,2}\s+\w+[,，]?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*N\S*y\s+\d{1,2}/\d{1,2}[,，]?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*Ng\?y\s+\d{1,2}/\d{1,2}[,，]?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*Ngày\s+\d{1,2}/\d{1,2}[,，]?\s*", "", text, flags=re.IGNORECASE)
    text = text.strip()

    # Try to end at the first complete sentence within a reasonable length
    sentence_end = re.search(r"[.!?]", text)
    if sentence_end and sentence_end.start() <= 120:
        candidate = text[: sentence_end.start()].strip()
        if 4 <= len(candidate.split()) <= 18:
            return candidate

    # Fall back: take up to 12 EN / 10 VN words
    words = text.split()
    limit = 12 if lang == "en" else 10
    lead = " ".join(words[:limit]).strip()
    return lead or text[:100].strip()


def _company_from_summary(summary: str, ticker: str) -> str:
    if not summary or not ticker:
        return ""
    match = re.match(rf"\s*{re.escape(ticker)}\s*\(([^)]+)\)", summary)
    return match.group(1).strip() if match else ""


def _ticker_from_summary(summary: str) -> str:
    match = re.match(r"\s*([A-Z][A-Z0-9]{1,10})\s*\(", summary or "")
    return match.group(1) if match else ""
