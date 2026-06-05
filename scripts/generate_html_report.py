#!/usr/bin/env python3
"""
generate_html_report.py — Vietnam Financial News Bulletin HTML generator.

Reads 4 JSON category files and produces TWO branded, print-ready A4 HTML
reports: one Vietnamese (`*_report_vn.html`) and one English (`*_report_en.html`).

Layout rules:
  - A4 fixed canvas, white background on every page.
  - Max 4 news items per content page (2 columns x 2 rows).
  - Each content page carries a footer with the company logo.
  - Title + body use Arial at 20px.
  - No source attribution, no per-item date shown.

Usage:
    python scripts/generate_html_report.py after_04_06_2026
    python scripts/generate_html_report.py          # auto-detect latest
"""
import html as html_mod
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_paths import export_file, find_data_file, find_latest_base
from news_title_rules import normalized_item_title, ticker_company_exchange_title

ASSET_ROOT = "../../../../news_html_template"
IMG_BASE = f"{ASSET_ROOT}/image_library"
LOGO_PATH = f"{ASSET_ROOT}/company-logo.jpg"

MAX_PER_PAGE = 4
MAX_TITLE_CHARS = 100
MAX_SUMMARY_CHARS = None

SECTION_IMAGE: dict[str, str] = {
    "macro":                  "macro & trading/macro_1.jpg",
    "trading":                "macro & trading/trading_1.jpg",
    "banking":                "banks & financials/banks_1.jpg",
    "financials":             "banks & financials/financials_1.jpg",
    "consumers":              "consumers/consumers_1.jpg",
    "industrials":            "industrials & materials/industrials_1.jpg",
    "materials":              "industrials & materials/materials_1.jpg",
    "real_estate":            "real_estate/real_estate_1.jpg",
    "technologies":           "technologies/technologies_1.jpg",
    "pharma":                 "pharma/pharma_1.jpg",
    "utilities":              "uilities_oil&gas/utilities_1.jpg",
    "oil_gas":                "uilities_oil&gas/oil_gas_1.jpg",
    "policies":               "political/policies_1.jpg",
    "social":                 "political/social_1.jpg",
    "political":              "political/political_1.jpg",
    "economies_investments":  "political/economies_investments_1.jpg",
    "international_relation": "political/international_relation_1.jpg",
    "commodities":            "commodities/commodities.jpg",
    "others":                 "political/others_1.jpg",
}

SESSION_CONFIG: dict[str, dict] = {
    "mor":   {
        "label_en": "Morning News", "label_vn": "Bản tin buổi sáng",
        "cover_bg": "background/mor_intro_background.jpg",
        "outro_bg": "background/mor_outro_background.jpg",
    },
    "after": {
        "label_en": "Afternoon News", "label_vn": "Bản tin buổi chiều",
        "cover_bg": "background/after_intro_background.jpg",
        "outro_bg": "background/after_outro_background.jpg",
    },
}

PRE_CORPORATE_SUBTYPES = ["commodities"]
POST_CORPORATE_SUBTYPES = [
    "political", "policies", "economies_investments", "social",
    "international_relation", "others",
]

MONTHS_EN = ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]

UI = {
    "vn": {"toc": "Trong báo cáo này", "cont": "(tiếp theo)", "thanks": "Trân Trọng Cảm Ơn",
           "tagline": "KIS Việt Nam · Bản tin thị trường",
           "cover_note": "KIS Vietnam 2026. Các thông tin trên dựa trên nguồn báo chí, chưa được kiểm chứng tính xác thực và không hàm ý khuyến nghị đầu tư mua bán nào. Nhà đầu tư cần cân nhắc kỹ rủi ro trước khi đưa ra quyết định."},
    "en": {"toc": "In this report", "cont": "(cont.)", "thanks": "Thank You",
           "tagline": "KIS Securities Vietnam · Market Intelligence",
           "cover_note": "KIS Vietnam 2026. The information herein is sourced from publicly available media, has not been independently verified, and does not constitute investment advice or a recommendation to buy or sell. Investors should carefully consider risks before making any investment decision."},
}


