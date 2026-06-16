# Project Reorganization Plan

To make the project more intuitive and explicitly aligned with your pipeline's logic (Phases, Tools, LLM Brain), I propose the following directory structure. 

This structure separates the sequential pipeline steps (`phases/`), the reusable utilities (`core_tools/`), and the AI logic (`llm_brain/`).

## Proposed Directory Structure

```text
Playwright-Daily-News/
│
├── phases/
│   ├── 01_scrape/                 # Formerly `vietnam_news_scraper/` (scraping logic only)
│   │   ├── main.py                
│   │   ├── hsx_insider_scraper.py
│   │   └── run.bat
│   │
│   ├── 02_curate/                 # Formerly `google-sheets-uploader/`
│   │   ├── upload-to-sheets.js
│   │   └── read-macro-sheet.js
│   │
│   ├── 03_summarize/              # Formerly in `scripts/` (Data fetching & parsing)
│   │   ├── fetch_full_articles.py
│   │   ├── prepare_chunks.py
│   │   └── combine_chunks.py
│   │
│   └── 04_publish/                # Formerly in `scripts/` (Final report generation)
│       ├── generate_html_report.py
│       ├── generate_pdf_report.py
│       └── generate_docx_report.py
│
├── llm_brain/                     # All Agentic and LLM-driven intelligence
│   ├── prompts_and_rules/         # Shared LLM instructions
│   │   ├── summary_rules.py
│   │   └── news_title_rules.py
│   │
│   ├── extractors/                # Agent extraction logic
│   │   ├── hsx_agent_extractor.py
│   │   ├── apply_news_title_rules.py
│   │   └── generate_summaries_md.py
│   │
│   └── vision/                    # PDF parsing and image rendering
│       └── hsx_prepare_pdfs.py
│
├── core_tools/                    # Shared utilities and configurations
│   ├── paths/                     
│   │   ├── report_paths.py        # Python path helpers
│   │   └── report-paths.js        # Node path helpers
│   ├── templates/                 # Formerly `news_html_template/`
│   └── validation/                
│       ├── validate_summary_data.py
│       └── benchmark_html_against_pdf.py
│
├── orchestration/                 # Top-level execution
│   ├── run-morning.bat
│   └── run-afternoon.bat
│
├── reports/                       # Output folder (Remains at root)
│   └── ...
│
└── docs/                          # Documentation
    ├── README.md
    ├── GEMINI.md
    └── DESIGN.md
```

## Required Code Updates (What will break during the move)

Reorganizing the folder structure is a major change. If we proceed, I will need to update the following to prevent the pipeline from breaking:

1. **Path Helpers:** We will need to update `report_paths.py` and `report-paths.js` to point to the correct `../../reports/` directory since they will be nested deeper.
2. **Python Imports:** Scripts in `phases/` and `llm_brain/` will need their `import` statements updated to find shared utilities in `core_tools/`.
3. **Batch Scripts:** `run-morning.bat` and `run-afternoon.bat` will need to be rewritten to navigate through the new `phases/` and `llm_brain/` directories rather than the old ones.
4. **Documentation:** `GEMINI.md` and `README.md` will need to be updated to document the new paths.

---

**Do you approve of this structure?** If you'd like to adjust any folder names or groupings, let me know. If it looks good, I will begin carefully moving the files and rewriting the import paths.
