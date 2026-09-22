import os
import datetime as dt
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import feedparser
import re
import time
import logging
import concurrent.futures
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# --- SELENIUM IMPORTS ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURATION ---
# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - [%(threadName)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Timezone Setup
try:
    import pytz
    TZ = pytz.timezone("Asia/Ho_Chi_Minh")
except ImportError:
    from datetime import timezone, timedelta
    TZ = timezone(timedelta(hours=7))
    

# Execution Settings
MAX_WORKERS = 10  # Number of parallel threads
OUTDIR = os.path.abspath(os.path.dirname(__file__))
FILENAME = "vietnam_financial_news_combined"
HOURS_LOOKBACK = 24

# Request Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, application/atom+xml, text/xml;q=0.9, */*;q=0.8'
}

# --- SOURCE CONFIGURATIONS ---

# 1. TinNhanhChungKhoan URLs
TINNHANH_URLS = [
    "https://www.tinnhanhchungkhoan.vn/",
    "https://www.tinnhanhchungkhoan.vn/doanh-nghiep/",
    "https://www.tinnhanhchungkhoan.vn/bat-dong-san/",
    "https://www.tinnhanhchungkhoan.vn/tai-chinh/",
    "https://www.tinnhanhchungkhoan.vn/quoc-te/",
    "https://www.tinnhanhchungkhoan.vn/thoi-su/"
]

# 2. BaoDautu URLs (NEW)
BAODAUTU_URLS = [
    "https://baodautu.vn/dau-tu-d2/",                  # Đầu tư
    "https://baodautu.vn/batdongsan/",                 # Bất động sản
    "https://baodautu.vn/ngan-hang-d5/",               # Ngân hàng
    "https://baodautu.vn/tai-chinh-chung-khoan-d6/",   # Tài chính - Chứng khoán
    "https://baodautu.vn/doanh-nghiep-d3/"             # Doanh nghiệp
]

# 3. RSS Feeds
RSS_FEEDS: List[str] = [
    "https://viettimes.vn/rss/kinh-te-du-lieu-3.rss",
    "https://viettimes.vn/rss/kinh-te-du-lieu/quan-tri-136.rss",
    "https://viettimes.vn/rss/xa-hoi-so-175.rss",
    "https://viettimes.vn/rss/bat-dong-san-186.rss",
    "https://baochinhphu.vn/rss/",
    "https://vneconomy.vn/nhip-cau-doanh-nghiep.rss",
    "https://vneconomy.vn/tai-chinh.rss", 
    "https://vneconomy.vn/dau-tu.rss",
    "https://vneconomy.vn/dia-oc.rss",
    "https://vneconomy.vn/chung-khoan.rss",
    "https://vneconomy.vn/thi-truong.rss",
    "https://vietstock.vn/737/doanh-nghiep/hoat-dong-kinh-doanh.rss",
    "https://vietstock.vn/738/doanh-nghiep/co-tuc.rss",
    "https://vietstock.vn/764/doanh-nghiep/tang-von-m-a.rss",
    "https://vietstock.vn/746/doanh-nghiep/ipo-co-phan-hoa.rss",
    "https://vietstock.vn/214/doanh-nghiep/nhan-vat.rss",
    "https://vietstock.vn/3118/doanh-nghiep/trai-phieu-doanh-nghiep.rss",
    "https://vietstock.vn/757/tai-chinh/ngan-hang.rss",
    "https://vietstock.vn/4222/bat-dong-san/du-an.rss",
    "https://vietstock.vn/4220//bat-dong-san/thi-truong-nha-dat.rss",
    "https://vietstock.vn/4266/bat-dong-san/bao-hiem-va-thue-nha-dat.rss",
    "https://vietstock.vn/3113/tai-chinh/bao-hiem.rss",
    "https://vietstock.vn/758/tai-chinh/thue-va-ngan-sach.rss",
    "https://vietstock.vn/16312/tai-chinh/tai-san-so.rss",
    "https://vietstock.vn/1636/nhan-dinh-phan-tich/nhan-dinh-thi-truong.rss",
    "https://vietstock.vn/761/kinh-te/vi-mo.rss",
    "https://vietstock.vn/768/kinh-te/kinh-te-dau-tu.rss",
    "https://vietstock.vn/739/chung-khoan/giao-dich-noi-bo.rss",
    "https://vietstock.vn/741/chung-khoan/niem-yet.rss",
    "https://vietstock.vn/143/chung-khoan/chinh-sach.rss",
    "https://vietnambusinessinsider.vn/rss/chuyen-thuong-truong.rss",
    "https://vietnambusinessinsider.vn/rss/tin-moi.rss",
    "https://vietnambusinessinsider.vn/rss/ho-so-doanh-nhan.rss",
    "https://vietnambusinessinsider.vn/rss/quan-tri.rss",
    "https://vietnambusinessinsider.vn/rss/review-bat-dong-san.rss",
    "https://vietnambusinessinsider.vn/rss/theo-dau-dong-tien.rss",
    "http://vietnamnet.vn/kinhte/index.rss",
    "https://nhandan.vn/rss/kinhte-1185.rss",
    "https://nhandan.vn/rss/chinhtri-1171.rss",
    "https://nhandan.vn/rss/chungkhoan-1191.rss",
    "https://nhandan.vn/rss/xahoi-1211.rss",
]

