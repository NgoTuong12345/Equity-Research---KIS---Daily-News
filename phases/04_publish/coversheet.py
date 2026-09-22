"""
coversheet.py — Master dynamic coversheet system for KIS Vietnam News Bulletins.

Controlled by three variables:
  - session: 'morning' (or 'mor') / 'afternoon' (or 'after')
  - language: 'vi' (or 'vn') / 'en'
  - date: 'DD.MM.YYYY' (e.g. '08.09.2026')

Preserves the locked background artwork (horse illustration, roof/fan decoration,
flowers, circular ornaments, horizontal lines, cream/beige for morning, sage-green
for afternoon). Only the text layer is dynamic.
"""
from __future__ import annotations

import re
from typing import TypedDict


class CoversheetConfig(TypedDict):
    session: str          # 'morning' | 'afternoon'
    language: str         # 'vi' | 'en'
    date_dots: str        # 'DD.MM.YYYY'
    top_title: str        # e.g. 'BẢN TIN BUỔI SÁNG' / 'MORNING NEWS'
    bottom_title: str     # e.g. 'CAFE CHỨNG KHOÁN' / 'MARKET ESPRESSO'
    subtitle: str         # e.g. 'Trung tâm Phân Tích - Bản Tin Tổng Hợp'
    disclaimer: str       # Full bilingual AI & research disclaimer
    bg_image_rel: str     # 'background/mor_intro_background.jpg' | 'background/after_intro_background.jpg'


# Text content dictionary per (session, language)
_COVERSHEET_TEXTS = {
    ("morning", "vi"): {
        "top_title": "BẢN TIN BUỔI SÁNG",
        "bottom_title": "CAFE CHỨNG KHOÁN",
        "subtitle": "Trung tâm Phân Tích - Bản Tin Tổng Hợp",
        "bg_image_rel": "background/mor_intro_background.jpg",
    },
    ("morning", "en"): {
        "top_title": "MORNING NEWS",
        "bottom_title": "MARKET ESPRESSO",
        "subtitle": "Research Division - Comprehensive Bulletin",
        "bg_image_rel": "background/mor_intro_background.jpg",
    },
    ("afternoon", "vi"): {
        "top_title": "BẢN TIN BUỔI CHIỀU",
        "bottom_title": "TRÀ CHIỀU CHỨNG KHOÁN",
        "subtitle": "Trung tâm Phân Tích - Bản Tin Tổng Hợp",
        "bg_image_rel": "background/after_intro_background.jpg",
    },
    ("afternoon", "en"): {
        "top_title": "AFTERNOON NEWS",
        "bottom_title": "THE POST-MARKET TEA",
        "subtitle": "Research Division - Comprehensive Bulletin",
        "bg_image_rel": "background/after_intro_background.jpg",
    },
}

_DISCLAIMERS = {
    "vi": (
        "Bản tin này được thực hiện bởi Bộ phận Phân tích và Nghiên cứu của Công ty Cổ phần Chứng khoán KIS Việt Nam (\"KIS\"), "
        "với sự hỗ trợ của các công cụ trí tuệ nhân tạo (AI) trong việc tổng hợp, phân tích và biên soạn nội dung. "
        "KIS không đưa ra bất kỳ khuyến nghị đầu tư, tuyên bố hay bảo đảm nào, dù rõ ràng hay ngụ ý, về tính chính xác, "
        "công bằng, đầy đủ hoặc kịp thời của các thông tin được cung cấp ở trên. Người đọc được khuyến nghị nên độc lập "
        "xác minh và đánh giá thông tin trước khi dựa vào hoặc sử dụng."
    ),
    "en": (
        "This bulletin is prepared by the Research Department of KIS Vietnam Securities "
        "Corporation (\"KIS\"), with the assistance of artificial intelligence (AI) tools "
        "in synthesizing, analyzing, and compiling content. KIS makes no investment "
        "recommendation, representation, or warranty, whether express or implied, regarding "
        "the accuracy, fairness, completeness, or timeliness of the information provided above. "
        "Readers are advised to independently verify and evaluate the information before relying "
        "upon or using it."
    ),
}


def normalize_session(raw: str) -> str:
    """Normalize session string to 'morning' or 'afternoon'."""
    s = (raw or "").strip().lower()
    if "after" in s:
        return "afternoon"
    return "morning"


