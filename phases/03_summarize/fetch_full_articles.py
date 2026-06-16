"""
fetch_full_articles.py
Reads a reports/{base}/source/*.md file, extracts all article URLs, fetches full content
using requests + BeautifulSoup (same approach as main.py), and writes an
enriched markdown report alongside the original.

Usage:
    python fetch_full_articles.py reports/mor_04_06_2026/source/mor_04_06_2026.md
"""

import re
import sys
import os
import datetime
import concurrent.futures
import requests
import time
from bs4 import BeautifulSoup
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "core_tools" / "paths"))
from report_paths import source_file

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
}
TIMEOUT = 15
MAX_WORKERS = 8

# ── Content extraction ──────────────────────────────────────────────────────

# Ordered list of (selector, is_css) tried in sequence
ARTICLE_SELECTORS = [
    # Site-specific
    ('.ct-edtior-web', True),
    # Generic article body selectors (most sites)
    ('.article-body', True),
    ('.article-content', True),
    ('.post-content', True),
    ('.entry-content', True),
    ('.content-detail', True),
    ('.detail-content', True),
    ('.cms-body', True),
    ('.article__body', True),
    ('.article__content', True),
    # Site-specific
    ('.maincontent', True),
    ('#main-detail-body', True),
    ('.detail__content', True),
    ('.singular-content', True),
    # Fallback: <article> tag
    ('article', True),
    # BaoDautu specific
    ('.nd_body', True),
    ('.detail-news-content', True),
    ('.news-content', True),
    ('.detail-content-body', True),
]

UNWANTED_TAGS = ['script', 'style', 'figure', 'figcaption', 'iframe',
                 'noscript', 'aside', 'nav', 'footer', 'header', 'form',
                 'button', 'input', '.ads', '.advertisement', '.related']


def extract_article_content(soup: BeautifulSoup) -> str:
    """Try a series of selectors to pull the main article body."""
    container = None
    for selector, is_css in ARTICLE_SELECTORS:
        container = soup.select_one(selector) if is_css else soup.find(selector)
        if container:
            break

    if not container:
        # Last resort: largest <div> by text length
        divs = soup.find_all('div')
        if divs:
            container = max(divs, key=lambda d: len(d.get_text()))

    # Even if no container found, try collecting all <p> tags directly from body
    if not container:
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text(separator=' ', strip=True)
            if len(text) >= 40:
                paragraphs.append(text)
        return '\n\n'.join(paragraphs).strip()

    if not container:
        return ''

    # Clean noise
    for tag in container.find_all(True):
        if tag.name in [t for t in UNWANTED_TAGS if not t.startswith('.')]:
            tag.decompose()

    # Extract paragraphs
    paragraphs = []
    for p in container.find_all(['p', 'h2', 'h3', 'h4', 'blockquote', 'li']):
        text = p.get_text(separator=' ', strip=True)
        if len(text) < 20:
            continue
        if p.name in ('h2', 'h3', 'h4'):
            paragraphs.append(f'\n**{text}**\n')
        elif p.name == 'blockquote':
            paragraphs.append(f'> {text}')
        elif p.name == 'li':
            paragraphs.append(f'- {text}')
        else:
            paragraphs.append(text)

    result = '\n\n'.join(paragraphs).strip()

    # If container gave too little, scan all <p> tags in the full page
    if len(result) < 200:
        all_p = []
        for p in soup.find_all('p'):
            text = p.get_text(separator=' ', strip=True)
            if len(text) >= 40:
                all_p.append(text)
        if len('\n\n'.join(all_p)) > len(result):
            result = '\n\n'.join(all_p).strip()

    return result


def extract_meta_description(soup: BeautifulSoup) -> str:
    tag = (soup.find('meta', attrs={'name': 'description'}) or
           soup.find('meta', property='og:description'))
    return tag.get('content', '').strip() if tag else ''