class Categorizer:
    """Keyword-based Categorizer."""

    def __init__(self):
        # --- KEYWORD LOGIC ---
        self.target_categories = [
            "Tài Chính-Ngân Hàng", "Chính Sách-Chính Phủ", "Xã Hội", "Kinh Tế",
            "Chứng Khoán", "Doanh Nghiệp", "Bất Động Sản", "Thế Giới", "Khác"
        ]
        self.url_map = {
            'ngan-hang': 'Tài Chính-Ngân Hàng', 'tai-chinh': 'Tài Chính-Ngân Hàng',
            'chung-khoan': 'Chứng Khoán', 'co-phieu': 'Chứng Khoán',
            'bat-dong-san': 'Bất Động Sản', 'dia-oc': 'Bất Động Sản',
            'doanh-nghiep': 'Doanh Nghiệp', 'kinh-te': 'Kinh Tế',
            'chinh-phu': 'Chính Sách-Chính Phủ', 'the-gioi': 'Thế Giới', 'quoc-te': 'Thế Giới'
        }
        self.keywords = {
            'Tài Chính-Ngân Hàng': {'weight': 4, 'words': {'ngân hàng', 'lãi suất', 'tín dụng', 'tiền gửi', 'nhnn', 'sbv', 'fintech', 'vietcombank'}},
            'Chứng Khoán': {'weight': 4, 'words': {'chứng khoán', 'cổ phiếu', 'vn-index', 'hnx', 'hose', 'thanh khoản', 'margin'}},
            'Bất Động Sản': {'weight': 4, 'words': {'bất động sản', 'căn hộ', 'chung cư', 'đất nền', 'nhà ở', 'vinhomes', 'novaland'}},
            'Doanh Nghiệp': {'weight': 3, 'words': {'doanh nghiệp', 'công ty', 'tập đoàn', 'cổ đông', 'cổ tức', 'lợi nhuận', 'doanh thu'}},
            'Kinh Tế': {'weight': 3, 'words': {'kinh tế', 'gdp', 'cpi', 'lạm phát', 'xuất khẩu', 'nhập khẩu', 'fdi'}},
            'Chính Sách-Chính Phủ': {'weight': 4, 'words': {'chính phủ', 'thủ tướng', 'nghị định', 'thông tư', 'bộ tài chính', 'thuế'}},
            'Xã Hội': {'weight': 2, 'words': {'xã hội', 'lao động', 'việc làm', 'y tế', 'giáo dục'}},
            'Thế Giới': {'weight': 3, 'words': {'thế giới', 'quốc tế', 'fed', 'trung quốc', 'mỹ', 'eu'}}
        }
        self.vn_map = str.maketrans({
            'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a', 'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a', 'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
            'đ': 'd', 'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e', 'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
            'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i', 'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o', 'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o', 'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
            'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u', 'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u', 'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y'
        })

    def normalize(self, text: str) -> str:
        if not text: return ""
        return text.lower().translate(self.vn_map)

    def categorize(self, title: str, url: str, feed_url: str) -> str:
        # Fallback to Keywords/URL
        combined_url = (feed_url + " " + url).lower()
        for key, category in self.url_map.items():
            if key in combined_url:
                return category
                
        norm_text = self.normalize(title + " " + url)
        scores = {cat: 0 for cat in self.keywords}
        for cat, data in self.keywords.items():
            count = sum(1 for w in data['words'] if w in norm_text)
            scores[cat] = count * data['weight']
        
        best_cat = max(scores, key=scores.get)
        if scores[best_cat] > 2: return best_cat
        return "Khác"

