from pathlib import Path
from playwright.sync_api import sync_playwright

p = Path("reports/coversheet_showcase")
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 794, "height": 1123})
    for h in sorted(p.glob("*.html")):
        page.goto(f"file:///{h.resolve().as_posix()}", wait_until="networkidle")
        top = page.locator(".cover-top").bounding_box()
        date = page.locator(".cover-date").bounding_box()
        bot = page.locator(".cover-bottom").bounding_box()
        sub = page.locator(".cover-sub").bounding_box()
        print(f"=== {h.stem} ===")
        print(f"  Top: text='{page.locator('.cover-top').inner_text()}' bbox=({top['x']:.1f}, {top['y']:.1f}, w={top['width']:.1f}, h={top['height']:.1f})")
        print(f"  Date: text='{page.locator('.cover-date').inner_text()}' bbox=({date['x']:.1f}, {date['y']:.1f}, w={date['width']:.1f}, h={date['height']:.1f})")
        print(f"  Bottom: text='{page.locator('.cover-bottom').inner_text()}' bbox=({bot['x']:.1f}, {bot['y']:.1f}, w={bot['width']:.1f}, h={bot['height']:.1f})")
        print(f"  Sub: text='{page.locator('.cover-sub').inner_text()}' bbox=({sub['x']:.1f}, {sub['y']:.1f}, w={sub['width']:.1f}, h={sub['height']:.1f})")
    browser.close()