def extract_published_time(soup: BeautifulSoup) -> str:
    tag = (soup.find('meta', property='article:published_time') or
           soup.find('meta', itemprop='datePublished'))
    if tag:
        raw = tag.get('content', '')
        try:
            dt = datetime.datetime.fromisoformat(raw.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M')
        except Exception:
            return raw[:16]
    return ''


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


def fetch_article(url: str, session: requests.Session = None) -> dict:
    """Fetch one article and return a dict with metadata + content."""
    result = {'url': url, 'title': '', 'published': '', 'description': '',
              'content': '', 'error': None}
    if session is None:
        session = get_session()
    try:
        resp = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code != 200:
            result['error'] = f'HTTP {resp.status_code}'
            return result
        # Decode Vietnamese correctly
        resp.encoding = resp.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Title
        og_title = soup.find('meta', property='og:title')
        result['title'] = (og_title.get('content', '').strip()
                           if og_title else
                           (soup.title.string.strip() if soup.title else ''))

        result['published'] = extract_published_time(soup)
        result['description'] = extract_meta_description(soup)
        result['content'] = extract_article_content(soup)

        if not result['content']:
            result['error'] = 'Could not extract article body'

    except requests.exceptions.HTTPError as e:
        result['error'] = f'HTTP {e.response.status_code}'
    except requests.exceptions.ConnectionError:
        result['error'] = 'Connection error'
    except requests.exceptions.Timeout:
        result['error'] = 'Timeout'
    except Exception as e:
        result['error'] = str(e)

    return result


# ── Markdown parsing ────────────────────────────────────────────────────────

URL_RE = re.compile(r'<(https?://[^>]+)>|(?<!\()(https?://\S+?)(?=[)\s]|$)')
SECTION_RE = re.compile(r'^## (.+)', re.MULTILINE)
ARTICLE_BLOCK_RE = re.compile(
    r'### (.+?)\n((?:- \*\*.+?\*\*.*\n)*(?:- \*\*URL:\*\* <.+?>)?\n?)',
    re.MULTILINE
)


def parse_report(path: str):
    """
    Returns list of dicts:
        { section, title, source, category, url }
    """
    with open(path, encoding='utf-8') as f:
        text = f.read()

    entries = []
    current_section = 'General'

    for line in text.splitlines():
        section_m = re.match(r'^## (.+)', line)
        if section_m:
            current_section = section_m.group(1).strip()
            continue

        title_m = re.match(r'^### (.+)', line)
        if title_m:
            entries.append({
                'section': current_section,
                'title': title_m.group(1).strip(),
                'source': '', 'category': '', 'url': ''
            })
            continue

        if entries:
            src_m = re.search(r'\*\*Source:\*\*\s*(.+?)\s*\|', line)
            if src_m:
                entries[-1]['source'] = src_m.group(1).strip()
            cat_m = re.search(r'\*\*Category:\*\*\s*(.+)', line)
            if cat_m:
                entries[-1]['category'] = cat_m.group(1).strip()
            url_m = re.search(r'<(https?://[^>]+)>', line)
            if url_m:
                entries[-1]['url'] = url_m.group(1).strip()

    return [e for e in entries if e['url']]


# ── Report generation ───────────────────────────────────────────────────────

def build_full_report(source_path: str, entries: list[dict],
                      fetched: dict[str, dict]) -> str:
    now = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    basename = os.path.basename(source_path)
    lines = [
        f'# Full Article Report — {basename}',
        f'> Fetched: {now}  |  Articles: {len(entries)}',
        '',
    ]

    # Group by section
    sections: dict[str, list] = {}
    for e in entries:
        sections.setdefault(e['section'], []).append(e)

    for section, arts in sections.items():
        lines.append(f'## {section}')
        lines.append('')
        for art in arts:
            url = art['url']
            fetched_data = fetched.get(url, {})
            error = fetched_data.get('error')

            fetched_title = fetched_data.get('title', '') or art['title']
            published = fetched_data.get('published', '')
            description = fetched_data.get('description', '')
            content = fetched_data.get('content', '')

            lines.append(f'### {fetched_title}')
            lines.append('')

            meta_parts = []
            if art['source']:
                meta_parts.append(f'**Source:** {art["source"]}')
            if art['category']:
                meta_parts.append(f'**Category:** {art["category"]}')
            if published:
                meta_parts.append(f'**Published:** {published}')
            if meta_parts:
                lines.append('  '.join(meta_parts))

            lines.append(f'**URL:** <{url}>')
            lines.append('')

            if error:
                lines.append(f'> ⚠️ Could not fetch article content: {error}')
            else:
                if description:
                    lines.append(f'**Summary:** {description}')
                    lines.append('')
                if content:
                    lines.append('**Full Content:**')
                    lines.append('')
                    lines.append(content)
                else:
                    lines.append('> _(No article body extracted)_')

            lines.append('')
            lines.append('---')
            lines.append('')

    return '\n'.join(lines)


# ── Entry point ─────────────────────────────────────────────────────────────

RATE_LIMITED_DOMAINS = ['tinnhanhchungkhoan.vn', 'baodautu.vn']

def is_rate_limited(url: str) -> bool:
    return any(domain in url for domain in RATE_LIMITED_DOMAINS)

def main():
    if len(sys.argv) < 2:
        print('Usage: python fetch_full_articles.py <path/to/report.md>')
        sys.exit(1)

    source_path = sys.argv[1]
    if not os.path.exists(source_path):
        print(f'File not found: {source_path}')
        sys.exit(1)

    print(f'Parsing report: {source_path}')
    entries = parse_report(source_path)
    print(f'Found {len(entries)} article(s) to fetch.')

    urls = [e['url'] for e in entries]
    session = get_session()

    # Separate URLs into sensitive and standard
    sensitive_urls = [url for url in urls if is_rate_limited(url)]
    standard_urls = [url for url in urls if not is_rate_limited(url)]

    fetched: dict[str, dict] = {}

    # 1. Fetch standard URLs in parallel
    if standard_urls:
        print(f'\nFetching {len(standard_urls)} standard article(s) in parallel...')
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            future_map = {ex.submit(fetch_article, url, session): url for url in standard_urls}
            for i, future in enumerate(concurrent.futures.as_completed(future_map), 1):
                url = future_map[future]
                result = future.result()
                fetched[url] = result
                status = 'OK' if not result['error'] else f'ERR {result["error"]}'
                print(f'  [Parallel {i}/{len(standard_urls)}] {status}  {url}')

    # 2. Fetch sensitive URLs sequentially
    if sensitive_urls:
        print(f'\nFetching {len(sensitive_urls)} rate-limited article(s) sequentially with delay...')
        for idx, url in enumerate(sensitive_urls, 1):
            if idx > 1:
                time.sleep(1.2)  # Delay between requests to prevent rate limit
            result = fetch_article(url, session)
            fetched[url] = result
            status = 'OK' if not result['error'] else f'ERR {result["error"]}'
            print(f'  [Sequential {idx}/{len(sensitive_urls)}] {status}  {url}')

    # 3. Robust sequential retry fallback for failed fetches
    failed_urls = [url for url, res in fetched.items() if res['error']]
    if failed_urls:
        print(f'\nRetrying {len(failed_urls)} failed fetch(es) sequentially with increased delay...')
        for idx, url in enumerate(failed_urls, 1):
            time.sleep(2.0)  # Exponential backoff delay
            result = fetch_article(url, session)
            fetched[url] = result
            status = 'OK' if not result['error'] else f'ERR {result["error"]}'
            print(f'  [Retry {idx}/{len(failed_urls)}] {status}  {url}')

    report_text = build_full_report(source_path, entries, fetched)

    report_base = Path(source_path).stem
    out_path = source_file(report_base, "full")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f'\nFull report saved to: {out_path}')


if __name__ == '__main__':
    main()