categorizer = Categorizer()

class DateParser:
    """Optimized RSS Date Parser."""
    def __init__(self):
        self.formats_tz = ["%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%d/%m/%Y %H:%M:%S %z"]
        self.formats_no_tz = ["%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%a, %d %b %Y %H:%M:%S", "%m/%d/%Y %I:%M:%S %p"]

    def parse(self, entry: Dict) -> Optional[dt.datetime]:
        if 'published_parsed' in entry and entry['published_parsed']:
            try:
                dt_utc = dt.datetime(*entry['published_parsed'][:6], tzinfo=dt.timezone.utc)
                return dt_utc.astimezone(TZ).replace(tzinfo=None)
            except: pass
        raw_date = entry.get('published') or entry.get('updated')
        if not raw_date: return None
        raw_date = raw_date.strip()
        for fmt in self.formats_tz:
            try:
                t = dt.datetime.strptime(raw_date, fmt)
                return t.astimezone(TZ).replace(tzinfo=None)
            except ValueError: continue
        for fmt in self.formats_no_tz:
            try: return dt.datetime.strptime(raw_date, fmt)
            except ValueError: continue
        return None

date_parser = DateParser()

_session = None

def get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        # Add retries adapter for general connection/read failures
        from requests.adapters import HTTPAdapter
        from urllib3.util import Retry
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)
        _session.headers.update(HEADERS)
    return _session

def get_soup(url, max_retries=3, base_delay=1.0):
    """Helper to get BeautifulSoup object from URL with retry backoff"""
    session = get_session()
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
            elif response.status_code in (429, 503):
                sleep_time = base_delay * (attempt + 1) * 2
                logger.warning(f"Rate limited (HTTP {response.status_code}) on {url}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                logger.warning(f"HTTP error {response.status_code} on {url}.")
                break
        except (requests.exceptions.RequestException, Exception) as e:
            sleep_time = base_delay * (attempt + 1)
            logger.warning(f"Error fetching {url} (Attempt {attempt+1}/{max_retries}): {e}. Retrying in {sleep_time}s...")
            time.sleep(sleep_time)
    return None

# --- MODULE 1: TINNHANHCHUNGKHOAN (Request + BS4) ---

def scrape_tinnhanh_details(article: Dict) -> Optional[Dict]:
    """Worker function to parse individual article pages."""
    url = article['url']
    title = article['heading']
    soup = get_soup(url)
    if not soup: return None
        
    dt_obj = None

    # Strategy 1: Meta Tags
    meta_date = soup.find("meta", property="article:published_time")
    if meta_date:
        raw_dt = meta_date.get("content")
        try:
            temp_dt = pd.to_datetime(raw_dt).to_pydatetime()
            # Remove timezone info for naive comparison
            dt_obj = temp_dt.replace(tzinfo=None)
        except: pass

    # Strategy 2: HTML Classes
    if not dt_obj:
        time_el = soup.select_one(".time, .article-time, .date, .info-date")
        if time_el:
            text = time_el.get_text(strip=True)
            try:
                clean_text = text.replace("Thứ hai,", "").replace("Thứ ba,", "").replace("CN,", "").strip()
                match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', clean_text)
                match_time = re.search(r'(\d{1,2}):(\d{2})', clean_text)
                if match:
                    d, m, y = map(int, match.groups())
                    if match_time:
                        hr, mi = map(int, match_time.groups())
                        dt_obj = dt.datetime(y, m, d, hr, mi)
                    else:
                        dt_obj = dt.datetime(y, m, d)
            except: pass

    if not dt_obj: return None

    return {
        "title": title,
        "link": url,
        "published_at": dt_obj,
        "feed_url": "https://tinnhanhchungkhoan.vn",
        "source": "TinNhanhCK",
        "category": categorizer.categorize(title, url, "chung-khoan")
    }

def fetch_tinnhanh_multi_category(urls: List[str], hours_lookback: int) -> List[Dict]:
    logger.info(">>> [Method 2] Fetching TinNhanhChungKhoan...")
    
    unique_articles = {} 
    for category_url in urls:
        soup = get_soup(category_url)
        if not soup: continue

        links = soup.select("article h3 a, article h2 a, .story__heading a")
        for link in links:
            href = link.get('href')
            title = link.get_text(strip=True)
            if href:
                if href.startswith("/"):
                    href = "https://www.tinnhanhchungkhoan.vn" + href.rstrip("/")
                if "tinnhanhchungkhoan.vn" in href and href not in unique_articles:
                    unique_articles[href] = {"url": href, "heading": title}

    article_list = list(unique_articles.values())
    results = []
    cutoff = dt.datetime.now() - dt.timedelta(hours=hours_lookback)
    
    # Use fewer workers (max 2) to avoid rate limiting on tinnhanhchungkhoan.vn
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(scrape_tinnhanh_details, art) for art in article_list]
        for future in concurrent.futures.as_completed(futures):
            try:
                data = future.result()
                if data and data['published_at']:
                    if data['published_at'] >= cutoff:
                        results.append(data)
            except Exception: pass

    logger.info(f"✓ TinNhanhCK: {len(results)} items collected.")
    return results