def esc(s: str) -> str:
    return html_mod.escape(s or "", quote=True)


def truncate_text(s: str, limit: int | None) -> str:
    if not limit or len(s) <= limit:
        return s
    return s[:limit].rstrip()


def img_url(filename: str) -> str:
    return f"{IMG_BASE}/{filename}".replace("&", "%26").replace(" ", "%20")


def section_img(key: str) -> str:
    return img_url(SECTION_IMAGE.get(key, "political/others_1.jpg"))


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_date(report_base: str) -> str:
    parts = report_base.split("_")
    try:
        day, month, year = int(parts[1]), int(parts[2]), int(parts[3])
        return f"{day:02d} {MONTHS_EN[month - 1]} {year}"
    except (IndexError, ValueError):
        return report_base


def parse_date_dots(report_base: str) -> str:
    parts = report_base.split("_")
    try:
        day, month, year = int(parts[1]), int(parts[2]), int(parts[3])
        return f"{day:02d}.{month:02d}.{year}"
    except (IndexError, ValueError):
        return report_base


# ---------------------------------------------------------------------------
# Card
# ---------------------------------------------------------------------------

def render_card(item: dict, lang: str, section_title: str, category: str = "") -> str:
    title_raw = truncate_text(item.get(f"title_{lang}", ""), MAX_TITLE_CHARS)
    summ_raw  = truncate_text(item.get(f"summary_{lang}", ""), MAX_SUMMARY_CHARS)
    title = esc(title_raw)
    summ = esc(summ_raw)
    
    if category in ("corporate", "trading"):
        heading = esc(ticker_company_exchange_title(item, lang))
        body = summ
    else:
        heading = title or esc(section_title)
        body = summ

    return (f'    <article class="story">\n'
            f'      <h3>{heading}</h3>\n'
            f'      <p>{body}</p>\n'
            f'    </article>')


# ---------------------------------------------------------------------------
# Section model -> paginated A4 pages
# ---------------------------------------------------------------------------

def collect_sections(report_base: str) -> list[dict]:
    """Return ordered list of sections: {title_vn, title_en, key, items, corp}."""
    out: list[dict] = []
    macro   = load_json(find_data_file(report_base, "macro"))
    trading = load_json(find_data_file(report_base, "trading"))
    corp    = load_json(find_data_file(report_base, "corporate"))
    epo     = load_json(find_data_file(report_base, "economy_political_others"))

    if macro and macro.get("item_count", 0) > 0:
        out.append({"vn": macro["section_title_vn"], "en": macro["section_title_en"],
                    "key": "macro", "category": "macro", "items": macro["items"], "corp": False})
    if trading and trading.get("item_count", 0) > 0:
        out.append({"vn": trading["section_title_vn"], "en": trading["section_title_en"],
                    "key": "trading", "category": "trading", "items": trading["items"], "corp": False})
    if epo and epo.get("item_count", 0) > 0:
        by_key = {st["subtype_key"]: st for st in epo.get("subtypes", [])}
        for key in PRE_CORPORATE_SUBTYPES:
            st = by_key.get(key)
            if st and st.get("items"):
                out.append({"vn": st["section_title_vn"], "en": st["section_title_en"],
                            "key": key, "category": "economy_political_others", "items": st["items"], "corp": False})
    if corp and corp.get("item_count", 0) > 0:
        for sec in corp.get("sectors", []):
            if sec.get("items"):
                out.append({"vn": sec["section_title_vn"], "en": sec["section_title_en"],
                            "key": sec["sector_key"], "category": "corporate", "items": sec["items"], "corp": True})
    if epo and epo.get("item_count", 0) > 0:
        by_key = {st["subtype_key"]: st for st in epo.get("subtypes", [])}
        for key in POST_CORPORATE_SUBTYPES:
            st = by_key.get(key)
            if st and st.get("items"):
                out.append({"vn": st["section_title_vn"], "en": st["section_title_en"],
                            "key": key, "category": "economy_political_others", "items": st["items"], "corp": False})
    return out


