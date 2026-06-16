# Publish News Report

Use this skill after `/dedup-news` HITL editing is complete, OR when the user runs `/publish-news` directly.

## Purpose

Run the full validation + report generation pipeline to produce HTML, PDF, and DOCX outputs from the finalized JSON data files.

---

## Step 1 — Identify Base

Confirm `{base}` (e.g. `mor_20260616`) — should be carried over from the `/dedup-news` session. If not known, use the most recently modified `reports/` subdirectory containing `data/`.

---

## Step 2 — Validate

```
phases\01_scrape\venv\Scripts\python.exe core_tools\validation\validate_summary_data.py {base}
```

If validation fails, show the errors and ask the user whether to fix them or proceed anyway. Do not continue to report generation if there are schema errors.

---

## Step 3 — Generate Reports

Run in sequence:

```
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_html_report.py {base}
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_pdf_report.py {base}
phases\01_scrape\venv\Scripts\python.exe phases\04_publish\generate_docx_report.py {base}
```

---

## Step 4 — Confirm Output

Report the generated file paths:

```
✓ HTML: reports/{base}/exports/html/{base}.html
✓ PDF:  reports/{base}/exports/pdf/{base}.pdf
✓ DOCX: reports/{base}/exports/docx/{base}.docx
```

---

## Step 5 — Upload to Heyzine (Flipbook)

Upload both the EN and VN PDFs to Heyzine to generate shareable flipbook links. Run sequentially (EN first, then VN):

```
node phases\02_curate\run-upload.js "reports\{base}\exports\pdf\{base}_report_en.pdf"
node phases\02_curate\run-upload.js "reports\{base}\exports\pdf\{base}_report_vn.pdf"
```

Each run:
- Launches Chrome using the saved user profile (auto-authenticated with Heyzine)
- Uploads the PDF, sets the flipbook title and page effect
- Extracts the share link and saves it to `reports/{base}/exports/heyzine_links.json`

After both runs, read `heyzine_links.json` and report the links:

```
✓ Flipbook EN: https://heyzine.com/flip-book/...
✓ Flipbook VN: https://heyzine.com/flip-book/...
```

Pipeline complete.
