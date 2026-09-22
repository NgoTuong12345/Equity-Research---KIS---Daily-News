#!/usr/bin/env python3
"""
generate_html_report_standard.py — Vietnam Financial News Bulletin HTML generator (Production Standard).

Reads 4 JSON category files and produces TWO branded, print-ready A4 HTML
reports: one Vietnamese (`*_report_vn.html`) and one English (`*_report_en.html`).

Layout rules:
  - A4 fixed canvas, white background on every page.
  - Max 4 news items per content page (2 columns x 2 rows).
  - Each content page carries a footer with the company logo.
  - Title + body use Arial at 15px.
  - Cover header and session titles use Segoe UI Black (font-weight: 900) for full diacritic support.
  - Standardized Outro back-cover formatting.
  - No source attribution, no per-item date shown.

Usage:
    python phases/04_publish/generate_html_report_standard.py after_20_08_2026
    python phases/04_publish/generate_html_report_standard.py          # auto-detect latest
"""
import html as html_mod
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "core_tools" / "paths"))
sys.path.insert(0, str(BASE_DIR / "llm_brain" / "prompts_and_rules"))
from report_paths import export_file, find_data_file, find_latest_base
from news_title_rules import normalized_item_title, ticker_company_exchange_title
from coversheet import get_coversheet_config