def render_pages(sections: list[dict], lang: str) -> str:
    pages: list[str] = []
    page_no = 1
    for sec in sections:
        items = sec["items"]
        chunks = [items[i:i + MAX_PER_PAGE] for i in range(0, len(items), MAX_PER_PAGE)]
        for ci, chunk in enumerate(chunks):
            title = sec["vn"] if lang == "vn" else sec["en"]
            sub   = sec["en"] if lang == "vn" else sec["vn"]
            cards = "\n".join(
                render_card(
                    {**it, f"title_{lang}": normalized_item_title(it, sec["category"], lang)},
                    lang,
                    title,
                    sec["category"],
                )
                for it in chunk
            )
            cont  = f' <span class="cont">{UI[lang]["cont"]}</span>' if ci > 0 else ""
            banner = (
                f'  <div class="sec-banner" style="background-image:url(\'{section_img(sec["key"])}\')"></div>\n'
                f'  <main class="content-wrap">\n'
                f'    <h2 class="sec-title">{esc(title)}{cont}</h2>\n'
                f'    <p class="sec-sub">{esc(sub)}</p>\n'
                f'    <div class="story-grid">\n{cards}\n    </div>\n'
                f'  </main>'
            )
            pages.append(
                f'<div class="page-content">\n'
                f'{banner}\n'
                f'  <footer class="page-footer"><img class="footer-logo" src="{LOGO_PATH}" alt="KIS"><span>{page_no:02d}</span></footer>\n'
                f'</div>'
            )
            page_no += 1
    return "\n".join(pages)


def toc_lines(sections: list[dict], lang: str) -> str:
    lines = []
    for sec in sections:
        label = sec["vn"] if lang == "vn" else sec["en"]
        lines.append(f'          <li>{esc(label)} <span class="toc-n">({len(sec["items"])})</span></li>')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------

def generate(report_base: str, lang: str) -> str:
    session = "after" if "after" in report_base else "mor"
    cfg     = SESSION_CONFIG[session]
    date_en = parse_date(report_base)
    date_dots = parse_date_dots(report_base)
    sections = collect_sections(report_base)
    ui = UI[lang]

    cover_bg = img_url(cfg["cover_bg"])
    outro_bg = img_url(cfg["outro_bg"])
    label = cfg["label_vn"] if lang == "vn" else cfg["label_en"]
    title = f"KIS Vietnam — {date_en} {cfg['label_en']} ({lang.upper()})"

    doc = _HTML_TEMPLATE
    for ph, val in [
        ("__LANG__",     lang),
        ("__TITLE__",    title),
        ("__DATE_EN__",  date_en),
        ("__DATE_DOTS__", date_dots),
        ("__SESSION__",  label),
        ("__COVER_BG__", cover_bg),
        ("__OUTRO_BG__", outro_bg),
        ("__LOGO__",     LOGO_PATH),
        ("__TOC_LABEL__", ui["toc"]),
        ("__TOC__",      toc_lines(sections, lang)),
        ("__THANKS__",   ui["thanks"]),
        ("__TAGLINE__",  ui["tagline"]),
        ("__COVER_NOTE__", ui["cover_note"]),
        ("__BODY__",     render_pages(sections, lang)),
    ]:
        doc = doc.replace(ph, val)
    return doc


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="__LANG__">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>__TITLE__</title>
  <style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

:root{
  --brown:#6f3f26;
  --brown-line:#8b4a22;
  --ink:#080808;
  --paper:#ffffff;
  --cover-paper:#f2e4d2;
  --pw:210mm; --ph:297mm;
}