# --- MODULE 2: SELENIUM SCRAPER (FIREANT) - FIXED ---

def parse_fireant_time(text: str) -> Optional[dt.datetime]:
    """Parses Fireant specific time formats. Returns None if failed."""
    if not text: return None
    now = dt.datetime.now()
    text = text.lower().strip()
    try:
        # Absolute Date
        match_date = re.search(r'(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})', text)
        if match_date:
            day, month, hour, minute = map(int, match_date.groups())
            year = now.year
            if now.month == 1 and month == 12: year -= 1
            return dt.datetime(year, month, day, hour, minute)
        # Relative "Yesterday"
        match_yesterday = re.search(r'hôm qua.*(\d{1,2}):(\d{2})', text)
        if match_yesterday:
            hour, minute = map(int, match_yesterday.groups())
            yesterday = now - dt.timedelta(days=1)
            return yesterday.replace(hour=hour, minute=minute, second=0, microsecond=0)
        # Relative Minutes/Hours
        match_rel = re.search(r'(\d+)\s+(phút|giờ|tiếng)', text)
        if match_rel:
            val = int(match_rel.group(1))
            unit = match_rel.group(2)
            if 'phút' in unit: return now - dt.timedelta(minutes=val)
            elif 'giờ' in unit or 'tiếng' in unit: return now - dt.timedelta(hours=val)
        # Just now
        if "vừa xong" in text or "vừa đăng" in text: return now
    except: pass
    return None

