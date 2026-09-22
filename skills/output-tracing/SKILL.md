---
name: output-tracing
description: |
  Post-session tracing report measuring pipeline effectiveness: latency, accuracy,
  user intervention effort, and tool/function call census. Triggers on
  "/output-tracing", "output tracing", "trace session", "pipeline report".
---

# Output Tracing — Pipeline Effectiveness Report

Use this skill **only when the user explicitly triggers it** (e.g. `/output-tracing`).
It is designed to be called after the user is satisfied with the final published output.

## Purpose

Generate a structured markdown report that documents how effectively the
`/summarize-news` → `/dedup-news` → `/publish-news` pipeline ran, including:

1. **Session overview** — base, model, wall-clock duration
2. **Pipeline phase latency** — time spent in each phase (curation, macro, HSX, summarization, dedup, publish)
3. **Accuracy & quality** — harness pass rate, dedup flags, user drops, re-publish count
4. **User intervention effort** — total follow-up prompts after initial trigger, categorised
5. **Tool & function call census** — every tool invoked, subagents spawned, commands executed
6. **Error & retry log** — failed commands, encoding issues, validation failures
7. **Output inventory** — final item counts, generated files, Heyzine links

---

## Step 1 — Identify Context

Determine:
- **Conversation ID**: Use the current session's conversation ID (available from the system context / artifact directory path).
- **Report base**: Identify the most recently modified `reports/{base}/` directory, or ask the user if ambiguous.
- **App Data Dir**: `C:\Users\trainee.rs11\.gemini\antigravity-cli\brain`

---

## Step 2 — Run the Trace Script

```powershell
phases\01_scrape\venv\Scripts\python.exe skills\output-tracing\scripts\trace_session.py --conversation-id {CONVERSATION_ID} --base {BASE}
```

The script will:
1. Read the main transcript at `{APP_DATA_DIR}\{CONVERSATION_ID}\.system_generated\logs\transcript.jsonl`
2. Discover subagent conversation IDs from `invoke_subagent` tool calls
3. Read each subagent's transcript
4. Compute all metrics across the full pipeline
5. Save the report to `C:\Users\trainee.rs11\Documents\KIS-DAILY-NEWS\prompt_tracing\{BASE}_trace_{YYYYMMDD_HHMMSS}.md`

---

## Step 3 — Present Findings

After the script completes:
1. Read the generated trace report
2. Present the **key highlights** to the user:
   - Total wall-clock duration
   - Number of user follow-up prompts
   - Items dropped (dedup + user HITL)
   - Any errors encountered
   - Final item count and Heyzine links
3. Note any anomalies (e.g. unusually long phases, high retry count)

---

## Notes

- This skill does NOT modify any data files or reports. It is read-only.
- The trace script reads transcript JSONL files which are append-only logs.
- Output directory: `C:\Users\trainee.rs11\Documents\KIS-DAILY-NEWS\prompt_tracing\`
- Each run produces a new timestamped file; previous traces are never overwritten.