html{font-size:20px}
body{font-family:Arial,Helvetica,sans-serif;background:#d8d8d8;color:var(--ink);line-height:1.28}

.page-full,.page-content{
  width:var(--pw);height:var(--ph);
  margin:0 auto 18px;background:#fff;position:relative;overflow:hidden;
}

.page-full{background-size:cover;background-position:center}
.cover-over{position:absolute;inset:0;padding:62px 38px 34px;background:rgba(242,228,210,.25)}
.cover-company{font-size:54px;font-weight:800;line-height:1.28;color:#000;text-transform:uppercase;max-width:760px}
.cover-date{font-size:21px;margin:34px 0 0 8px;color:#000}
.cover-title{position:absolute;right:38px;bottom:104px;text-align:right}
.cover-session{font-size:49px;font-weight:bold;line-height:1;color:#000;text-transform:uppercase}
.cover-sub{font-size:20px;margin-top:12px;color:#000}
.cover-note{position:absolute;left:68px;right:70px;bottom:50px;font-size:14px;line-height:1.16;color:#909090}

.page-content{display:flex;flex-direction:column}
.sec-banner{height:400px;background-size:cover;background-position:center;border-bottom:5px solid var(--brown-line);flex-shrink:0}
.content-wrap{padding:36px 46px 86px;flex:1;overflow:hidden}
.sec-title{font-size:39px;font-weight:bold;color:var(--brown);text-transform:uppercase;line-height:1.05;margin-bottom:54px}
.sec-title .cont{font-size:20px;font-weight:400;text-transform:none}
.sec-sub{display:none}
.story-grid{display:grid;grid-template-columns:1fr 1fr;column-gap:70px;row-gap:62px}
.story{overflow:hidden}
.story h3{font-size:15px;font-weight:bold;color:var(--brown);line-height:1.18;margin-bottom:4px}
.story p{font-size:15px;font-weight:400;color:#000;line-height:1.3;text-align:justify}

.page-footer{position:absolute;left:48px;right:44px;bottom:17px;height:41px;border-top:2px solid var(--brown-line);display:flex;align-items:center;justify-content:space-between;background:#fff}
.footer-logo{width:96px;height:24px;object-fit:cover;object-position:center}
.page-footer span{font-size:26px;color:var(--brown)}

.outro-over{position:absolute;inset:0;color:#fff;text-align:center}
.outro-company{position:absolute;top:350px;left:48px;right:48px;font-size:24px;font-weight:800;line-height:1.12;text-transform:uppercase;letter-spacing:0;white-space:nowrap}
.outro-thanks-row{position:absolute;top:420px;left:52px;right:52px;display:flex;align-items:center;gap:14px}
.outro-rule{height:1px;flex:1;background:rgba(255,255,255,.78)}
.outro-ty{font-size:28px;font-weight:400;color:#fff;line-height:1;text-transform:uppercase;white-space:nowrap}
.outro-copy{position:absolute;left:26px;right:auto;bottom:20px;font-size:12px;line-height:1.15;color:#fff;text-align:left}

@media print{
  @page{size:A4;margin:0}
  html,body{background:#fff}
  .page-full,.page-content{margin:0;page-break-after:always;break-after:page}
  .story{break-inside:avoid}
}
@media screen{body{padding:20px 0}}
  </style>
</head>
<body>

<!-- COVER -->
<div class="page-full" style="background-image:url('__COVER_BG__')">
  <div class="cover-over">
    <div class="cover-company">KIS Vietnam Securities Corporation</div>
    <div class="cover-date">__DATE_DOTS__</div>
    <div class="cover-title">
      <div class="cover-session">__SESSION__</div>
      <div class="cover-sub">__TAGLINE__</div>
    </div>
    <div class="cover-note">__COVER_NOTE__</div>
  </div>
</div>

<!-- BODY -->
__BODY__

<!-- OUTRO -->
<div class="page-full" style="background-image:url('__OUTRO_BG__')">
  <div class="outro-over">
    <div class="outro-company">KIS Vietnam Securities Corporation</div>
    <div class="outro-thanks-row">
      <div class="outro-rule"></div>
      <div class="outro-ty">Thank You</div>
      <div class="outro-rule"></div>
    </div>
    <div class="outro-copy">Copyright © 2026 by KIS Vietnam Securities Corporation.<br>All rights reserved.</div>
  </div>
</div>

</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def auto_detect() -> str:
    return find_latest_base()


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else auto_detect()
    print(f"Generating: {base}")
    for lang in ("vn", "en"):
        out = export_file(base, "html", f"{base}_report_{lang}.html")
        out.write_text(generate(base, lang), encoding="utf-8")
        print(f"  [{lang}] saved -> {out}")