def normalize_language(raw: str) -> str:
    """Normalize language string to 'vi' or 'en'."""
    l = (raw or "").strip().lower()
    if l in ("vi", "vn", "vietnamese"):
        return "vi"
    return "en"


def normalize_date_dots(raw: str) -> str:
    """
    Ensure date string is formatted as DD.MM.YYYY.
    Handles 'mor_08_09_2026', 'after_08_09_2026', '08/09/2026', '2026-09-08', etc.
    """
    s = (raw or "").strip()
    # Match mor_DD_MM_YYYY or after_DD_MM_YYYY
    m = re.search(r"(?:mor|after)_(\d{1,2})_(\d{1,2})_(\d{4})", s)
    if m:
        return f"{int(m.group(1)):02d}.{int(m.group(2)):02d}.{m.group(3)}"

    # Match DD.MM.YYYY
    m = re.search(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", s)
    if m:
        return f"{int(m.group(1)):02d}.{int(m.group(2)):02d}.{m.group(3)}"

    # Match DD/MM/YYYY or DD-MM-YYYY
    m = re.search(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", s)
    if m:
        return f"{int(m.group(1)):02d}.{int(m.group(2)):02d}.{m.group(3)}"

    # Match YYYY-MM-DD
    m = re.search(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        return f"{int(m.group(3)):02d}.{int(m.group(2)):02d}.{m.group(1)}"

    return s


def get_coversheet_config(session: str, language: str, date: str) -> CoversheetConfig:
    """Return structured coversheet configuration for the given combination."""
    norm_sess = normalize_session(session)
    norm_lang = normalize_language(language)
    date_dots = normalize_date_dots(date)

    texts = _COVERSHEET_TEXTS[(norm_sess, norm_lang)]
    disclaimer = _DISCLAIMERS[norm_lang]

    return {
        "session": norm_sess,
        "language": norm_lang,
        "date_dots": date_dots,
        "top_title": texts["top_title"],
        "bottom_title": texts["bottom_title"],
        "subtitle": texts["subtitle"],
        "disclaimer": disclaimer,
        "bg_image_rel": texts["bg_image_rel"],
    }


def render_coversheet_html(
    session: str,
    language: str,
    date: str,
    asset_base_url: str = "../../../../core_tools/templates/image_library",
) -> str:
    """
    Render standard A4 coversheet HTML markup according to the master template.
    Uses locked visual artwork as background with dynamic text overlay.
    """
    cfg = get_coversheet_config(session, language, date)
    bg_url = f"{asset_base_url}/{cfg['bg_image_rel']}"

    return (
        f'<!-- COVER -->\n'
        f'<div class="page-full" style="background-image:url(\'{bg_url}\')">\n'
        f'  <div class="cover-over">\n'
        f'    <div class="cover-top cover-company">{cfg["top_title"]}</div>\n'
        f'    <div class="cover-date">{cfg["date_dots"]}</div>\n'
        f'    <div class="cover-bottom-wrap cover-title">\n'
        f'      <div class="cover-bottom cover-session">{cfg["bottom_title"]}</div>\n'
        f'      <div class="cover-sub">{cfg["subtitle"]}</div>\n'
        f'    </div>\n'
        f'    <div class="cover-note">{cfg["disclaimer"]}</div>\n'
        f'  </div>\n'
        f'</div>'
    )


COVER_CSS = """
/* Master Coversheet System */
.cover-over {
  position: absolute;
  inset: 0;
  padding: 62px 38px 34px;
  background: transparent;
}
.cover-top, .cover-company {
  font-family: 'Segoe UI Black', 'Segoe UI', Arial, sans-serif;
  font-size: 48px;
  font-weight: 900;
  line-height: 1.15;
  color: #000;
  text-transform: uppercase;
  text-align: left;
  letter-spacing: -0.5px;
  white-space: nowrap;
}
.cover-date {
  font-family: Arial, Helvetica, sans-serif;
  font-size: 21px;
  font-weight: bold;
  margin-top: 18px;
  color: #000;
  text-align: left;
}
.cover-bottom-wrap, .cover-title {
  position: absolute;
  right: 38px;
  bottom: 185px;
  text-align: right;
}
.cover-bottom, .cover-session {
  font-family: 'Segoe UI Black', 'Segoe UI', Arial, sans-serif;
  font-size: 44px;
  font-weight: 900;
  line-height: 1.1;
  color: #000;
  text-transform: uppercase;
  letter-spacing: -0.5px;
  white-space: nowrap;
}
.cover-sub {
  font-family: Arial, Helvetica, sans-serif;
  font-size: 20px;
  font-weight: normal;
  margin-top: 12px;
  color: #000;
  text-align: right;
}
.cover-note {
  position: absolute;
  left: 68px;
  right: 70px;
  bottom: 35px;
  font-family: Arial, Helvetica, sans-serif;
  font-size: 12.5px;
  line-height: 1.35;
  color: #7a7a7a;
  text-align: justify;
}
"""


def render_standalone_page(
    session: str,
    language: str,
    date: str,
    asset_base_url: str = "../../../../core_tools/templates/image_library",
) -> str:
    """Render a standalone A4 HTML document displaying the master coversheet."""
    cfg = get_coversheet_config(session, language, date)
    cover_html = render_coversheet_html(session, language, date, asset_base_url=asset_base_url)

    return f"""<!DOCTYPE html>
<html lang="{cfg['language']}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{cfg['top_title']} — {cfg['date_dots']}</title>
  <style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--pw:210mm;--ph:297mm}}
html{{font-size:20px}}
body{{font-family:Arial,Helvetica,sans-serif;background:#d8d8d8;color:#000;line-height:1.28}}
.page-full{{
  width:var(--pw);height:var(--ph);
  margin:0 auto 18px;background:#fff;position:relative;overflow:hidden;
  background-size:cover;background-position:center;
}}
{COVER_CSS}
@media print{{
  @page{{size:A4;margin:0}}
  html,body{{background:#fff}}
  .page-full{{margin:0;page-break-after:always;break-after:page}}
}}
@media screen{{body{{padding:20px 0}}}}
  </style>
</head>
<body>
{cover_html}
</body>
</html>"""


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Coversheet generator & tester")
    parser.add_argument("--session", default="morning", choices=["morning", "mor", "afternoon", "after"])
    parser.add_argument("--lang", default="vi", choices=["vi", "vn", "en"])
    parser.add_argument("--date", default="08.09.2026")
    parser.add_argument("--render-all", action="store_true", help="Generate all 4 reference variants")
    parser.add_argument("--out-dir", default=None, help="Output directory for test renders")
    parser.add_argument("--screenshots", action="store_true", help="Render PNG screenshots of the generated coversheets")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    out_dir = Path(args.out_dir) if args.out_dir else project_root / "reports" / "coversheet_showcase"
    out_dir.mkdir(parents=True, exist_ok=True)

    relative_asset_url = str(
        (project_root / "core_tools" / "templates" / "image_library").resolve()
    ).replace("\\", "/")

    generated_files = []
    if args.render_all:
        variants = [
            ("morning", "vi", "Morning Vietnamese"),
            ("morning", "en", "Morning English"),
            ("afternoon", "vi", "Afternoon Vietnamese"),
            ("afternoon", "en", "Afternoon English"),
        ]
        print(f"Rendering all 4 coversheet variants to: {out_dir}")
        for sess, lng, label in variants:
            html_content = render_standalone_page(
                sess, lng, args.date, asset_base_url=f"file:///{relative_asset_url}"
            )
            slug = f"coversheet_{sess}_{lng}"
            html_file = out_dir / f"{slug}.html"
            html_file.write_text(html_content, encoding="utf-8")
            generated_files.append((html_file, label))
            print(f"  ✓ [{label}] -> {html_file.name}")
    else:
        html_content = render_standalone_page(
            args.session, args.lang, args.date, asset_base_url=f"file:///{relative_asset_url}"
        )
        slug = f"coversheet_{normalize_session(args.session)}_{normalize_language(args.lang)}"
        html_file = out_dir / f"{slug}.html"
        html_file.write_text(html_content, encoding="utf-8")
        generated_files.append((html_file, f"{args.session} {args.lang}"))
        print(f"Saved: {html_file}")

    if args.screenshots:
        print("Rendering PNG screenshots via Playwright...")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="msedge", headless=True)
            except Exception:
                browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 794, "height": 1123})
            for h_file, label in generated_files:
                file_url = f"file:///{h_file.resolve().as_posix()}"
                page.goto(file_url, wait_until="networkidle")
                png_path = out_dir / f"{h_file.stem}.png"
                page.screenshot(path=str(png_path), full_page=True)
                print(f"  ✓ Screenshot [{label}] -> {png_path.name}")
            browser.close()

