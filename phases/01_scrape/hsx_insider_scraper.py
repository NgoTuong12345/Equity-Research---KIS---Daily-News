"""
HSX Insider Trading Scraper
Fetches the last 24h of insider trading disclosure news from the HOSE (HSX)
stock exchange API and saves results as a JSON file.

Output: hsx_insider_trading_YYYYMMDD_HHMM.json

Usage:
    python hsx_insider_scraper.py              # last 24 hours
    python hsx_insider_scraper.py --hours 48   # last 48 hours
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BASE_API = "https://api.hsx.vn"
HSX_ARTICLE_BASE = "https://www.hsx.vn/vi/tin-tuc/tin-to-chuc-niem-yet"
PAGE_SIZE = 100
OUTDIR = "./"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


# ── Vietnamese text helpers ───────────────────────────────────────────────────

_ACCENT_RE = re.compile(r"[̀-ͯ]")


def _ascii_fold(s: str) -> str:
    if not s:
        return ""
    s = s.replace("đ", "d").replace("Đ", "D")
    nfd = unicodedata.normalize("NFD", s.lower())
    return _ACCENT_RE.sub("", nfd)


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s or "")


# ── Classifier ────────────────────────────────────────────────────────────────

_INSIDER_ANCHORS = [
    "giao dich cua co dong noi bo",
    "giao dich cua nguoi noi bo",
    "giao dich cua nguoi co lien quan",
    "co dong noi bo",
    "nguoi co lien quan",
    "nguoi noi bo",
    "thong bao giao dich",
    "bao cao ket qua giao dich",
    "cong bo thong tin ve giao dich",
]

_UPCOMING_KEYWORDS = [
    "thong bao giao dich",
    "thong bao dang ky",
    "thong bao ve viec giao dich",
]

_EXCLUDED_KEYWORDS = [
    "ket qua",
    "hop dong",
    "nghi quyet",
    "dinh chinh",
    "phe duyet",
]


def _is_insider_trading(title: str, summary: str) -> bool:
    folded = _ascii_fold(title) + " " + _ascii_fold(_strip_html(summary or ""))
    has_anchor = any(a in folded for a in _INSIDER_ANCHORS)
    if not has_anchor:
        return False
    title_f = _ascii_fold(title)
    has_upcoming = any(k in title_f for k in _UPCOMING_KEYWORDS)
    has_excluded = any(k in title_f for k in _EXCLUDED_KEYWORDS)
    return has_upcoming and not has_excluded


def _extract_ticker(title: str) -> Optional[str]:
    if not title:
        return None
    m = re.match(r"^\s*([A-Z][A-Z0-9]{1,10}):\s+", title)
    if m:
        return m.group(1)[:6]
    return None


# ── HSX API ───────────────────────────────────────────────────────────────────

def _vn_now() -> datetime:
    return datetime.now(timezone(timedelta(hours=7)))


def _fetch_stock_news(start_date: str, end_date: str) -> List[dict]:
    url = f"{BASE_API}/n/api/v1/1/news/securitiesType/1"
    params = {"startDate": start_date, "endDate": end_date, "pageIndex": 1, "pageSize": PAGE_SIZE}
    all_items: List[dict] = []
    while True:
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch HSX news page {params['pageIndex']}: {e}")
            break
        data = payload.get("data") or {}
        items = data.get("list") or []
        paging = data.get("paging") or {}
        total = paging.get("totalCount", 0)
        all_items.extend(items)
        if not items or len(all_items) >= total:
            break
        params["pageIndex"] += 1
        time.sleep(0.3)
    return all_items


def fetch_insider_news(hours: int = 24) -> List[dict]:
    vn_now = _vn_now()
    baseline_ts = time.time()
    limit_seconds = hours * 3600
    days = (hours + 23) // 24
    start_date = (vn_now - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = vn_now.strftime("%Y-%m-%d")

    logger.info(f"Fetching HSX stock news from {start_date} to {end_date}...")
    all_news = _fetch_stock_news(start_date, end_date)
    logger.info(f"Total articles fetched: {len(all_news)}")

    insider_items = []
    for item in all_news:
        # Time window filter
        posted_ts = item.get("postedDate")
        if posted_ts is not None:
            try:
                if baseline_ts - float(posted_ts) > limit_seconds:
                    continue
            except (ValueError, TypeError):
                pass

        title = item.get("title") or ""
        summary = item.get("summary") or ""
        if _is_insider_trading(title, summary):
            insider_items.append(item)

    logger.info(f"Insider trading disclosures found: {len(insider_items)}")
    return insider_items


# ── PDF link scraper ──────────────────────────────────────────────────────────

def _make_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument(f"user-agent={HEADERS['User-Agent']}")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


def scrape_pdf_links_batch(article_ids: List[int]) -> dict:
    """Return {article_id: [pdf_url, ...]} for all IDs using a single browser session."""
    results = {aid: [] for aid in article_ids}
    if not article_ids:
        return results
    driver = _make_driver()
    try:
        for i, article_id in enumerate(article_ids):
            if i > 0:
                time.sleep(0.5)
            url = f"{HSX_ARTICLE_BASE}/{article_id}"
            try:
                driver.get(url)
                time.sleep(2)  # wait for React to render
                soup = BeautifulSoup(driver.page_source, "html.parser")
                pdf_urls = []
                for tag in soup.find_all("a", href=True):
                    href = tag["href"]
                    href_lower = href.lower()
                    if ".pdf" in href_lower or "uploads/uploaddocuments" in href_lower:
                        abs_url = urljoin("https://www.hsx.vn", href)
                        if abs_url not in pdf_urls:
                            pdf_urls.append(abs_url)
                results[article_id] = pdf_urls
            except Exception as e:
                logger.error(f"Failed to scrape article {article_id}: {e}")
    finally:
        driver.quit()
    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def build_output_record(article: dict) -> dict:
    posted_ts = float(article.get("postedDate") or 0)
    tz_vn = timezone(timedelta(hours=7))
    dt_vn = datetime.fromtimestamp(posted_ts, tz=tz_vn)
    article_id = article.get("id")
    title = article.get("title") or ""
    return {
        "date": dt_vn.strftime("%Y-%m-%d"),
        "time": dt_vn.strftime("%H:%M"),
        "source": "HSX",
        "category": "insider_trading",
        "ticker": _extract_ticker(title),
        "article_id": article_id,
        "title": title,
        "summary": _strip_html(article.get("summary") or "").strip(),
        "url": f"{HSX_ARTICLE_BASE}/{article_id}",
        "pdf_urls": [],
    }


def run(hours: int = 24, scrape_pdfs: bool = True) -> str:
    insider_articles = fetch_insider_news(hours=hours)

    records = [build_output_record(a) for a in insider_articles]

    if scrape_pdfs and records:
        article_ids = [r["article_id"] for r in records if r["article_id"]]
        logger.info(f"Scraping PDF links for {len(article_ids)} articles...")
        pdf_map = scrape_pdf_links_batch(article_ids)
        for record in records:
            aid = record["article_id"]
            if aid:
                record["pdf_urls"] = pdf_map.get(aid, [])
                logger.info(f"{record['ticker']} (#{aid}) — {len(record['pdf_urls'])} PDF(s)")

    vn_now = _vn_now()
    filename = f"hsx_insider_trading_{vn_now.strftime('%Y%m%d_%H%M')}.json"
    out_path = OUTDIR + filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(records)} records to {out_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HSX insider trading scraper")
    parser.add_argument("--hours", type=int, default=None, help="Lookback window in hours (overrides all other logic)")
    parser.add_argument("--session", choices=["morning", "afternoon"], default=None,
                        help="Explicit session context for hour selection (morning=16h/60h Mon, afternoon=7h)")
    parser.add_argument("--no-pdfs", action="store_true", help="Skip PDF link scraping")
    args = parser.parse_args()

    hours = args.hours
    if hours is None:
        tz = timezone(timedelta(hours=7))
        local_now = datetime.now(tz)
        is_monday = local_now.weekday() == 0

        session = args.session
        if session is None:
            session = "morning" if local_now.hour < 12 else "afternoon"
            logger.info(f"No --session provided; inferred from clock: {session}")

        if session == "morning":
            if is_monday:
                hours = 60
                logger.info("Monday morning: setting HSX lookback to 60 hours.")
            else:
                hours = 16
                logger.info("Morning session: setting HSX lookback to 16 hours.")
        else:
            hours = 7
            logger.info("Afternoon session: setting HSX lookback to 7 hours.")
    else:
        logger.info(f"Using explicit --hours: {hours}")

    run(hours=hours, scrape_pdfs=not args.no_pdfs)
