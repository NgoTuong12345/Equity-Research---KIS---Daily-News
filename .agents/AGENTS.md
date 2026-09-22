# AGENTS.md

Repository guide for Antigravity (AGY) sessions in KIS-DAILY-NEWS.

**For the complete directory map, manual commands, pipeline overview, and all rules, refer to the master [AGENTS.md](file:///W:/KIS-DAILY-NEWS/AGENTS.md) at the repository root.** This file contains only `.agents/`-specific context.

---

## .agents/ Structure

```
.agents/
  AGENTS.md          ← this file (thin pointer to root AGENTS.md)
  hooks.json         ← lifecycle hooks config (Opus 4.6 Thinking + Gemini 3.8 Flash)
  hooks/             ← lifecycle hook scripts (orchestrator_subagent_hook.py)
  rules/
    pipeline-rules.md        ← core pipeline execution constraints
    subagent-orchestrator.md ← Opus 4.6 Thinking orchestrator & Gemini 3.8 Flash subagents
  skills/              ← 8 registered AGY skill definitions
    curate-news/
    dedup-news/
    delta-summarize/
    kis-writing-style/
    paste-news/
    publish-news/
    scrape-and-upload/
    summarize-news/
```

## Available Skills

The following 8 skills are registered for AGY:
- `/scrape-and-upload` - Run news scraper, HSX insider trading, and upload CSV to Google Sheets.
- `/curate-news` - Read TAKE rows from Google Sheets into markdown source file.
- `/summarize-news` - Summarize TAKE articles & process Macro/VinBank/HSX into 4 JSON categories.
- `/dedup-news` - Agentic deduplication (intra-session & cross-session) with HITL review.
- `/publish-news` - Schema validation, generate HTML/PDF/DOCX, and upload to Heyzine.
- `/paste-news` - Process ad-hoc pasted text directly into news reports.
- `/delta-summarize` - Summarize new delta articles added after initial run.
- `/kis-writing-style` - KIS Vietnamese & English writing style reference guide.

## Production HTML Generator

- Canonical script: `phases\04_publish\generate_html_report_standard.py` (incorporates standard intro & outro formatting).

---

All pipeline rules, typography rules, cover/outpage standards, HSX extraction rules, commodities title rules, and working conventions are defined in the master [AGENTS.md](file:///W:/KIS-DAILY-NEWS/AGENTS.md). Do not duplicate them here.
