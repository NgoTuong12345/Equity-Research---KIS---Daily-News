---
version: alpha
name: KIS Vietnam Daily News Report
description: Print-style HTML report system matched to the original KIS PDF bulletin format.
colors:
  ink: "#080808"
  brown: "#6f3f26"
  brown-line: "#8b4a22"
  paper: "#ffffff"
  screen-background: "#d8d8d8"
  cover-paper: "#f2e4d2"
  note-muted: "#909090"
typography:
  cover-company:
    fontFamily: Arial, Helvetica, sans-serif
    fontSize: 54px
    fontWeight: 800
    lineHeight: 1.28
    letterSpacing: 0
  cover-date:
    fontFamily: Arial, Helvetica, sans-serif
    fontSize: 21px
    fontWeight: 400
    lineHeight: 1.28
    letterSpacing: 0
  cover-session:
    fontFamily: Arial, Helvetica, sans-serif
    fontSize: 49px
    fontWeight: 800
    lineHeight: 1
    letterSpacing: 0
  section-title:
    fontFamily: Arial, Helvetica, sans-serif
    fontSize: 39px
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: 0
  story-title:
    fontFamily: Arial, Helvetica, sans-serif
    fontSize: 15px
    fontWeight: 800
    lineHeight: 1.18
    letterSpacing: 0
  story-body:
    fontFamily: Arial, Helvetica, sans-serif
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.3
    letterSpacing: 0
  footer-page-number:
    fontFamily: Arial, Helvetica, sans-serif
    fontSize: 26px
    fontWeight: 400
    lineHeight: 1
    letterSpacing: 0
spacing:
  page-width: 210mm
  page-height: 297mm
  content-x: 46px
  content-top: 36px
  content-bottom-safe-area: 86px
  section-banner-height: 400px
  section-title-bottom: 54px
  story-column-gap: 70px
  story-row-gap: 62px
  max-news-per-page: 4
  max-title-chars: 100
  target-title-chars: 80-100
  max-summary-chars: none
  footer-left: 48px
  footer-right: 44px
  footer-bottom: 17px
  footer-height: 41px
rounded:
  none: 0px
components:
  report-page:
    backgroundColor: "{colors.paper}"
    width: "{spacing.page-width}"
    height: "{spacing.page-height}"
  section-banner:
    height: "{spacing.section-banner-height}"
    borderBottomColor: "{colors.brown-line}"
  section-title:
    textColor: "{colors.brown}"
    typography: "{typography.section-title}"
  story-title:
    textColor: "{colors.brown}"
    typography: "{typography.story-title}"
  story-body:
    textColor: "{colors.ink}"
    typography: "{typography.story-body}"
  footer-logo:
    width: 96px
    height: 24px
  footer-rule:
    backgroundColor: "{colors.brown-line}"
    height: 2px
---

## Overview

This repository generates KIS Vietnam daily news HTML reports that must visually follow the original exported PDF bulletin. Treat this file as the design contract for `scripts/generate_html_report.py` and any future HTML/CSS output.

The target is a print-like report page, not a web dashboard. Keep the layout quiet, editorial, and fixed-format. Do not introduce cards, decorative gradients, dark overlays, rounded panels, marketing sections, or responsive reflow for the print artifact.

## Page Model

Every report page is a fixed A4 canvas: `210mm` wide by `297mm` tall. Pages must be white, centered on a neutral gray screen background, and clipped to their page bounds.

The print rule must remain `@page{size:A4;margin:0}` so browser PDF output keeps the A4 page box and no default margins.

## Cover

The cover uses a full-page thematic background image with a light paper overlay, not a dark overlay. The KIS company name sits large at the upper-left, the date sits below it as `DD.MM.YYYY`, and the session title sits at lower-right.

Cover text is black. The cover note sits near the bottom-left in muted gray. Do not show a table of contents on the cover; the original PDF format is direct title-first editorial presentation.

## Content Pages

Each content page has a full-width image banner at the top. The banner height is exactly `400px`, followed by a `5px` brown divider. Do not place text over the banner.

The content area starts at `36px` below the banner and has `46px` horizontal padding. The bottom safe area is `86px` so story text never collides with the footer. Content must never overlap, hide behind, or sit under the footer.

Section titles use uppercase brown text. Continued pages may append `(cont.)` or the Vietnamese equivalent after the section title using smaller regular-weight text.

## Story Grid

Stories are laid out in two columns with `70px` column gap and `62px` row gap. Story title and story body are both `15px`. A content page must never contain more than four news items, and when a section has five or more items the first page should contain four and the next page should start with item five. Story titles are bold brown. Story bodies are black, regular weight, and justified.

Titles should be limited to `80-100` characters, with a hard cap of `100`. Summaries should not be hard-truncated; use pagination and overflow checks to preserve complete summarized content.

Do not increase story title or body font size above `15px` unless the benchmark and screenshot review prove that no page content collides with the footer. If a page still feels crowded, trim story text before changing footer or page geometry.

## Footer

Every content page has a footer fixed near the bottom: left `48px`, right `44px`, bottom `17px`, height `41px`. It contains a brown top rule, a small cropped KIS logo on the left (`96px x 24px`), and a brown page number on the right.

The footer logo must remain visually small. It should support brand identification only; it must not dominate the page or touch story text.

## Outro

The outro page follows the original PDF final-page composition. Use the full-bleed outro background image without a beige overlay. Place `KIS Vietnam Securities Corporation` in white uppercase near the upper third of the page, centered horizontally. Place `Thank You` below it in white with thin horizontal white rules on both sides.

Do not show the KIS logo, market-intelligence tagline, or localized thank-you text on the outro. The copyright belongs in the lower-left corner in small white text over two lines.

## Overflow Rules

No generated page may have story text below the top edge of the footer rule. If content is too long, create another content page and continue the section.

The generator and visual benchmark should be used together:

- Regenerate reports with `python scripts/generate_html_report.py after_04_06_2026`.
- Run `python scripts/benchmark_html_against_pdf.py`.
- Inspect rendered pages under `reports/{base}/testing/diffs/html_vs_pdf/`.

Passing conditions:

- Every generated PDF page is A4, approximately `595 x 842 pt`.
- Footer logo is small and does not cover content.
- Story text and section titles do not overlap the footer.
- The report keeps the original PDF visual language: white content pages, brown editorial typography, top image banner, two-column text, and numbered footer.

## Do Not Change Without Review

Do not change page dimensions, banner height, footer position, footer logo size, story font size, or safe-area padding without updating this file and rerunning the benchmark. These values are intentionally strict because the report is judged against the original PDF format.