ASSET_ROOT = "../../../../core_tools/templates"
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
        "header_en": "Morning News", "header_vn": "Bản tin buổi sáng",
        "session_title_en": "Market Espresso", "session_title_vn": "Cafe Chứng Khoán",
        "label_en": "Morning News", "label_vn": "Bản tin buổi sáng",
        "cover_bg": "background/mor_intro_background.jpg",
        "outro_bg": "background/mor_outro_background.jpg",
    },
    "after": {
        "header_en": "Afternoon News", "header_vn": "Bản tin buổi chiều",
        "session_title_en": "THE POST-MARKET TEA", "session_title_vn": "TRÀ CHIỀU CHỨNG KHOÁN",
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
    "vn": {
        "toc": "Trong báo cáo này",
        "cont": "(tiếp theo)",
        "thanks": "Trân Trọng Cảm Ơn",
        "tagline": "Trung tâm Phân Tích - Bản Tin Tổng Hợp",
        "cover_note": "Bản tin này được thực hiện bởi Bộ phận Phân tích và Nghiên cứu của Công ty Cổ phần Chứng khoán KIS Việt Nam (\"KIS\"), với sự hỗ trợ của các công cụ trí tuệ nhân tạo (AI) trong việc tổng hợp, phân tích và biên soạn nội dung. KIS không đưa ra bất kỳ khuyến nghị đầu tư, tuyên bố hay bảo đảm nào, dù rõ ràng hay ngụ ý, về tính chính xác, công bằng, đầy đủ hoặc kịp thời của các thông tin được cung cấp ở trên. Người đọc được khuyến nghị nên độc lập xác minh và đánh giá thông tin trước khi dựa vào hoặc sử dụng.",
        "outro_company": "CTCP CHỨNG KHOÁN KIS VIỆT NAM",
        "outro_thanks": "TRÂN TRỌNG CẢM ƠN",
        "outro_copy": "Bản quyền © 2026 thuộc về CTCP Chứng khoán KIS Việt Nam.<br>Bảo lưu mọi quyền.",
    },
    "en": {
        "toc": "In this report",
        "cont": "(cont.)",
        "thanks": "Thank You",
        "tagline": "Research Division - Comprehensive Bulletin",
        "cover_note": "This bulletin is prepared by the Research Department of KIS Vietnam Securities Corporation (\"KIS\"), with the assistance of artificial intelligence (AI) tools in synthesizing, analyzing, and compiling content. KIS makes no investment recommendation, representation, or warranty, whether express or implied, regarding the accuracy, fairness, completeness, or timeliness of the information provided above. Readers are advised to independently verify and evaluate the information before relying upon or using it.",
        "outro_company": "KIS VIETNAM SECURITIES CORPORATION",
        "outro_thanks": "THANK YOU",
        "outro_copy": "Copyright © 2026 by KIS Vietnam Securities Corporation.<br>All rights reserved.",
    },
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
    summ = esc(summ_raw).replace("\r\n", "\n").replace("\n", "<br>\n")
    
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
    session = "afternoon" if "after" in report_base else "morning"
    cfg_cover = get_coversheet_config(session, lang, report_base)
    session_key = "after" if "after" in report_base else "mor"
    cfg     = SESSION_CONFIG[session_key]
    date_en = parse_date(report_base)
    date_dots = cfg_cover["date_dots"]
    sections = collect_sections(report_base)
    ui = UI[lang]

    cover_bg = img_url(cfg_cover["bg_image_rel"])
    outro_bg = img_url(cfg["outro_bg"])
    cover_header = cfg_cover["top_title"]
    session_title = cfg_cover["bottom_title"]
    tagline = cfg_cover["subtitle"]
    cover_note = cfg_cover["disclaimer"]
    title = f"KIS Vietnam — {date_en} {cfg['label_en']} ({lang.upper()})"

    doc = _HTML_TEMPLATE
    for ph, val in [
        ("__LANG__",          lang),
        ("__TITLE__",         title),
        ("__DATE_EN__",       date_en),
        ("__DATE_DOTS__",     date_dots),
        ("__COVER_HEADER__",  cover_header),
        ("__SESSION__",       session_title),
        ("__COVER_BG__",      cover_bg),
        ("__OUTRO_BG__",      outro_bg),
        ("__LOGO__",          LOGO_PATH),
        ("__TOC_LABEL__",     ui["toc"]),
        ("__TOC__",           toc_lines(sections, lang)),
        ("__THANKS__",        ui["thanks"]),
        ("__TAGLINE__",       tagline),
        ("__COVER_NOTE__",    cover_note),
        ("__OUTRO_COMPANY__", ui["outro_company"]),
        ("__OUTRO_THANKS__",  ui["outro_thanks"]),
        ("__OUTRO_COPY__",    ui["outro_copy"]),
        ("__BODY__",          render_pages(sections, lang)),
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
.cover-over{position:absolute;inset:0;padding:62px 38px 34px;background:transparent}
.cover-top,.cover-company{font-family:'Segoe UI Black','Segoe UI',Arial,sans-serif;font-size:48px;font-weight:900;line-height:1.15;color:#000;text-transform:uppercase;max-width:760px;text-align:left;letter-spacing:-0.5px;white-space:nowrap}
.cover-date{font-family:Arial,Helvetica,sans-serif;font-size:21px;font-weight:bold;margin:18px 0 0 0;color:#000;text-align:left}
.cover-bottom-wrap,.cover-title{position:absolute;right:38px;bottom:185px;text-align:right}
.cover-bottom,.cover-session{font-family:'Segoe UI Black','Segoe UI',Arial,sans-serif;font-size:44px;font-weight:900;line-height:1.1;color:#000;text-transform:uppercase;letter-spacing:-0.5px;white-space:nowrap}
.cover-sub{font-family:Arial,Helvetica,sans-serif;font-size:20px;font-weight:normal;margin-top:12px;color:#000;text-align:right}
.cover-note{position:absolute;left:68px;right:70px;bottom:35px;font-family:Arial,Helvetica,sans-serif;font-size:12.5px;line-height:1.35;color:#7a7a7a;text-align:justify}

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
    <div class="cover-top cover-company">__COVER_HEADER__</div>
    <div class="cover-date">__DATE_DOTS__</div>
    <div class="cover-bottom-wrap cover-title">
      <div class="cover-bottom cover-session">__SESSION__</div>
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
    <div class="outro-company">__OUTRO_COMPANY__</div>
    <div class="outro-thanks-row">
      <div class="outro-rule"></div>
      <div class="outro-ty">__OUTRO_THANKS__</div>
      <div class="outro-rule"></div>
    </div>
    <div class="outro-copy">__OUTRO_COPY__</div>
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
