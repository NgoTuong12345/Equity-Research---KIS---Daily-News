#!/usr/bin/env python3
import sys
import os
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "core_tools" / "paths"))
from report_paths import export_file, find_html_file, find_latest_base

def convert_html_to_pdf(html_path: Path, pdf_path: Path):
    print(f"Loading {html_path.name} in Playwright...")
    with sync_playwright() as p:
        # Launch headless browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Open local HTML file using absolute file URL
        file_url = f"file:///{html_path.resolve().as_posix()}"
        page.goto(file_url, wait_until="networkidle")
        page.emulate_media(media="print")
        page.add_style_tag(
            content="""
@page{size:A4;margin:0}
:root{--pw:210mm;--ph:297mm}
.page-full,.page-content{width:210mm;height:297mm;margin:0}
"""
        )
        
        # Print to a true A4 page. The HTML print CSS owns the page box and
        # margins, so prefer_css_page_size keeps Chromium from adding padding.
        page.pdf(
            path=str(pdf_path),
            print_background=True,
            format="A4",
            prefer_css_page_size=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        
        browser.close()
    print(f"  [PDF] saved -> {pdf_path.name}")

def main():
    parser = argparse.ArgumentParser(description="Convert HTML report to PDF using Playwright")
    parser.add_argument("base", nargs="?", default=None, help="Report base name, e.g. after_04_06_2026")
    args = parser.parse_args()
    
    base = args.base
    if not base:
        base = find_latest_base()
        
    vn_html = find_html_file(base, "vn")
    en_html = find_html_file(base, "en")
    
    vn_pdf = export_file(base, "pdf", f"{base}_report_vn.pdf")
    en_pdf = export_file(base, "pdf", f"{base}_report_en.pdf")
    
    if not vn_html.exists():
        print(f"Error: HTML report file not found: {vn_html}")
        sys.exit(1)
        
    print(f"Generating PDFs for: {base}")
    convert_html_to_pdf(vn_html, vn_pdf)
    if en_html.exists():
        convert_html_to_pdf(en_html, en_pdf)
        
    print("\nPDF generation completed successfully!")

if __name__ == "__main__":
    main()
