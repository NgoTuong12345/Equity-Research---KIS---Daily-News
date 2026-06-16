from __future__ import annotations
from typing import Any

def normalized_item_title(item: dict[str, Any], category: str, lang: str) -> str:
    """
    Returns the news title for a given item, category, and language.
    Since the pipeline has switched to an agent-driven title generation workflow,
    we directly return the pre-standardized titles merged into the data JSONs.
    """
    return str(item.get(f"title_{lang}") or "").strip()

def ticker_company_exchange_title(item: dict[str, Any], lang: str) -> str:
    """
    Returns the standard formatted title for corporate and trading news:
    TICKER. (Company Name. Exchange)
    """
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