def slugify_fireant_title(text: str) -> str:
    if not text:
        return "tin-tuc"
    text = text.strip()
    text = re.sub(r'[đĐ]', 'd', text)
    text = text.lower()
    text = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', text)
    text = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', text)
    text = re.sub(r'[ìíịỉĩ]', 'i', text)
    text = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', text)
    text = re.sub(r'[ùúụủũưừứựửữ]', 'u', text)
    text = re.sub(r'[ỳýỵỷỹ]', 'y', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    slug = text.strip('-')
    return slug if slug else "tin-tuc"

def fetch_fireant_api(hours_lookback: int) -> List[Dict]:
    """Fetches FireAnt news via REST API using dynamic token extraction, with Selenium fallback."""
    logger.info(">>> [Method 3] Starting FireAnt API Scraper...")
    collected_articles = []
    
    try:
        fireant_url = "https://fireant.vn/bai-viet"
        resp = requests.get(fireant_url, headers=HEADERS, timeout=10)
        token = None
        if resp.status_code == 200:
            match = re.search(r'"accessToken":"([^"]+)"', resp.text)
            if match:
                token = match.group(1)
        
        if token:
            api_url = f"https://betarest.fireant.vn/posts?type=1&offset=0&limit=50"
            api_headers = {
                "User-Agent": HEADERS.get("User-Agent", "Mozilla/5.0"),
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            api_resp = requests.get(api_url, headers=api_headers, timeout=10)
            if api_resp.status_code == 200:
                items = api_resp.json()
                cutoff_time = dt.datetime.now() - dt.timedelta(hours=hours_lookback)
                
                for item in items:
                    post_id = item.get("postID")
                    heading = item.get("title")
                    date_str = item.get("date")
                    
                    if not heading or not post_id or not date_str:
                        continue
                    
                    try:
                        dt_obj = dt.datetime.fromisoformat(date_str).replace(tzinfo=None)
                    except Exception:
                        dt_obj = None
                        
                    if dt_obj and dt_obj < cutoff_time:
                        continue
                        
                    slug = slugify_fireant_title(heading)
                    link = f"https://fireant.vn/bai-viet/{slug}/{post_id}"
                    collected_articles.append({
                        "title": heading,
                        "link": link,
                        "published_at": dt_obj,
                        "feed_url": fireant_url,
                        "source": "FireAnt",
                        "category": categorizer.categorize(heading, link, fireant_url)
                    })
                
                logger.info(f"✓ FireAnt API: {len(collected_articles)} items collected.")
                if collected_articles:
                    return collected_articles
    except Exception as e:
        logger.warning(f"⚠️ FireAnt API Error: {e}. Falling back to Selenium...")
        
    return fetch_fireant_selenium(hours_lookback)

def fetch_fireant_selenium(hours_lookback: int) -> List[Dict]:
    """Fetches FireAnt news using Selenium with improved Time detection."""
    logger.info(">>> [Method 3 Fallback] Starting FireAnt Selenium Scraper...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--log-level=3")
    
    driver = None
    collected_articles = []
    seen_urls = set()
    cutoff_time = dt.datetime.now() - dt.timedelta(hours=hours_lookback)
    fireant_url = "https://fireant.vn/bai-viet"
    scroll_step = 800
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(fireant_url)
        time.sleep(5)

        keep_scrolling = True
        while keep_scrolling:
            links = driver.find_elements(By.XPATH, "//a[contains(@href, '/bai-viet/')]")
            
            for link in links:
                try:
                    url = link.get_attribute("href")
                    if url in seen_urls: continue
                    heading = link.text.strip()
                    if not heading: continue

                    dt_obj = None
                    current_element = link
                    # 1. Check Ancestors
                    for i in range(3):
                        try:
                            parent = current_element.find_element(By.XPATH, "./..")
                            parsed_date = parse_fireant_time(parent.text)
                            if parsed_date:
                                dt_obj = parsed_date
                                break
                            current_element = parent
                        except: break
                    
                    # 2. Check Siblings
                    if not dt_obj:
                         try:
                             meta_info = link.find_element(By.XPATH, "./following::div[1] | ./following::span[1] | ./../following-sibling::div[1]")
                             dt_obj = parse_fireant_time(meta_info.text)
                         except: pass

                    if not dt_obj: continue 

                    if dt_obj < cutoff_time:
                        keep_scrolling = False
                        break
                    
                    seen_urls.add(url)
                    collected_articles.append({
                        "title": heading,
                        "link": url,
                        "published_at": dt_obj,
                        "feed_url": fireant_url,
                        "source": "FireAnt",
                        "category": categorizer.categorize(heading, url, fireant_url)
                    })
                except (StaleElementReferenceException, Exception): continue
            
            if not keep_scrolling: break
            driver.execute_script(f"window.scrollBy(0, {scroll_step});")
            time.sleep(2)
            new_h = driver.execute_script("return document.body.scrollHeight")
            cur_h = driver.execute_script("return window.pageYOffset + window.innerHeight")
            if cur_h >= new_h: break
                    
    except Exception as e:
        logger.error(f"❌ FireAnt Error: {e}")
    finally:
        if driver: driver.quit()
    
    logger.info(f"✓ FireAnt: {len(collected_articles)} items collected.")
    return collected_articles

# --- MODULE 3: RSS SCRAPER ---
def fetch_single_feed(url: str) -> List[Dict]:
    try:
        d = feedparser.parse(url, request_headers=HEADERS)
        if d.bozo and not d.entries: return []
        articles = []
        for e in d.entries:
            link = e.get("link", "").strip()
            title = e.get("title", "").strip()
            if not link or not title: continue
            pub_date = date_parser.parse(e)
            
            articles.append({
                "title": title,
                "link": link,
                "published_at": pub_date,
                "feed_url": url,
                "source": urlparse(link).netloc.replace("www.", "").split('.')[0].title(),
                "category": categorizer.categorize(title, link, url)
            })
        return articles
    except Exception: return []

def fetch_all_feeds_parallel(feeds: List[str]) -> List[Dict]:
    all_articles = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(fetch_single_feed, url): url for url in feeds}
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                data = future.result()
                if data: all_articles.extend(data)
            except Exception: pass
    return all_articles

# --- MODULE 4: BAODAUTU (Requests + BS4) ---

def scrape_baodautu_details(article: Dict) -> Optional[Dict]:
    """Worker function for BaoDautu details."""
    url = article['url']
    title = article['heading']
    soup = get_soup(url)
    if not soup: return None
        
    dt_obj = None

    # Strategy 1: Meta Tags
    meta_date = soup.find("meta", property="article:published_time") or \
                soup.find("meta", itemprop="datePublished")
    if meta_date:
        raw_dt = meta_date.get("content")
        try:
            temp_dt = pd.to_datetime(raw_dt).to_pydatetime()
            dt_obj = temp_dt.replace(tzinfo=None)
        except: pass

    # Strategy 2: Visual Fallback
    if not dt_obj:
        time_el = soup.select_one(".post-time, .author-time, .time, .date")
        if time_el:
            text = time_el.get_text(strip=True).replace("|", " ").replace("-", " ")
            try:
                # Attempt to find generic date pattern
                match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
                if match:
                    d, m, y = map(int, match.groups())
                    # Look for time
                    match_time = re.search(r'(\d{1,2}):(\d{2})', text)
                    if match_time:
                        h, mi = map(int, match_time.groups())
                        dt_obj = dt.datetime(y, m, d, h, mi)
                    else:
                        dt_obj = dt.datetime(y, m, d)
            except: pass

    if not dt_obj: return None

    return {
        "title": title,
        "link": url,
        "published_at": dt_obj,
        "feed_url": "https://baodautu.vn",
        "source": "BaoDautu",
        "category": categorizer.categorize(title, url, "dau-tu")
    }

def fetch_baodautu_multi_category(urls: List[str], hours_lookback: int) -> List[Dict]:
    logger.info(">>> [Method 4] Fetching BaoDautu...")
    
    unique_articles = {} 
    article_pattern = re.compile(r'-d\d+\.html$')

    # 1. Collect Links
    for category_url in urls:
        soup = get_soup(category_url)
        if not soup: continue

        links = soup.find_all("a", href=True)
        for link in links:
            href = link.get('href')
            title = link.get_text(strip=True)
            if not href: continue

            if href.startswith("/"):
                full_url = "https://baodautu.vn" + href.rstrip("/")
            elif href.startswith("http"):
                full_url = href
            else: continue

            if "baodautu.vn" in full_url and article_pattern.search(full_url):
                if full_url not in unique_articles and len(title) > 10:
                    unique_articles[full_url] = {"url": full_url, "heading": title}

    article_list = list(unique_articles.values())
    results = []
    cutoff = dt.datetime.now() - dt.timedelta(hours=hours_lookback)

    # 2. Scrape Details
    # Use fewer workers (max 2) to avoid rate limiting on baodautu.vn
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(scrape_baodautu_details, art) for art in article_list]
        for future in concurrent.futures.as_completed(futures):
            try:
                data = future.result()
                if data and data['published_at']:
                    if data['published_at'] >= cutoff:
                        results.append(data)
            except Exception: pass

    logger.info(f"✓ BaoDautu: {len(results)} items collected.")
    return results

# --- MAIN PROCESSING ---
def process_data(articles: List[Dict]) -> pd.DataFrame:
    if not articles: return pd.DataFrame()
    df = pd.DataFrame(articles)
    
    now = dt.datetime.now(TZ).replace(tzinfo=None)
    cutoff = now - dt.timedelta(hours=HOURS_LOOKBACK)

    # Fill missing dates
    mask_missing = df['published_at'].isna()
    df.loc[mask_missing, 'published_at'] = now - dt.timedelta(minutes=30)

    # Filter recent
    df = df[df['published_at'] >= cutoff].copy()
    
    # Deduplicate
    df.drop_duplicates(subset=['link'], keep='first', inplace=True)
    
    # Format
    df['date'] = df['published_at'].apply(lambda x: x.strftime("%d/%m/%Y"))
    df['time'] = df['published_at'].apply(lambda x: x.strftime("%H:%M"))
    
    cols = ['date', 'time', 'source', 'category', 'title', 'link']
    return df[cols].sort_values(by=['date', 'time'], ascending=[False, False])

def main():
    logger.info("=== COMBINED HYBRID NEWS SCRAPER ===")
    global HOURS_LOOKBACK
    
    import argparse
    parser = argparse.ArgumentParser(description="Combined Hybrid News Scraper")
    parser.add_argument("--hours", type=int, default=None, help="Lookback window in hours (overrides default/automated logic)")
    args, unknown = parser.parse_known_args()
    
    if args.hours is not None:
        HOURS_LOOKBACK = args.hours
        logger.info(f"Using command-line lookback hours: {HOURS_LOOKBACK}")
    else:
        local_now = dt.datetime.now(TZ)
        is_monday = local_now.weekday() == 0
        is_morning = local_now.hour < 12
        if is_monday and is_morning:
            HOURS_LOOKBACK = 72
            logger.info(f"Monday morning detected. Setting default lookback to {HOURS_LOOKBACK} hours.")
        else:
            HOURS_LOOKBACK = 24
            logger.info(f"Defaulting lookback to {HOURS_LOOKBACK} hours.")
            
    all_articles = []

    # 1. RSS
    rss_data = fetch_all_feeds_parallel(RSS_FEEDS)
    all_articles.extend(rss_data)

    # 2. TinNhanhChungKhoan
    tinnhanh_data = fetch_tinnhanh_multi_category(TINNHANH_URLS, HOURS_LOOKBACK)
    all_articles.extend(tinnhanh_data)

    # 3. BaoDautu (NEW)
    baodautu_data = fetch_baodautu_multi_category(BAODAUTU_URLS, HOURS_LOOKBACK)
    all_articles.extend(baodautu_data)

    # 4. FireAnt (API with Selenium Fallback)
    fireant_data = fetch_fireant_api(HOURS_LOOKBACK)
    all_articles.extend(fireant_data)

    # 5. Process
    df = process_data(all_articles)
    
    logger.info(f"\n=== SUMMARY ===")
    logger.info(f"Total Articles: {len(df)}")
    
    if not df.empty:
        logger.info("\nCategory Breakdown:")
        import sys
        sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
        print(df['category'].value_counts().to_string())

        os.makedirs(OUTDIR, exist_ok=True)
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
        fpath = os.path.join(OUTDIR, f"{FILENAME}_{timestamp}.csv")

        df.to_csv(fpath, index=False, encoding='utf-8-sig')
        logger.info(f"\n✅ Saved to: {fpath}")
        print("\nTop 5 Latest News:")
        print(df.head(5).to_string(index=False))
    else:
        logger.warning("No articles met the criteria.")

if __name__ == "__main__":
    main()
