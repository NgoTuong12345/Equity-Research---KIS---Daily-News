"""
Output Tracing Script for KIS Daily News Pipeline.
Parses conversation transcripts to generate pipeline effectiveness reports.

Usage:
    python trace_session.py --conversation-id <ID> --base <report_base>
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

VN_TZ = timezone(timedelta(hours=7))


APP_DATA_DIR = Path(r"C:\Users\trainee.rs11\.gemini\antigravity-cli\brain")
OUTPUT_DIR = Path(r"C:\Users\trainee.rs11\Documents\KIS-DAILY-NEWS\prompt_tracing")
REPORTS_DIR = Path(r"C:\Users\trainee.rs11\Documents\KIS-DAILY-NEWS\reports")

# Phase detection: (command substring, phase name)
PHASE_PATTERNS = [
    ("generate-report.js", "Curation"),
    ("read-macro-sheet.js", "Macro Data"),
    ("hsx_insider_scraper", "HSX Trading"),
    ("hsx_prepare_pdfs", "HSX Trading"),
    ("format_hsx_trading_news", "HSX Trading"),
    ("fetch_full_articles.py", "Fetch Articles"),
    ("prepare_chunks.py", "Chunk Preparation"),
    ("invoke_subagent", "Summarization"),
    ("combine_chunks.py", "Combine Chunks"),
    ("harness.py", "Validation"),
    ("validate_summary_data.py", "Validation"),
    ("dedup_engine.py", "Deduplication"),
    ("generate_html_report.py", "Publishing"),
    ("generate_pdf_report.py", "Publishing"),
    ("generate_docx_report.py", "Publishing"),
    ("run-upload.js", "Publishing"),
]


def parse_ts(ts_str):
    """Parse ISO 8601 timestamp string to datetime and convert to Vietnam timezone (GMT+7)."""
    if not ts_str:
        return None
    try:
        ts = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(VN_TZ)
    except Exception:
        return None


def fmt_duration(td):
    """Format a timedelta into human-readable string."""
    total = int(td.total_seconds())
    if total < 0:
        return "0s"
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def fmt_time(dt):
    """Format datetime to HH:MM:SS display."""
    if not dt:
        return "—"
    return dt.strftime("%H:%M:%S")


def clean_arg(value):
    """Clean a tool call argument value (strip wrapping quotes)."""
    if isinstance(value, str):
        s = value.strip()
        if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
            try:
                return json.loads(s)
            except Exception:
                return s[1:-1]
        return s
    return value


def load_transcript(conv_id):
    """Load all steps from a transcript.jsonl file."""
    path = APP_DATA_DIR / conv_id / ".system_generated" / "logs" / "transcript.jsonl"
    if not path.exists():
        return []
    steps = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                steps.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return steps


def extract_tool_calls(steps):
    """Extract all tool calls with metadata from PLANNER_RESPONSE steps."""
    calls = []
    for step in steps:
        if not step.get("tool_calls"):
            continue
        for tc in step["tool_calls"]:
            calls.append({
                "step": step.get("step_index"),
                "name": tc.get("name", "unknown"),
                "args": tc.get("args", {}),
                "ts": step.get("created_at"),
            })
    return calls


def extract_commands(tool_calls):
    """Extract run_command calls and their command lines."""
    cmds = []
    for tc in tool_calls:
        if tc["name"] == "run_command":
            cmd_line = clean_arg(tc["args"].get("CommandLine", ""))
            cmds.append({
                "step": tc["step"],
                "command": cmd_line,
                "ts": tc["ts"],
            })
    return cmds


def detect_phase(text):
    """Match a command string or tool name to a pipeline phase."""
    for pattern, phase in PHASE_PATTERNS:
        if pattern in text:
            return phase
    return None


def _read_full_transcript_step(step_index, conv_id):
    """Read a specific step from transcript_full.jsonl for untruncated content."""
    if step_index is None or not conv_id:
        return None
    full_path = APP_DATA_DIR / conv_id / ".system_generated" / "logs" / "transcript_full.jsonl"
    if not full_path.exists():
        return None
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get("step_index") == step_index:
                        for tc in obj.get("tool_calls", []):
                            if tc.get("name") == "invoke_subagent":
                                raw = tc.get("args", {}).get("Subagents", "")
                                # Return as string for consistent regex parsing
                                if isinstance(raw, (list, dict)):
                                    return json.dumps(raw)
                                return clean_arg(raw)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return None



def find_subagent_ids(steps, conv_id=None):
    """Find subagent conversation IDs, roles, and types from transcript steps."""
    subagents = []

    # First pass: collect roles/types from invoke_subagent tool_calls
    invoke_meta = []  # list of (step_index, role, type)
    for step in steps:
        if not step.get("tool_calls"):
            continue
        for tc in step["tool_calls"]:
            if tc.get("name") != "invoke_subagent":
                continue
            raw = tc.get("args", {}).get("Subagents", "")
            raw = clean_arg(raw)
            # If truncated, try reading the full transcript line for this step
            truncated = step.get("truncated_fields") or step.get("is_truncated")
            if truncated:
                full_raw = _read_full_transcript_step(step.get("step_index"), conv_id)
                if full_raw:
                    raw = full_raw
            # Parse roles and types from the Subagents JSON array
            roles = re.findall(r'"Role"\s*:\s*"([^"]+)"', str(raw))
            types = re.findall(r'"TypeName"\s*:\s*"([^"]+)"', str(raw))
            for i in range(max(len(roles), len(types))):
                invoke_meta.append({
                    "role": roles[i] if i < len(roles) else "unknown",
                    "type": types[i] if i < len(types) else "unknown",
                    "ts": step.get("created_at"),
                })

    # Second pass: collect conversation IDs from response steps
    conv_ids = []
    for step in steps:
        content = step.get("content", "")
        if not content or "conversationId" not in content:
            continue
        ids = re.findall(r'"conversationId"\s*:\s*"([^"]+)"', content)
        for cid in ids:
            conv_ids.append(cid)

    # Deduplicate conversation IDs
    seen = set()
    unique_ids = []
    for cid in conv_ids:
        if cid not in seen:
            seen.add(cid)
            unique_ids.append(cid)

    # Merge: pair metadata with conversation IDs by order
    for i, cid in enumerate(unique_ids):
        meta = invoke_meta[i] if i < len(invoke_meta) else {}
        subagents.append({
            "conversation_id": cid,
            "role": meta.get("role", "unknown"),
            "type": meta.get("type", "unknown"),
            "created_at": meta.get("ts"),
        })

    return subagents


def count_user_prompts(steps):
    """Count and categorise user input steps."""
    prompts = []
    for step in steps:
        if step.get("type") != "USER_INPUT":
            continue
        content = step.get("content", "")
        prompts.append({
            "step": step.get("step_index"),
            "ts": step.get("created_at"),
            "content_preview": content[:120].replace("\n", " "),
        })
    return prompts


def categorise_prompt(content):
    """Categorise a user prompt into a bucket."""
    c = content.lower()
    if "/summarize-news" in c or "/curate-news" in c:
        return "Initial trigger"
    if "/dedup-news" in c:
        return "Dedup trigger"
    if "/publish-news" in c:
        return "Publish trigger"
    if "/output-tracing" in c:
        return "Tracing trigger"
    if "keep" in c and ("item" in c or "this" in c):
        return "Dedup decision"
    if "drop" in c and ("item" in c or "this" in c):
        return "Dedup decision"
    if any(w in c for w in ["drop-all", "keep-all", "review"]):
        return "Dedup decision"
    if any(w in c for w in ["drop ", "edit ", "merge ", "add ", "paste", "done"]):
        return "HITL editing"
    if "publish" in c or "re-publish" in c or "republish" in c:
        return "Re-publish request"
    if "show" in c or "list" in c or "open" in c or "help me" in c:
        return "Review / inspection"
    return "Other"


def find_errors(steps):
    """Find steps with errors or failed commands."""
    errors = []
    for step in steps:
        if step.get("status") == "ERROR":
            errors.append({
                "step": step.get("step_index"),
                "type": step.get("type", "unknown"),
                "ts": step.get("created_at"),
                "preview": (step.get("content", "") or "")[:150].replace("\n", " "),
            })
        content = step.get("content", "")
        if content and "failed with exit code" in content.lower():
            errors.append({
                "step": step.get("step_index"),
                "type": "Command failure",
                "ts": step.get("created_at"),
                "preview": content[:150].replace("\n", " "),
            })
        if content and ("UnicodeEncodeError" in content or "charmap" in content):
            errors.append({
                "step": step.get("step_index"),
                "type": "Encoding error",
                "ts": step.get("created_at"),
                "preview": "charmap / UnicodeEncodeError",
            })
    return errors


def load_output_inventory(base):
    """Load final item counts and file info from reports directory."""
    data_dir = REPORTS_DIR / base / "data"
    inventory = {"items_by_category": {}, "files": [], "heyzine": {}}

    # Count items per category JSON
    category_files = [
        (f"{base}_macro.json", "macro"),
        (f"{base}_trading.json", "trading"),
        (f"{base}_corporate.json", "corporate"),
        (f"{base}_economy_political_others.json", "economy_political_others"),
    ]
    total = 0
    for fname, cat in category_files:
        fpath = data_dir / fname
        if not fpath.exists():
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            count = data.get("item_count", 0)
            inventory["items_by_category"][cat] = count
            total += count
        except Exception:
            pass
    inventory["total_items"] = total

    # List export files with sizes
    exports_dir = REPORTS_DIR / base / "exports"
    for sub in ["html", "pdf", "docx"]:
        sub_dir = exports_dir / sub
        if not sub_dir.exists():
            continue
        for fp in sorted(sub_dir.iterdir()):
            if fp.is_file():
                size_kb = fp.stat().st_size / 1024
                inventory["files"].append({
                    "name": fp.name,
                    "type": sub.upper(),
                    "size": f"{size_kb:.0f} KB",
                })

    # Heyzine links
    links_path = exports_dir / "heyzine_links.json"
    if links_path.exists():
        try:
            with open(links_path, "r", encoding="utf-8") as f:
                inventory["heyzine"] = json.load(f)
        except Exception:
            pass

    return inventory


def compute_phases(tool_calls, commands, steps):
    """Compute phase start/end times from commands and tool calls."""
    phase_events = defaultdict(list)

    # From run_command calls
    for cmd in commands:
        phase = detect_phase(cmd["command"])
        if phase:
            ts = parse_ts(cmd["ts"])
            if ts:
                phase_events[phase].append(ts)

    # From invoke_subagent calls (Summarization phase)
    for tc in tool_calls:
        if tc["name"] == "invoke_subagent":
            ts = parse_ts(tc["ts"])
            if ts:
                phase_events["Summarization"].append(ts)

    # For summarization end: use combine_chunks start as proxy
    # (combine runs after all subagents finish)

    # Also scan step content for task completion messages (subagent results)
    for step in steps:
        content = step.get("content", "")
        if not content:
            continue
        ts = parse_ts(step.get("created_at"))
        if not ts:
            continue
        # Subagent completion messages indicate summarization phase still active
        if "chunk_summarizer" in content.lower() or "chunk" in content.lower():
            if "finished" in content.lower() or "completed" in content.lower():
                phase_events["Summarization"].append(ts)

    phases = []
    for phase_name in [
        "Curation", "Macro Data", "HSX Trading", "Fetch Articles",
        "Chunk Preparation", "Summarization", "Combine Chunks",
        "Validation", "Deduplication", "Publishing"
    ]:
        events = phase_events.get(phase_name, [])
        if not events:
            continue
        start = min(events)
        end = max(events)
        # Ensure at least 1 second duration for single-event phases
        if start == end:
            from datetime import timedelta
            end = start + timedelta(seconds=1)
        phases.append({
            "name": phase_name,
            "start": start,
            "end": end,
            "duration": end - start,
        })

    # Sort by start time
    phases.sort(key=lambda p: p["start"])
    return phases


def generate_report(conv_id, base, steps, tool_calls, commands,
                    subagents, user_prompts, errors, phases, inventory):
    """Generate the markdown trace report."""
    now = datetime.now(VN_TZ)
    lines = []

    # --- Header ---
    lines.append(f"# Pipeline Trace Report — {base}\n")
    lines.append(f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Conversation ID: `{conv_id}`\n")

    # --- 1. Session Overview ---
    lines.append("## 1. Session Overview\n")

    all_ts = [parse_ts(s.get("created_at")) for s in steps]
    all_ts = [t for t in all_ts if t]
    start_time = min(all_ts) if all_ts else None
    end_time = max(all_ts) if all_ts else None
    total_duration = (end_time - start_time) if start_time and end_time else None

    session_type = "Morning" if base.startswith("mor") else "Afternoon" if base.startswith("after") else "Unknown"

    lines.append("| Field | Value |")
    lines.append("|---|---|")
    lines.append(f"| Report Base | `{base}` |")
    lines.append(f"| Session Type | {session_type} |")
    lines.append(f"| Start Time | {fmt_time(start_time)} |")
    lines.append(f"| End Time | {fmt_time(end_time)} |")
    lines.append(f"| Total Duration | {fmt_duration(total_duration) if total_duration else '—'} |")
    lines.append(f"| Transcript Steps | {len(steps)} |")
    lines.append(f"| Total Tool Calls | {len(tool_calls)} |")
    lines.append(f"| Subagents Spawned | {len(subagents)} |")
    lines.append("")

    # --- 2. Pipeline Phase Breakdown ---
    lines.append("## 2. Pipeline Phase Breakdown\n")

    if phases:
        lines.append("| Phase | Start | End | Duration | % of Total |")
        lines.append("|---|---|---|---|---|")
        for p in phases:
            pct = (p["duration"].total_seconds() / total_duration.total_seconds() * 100) if total_duration and total_duration.total_seconds() > 0 else 0
            lines.append(
                f"| {p['name']} | {fmt_time(p['start'])} | {fmt_time(p['end'])} "
                f"| {fmt_duration(p['duration'])} | {pct:.1f}% |"
            )
        lines.append("")
    else:
        lines.append("_No phase data detected._\n")

    # --- 3. Accuracy & Quality Metrics ---
    lines.append("## 3. Accuracy & Quality Metrics\n")

    # Count harness calls and failures
    harness_calls = [c for c in commands if "harness.py" in c["command"] or "validate_summary_data" in c["command"]]
    harness_failures = [e for e in errors if "harness" in e.get("preview", "").lower() or "validation" in e.get("type", "").lower()]

    # Count dedup flags from steps content
    dedup_flagged = 0
    dedup_dropped = 0
    for step in steps:
        content = step.get("content", "")
        m = re.search(r"(\d+)\s+flagged", content)
        if m:
            dedup_flagged = max(dedup_flagged, int(m.group(1)))
        # Count "Dropping flat index" lines
        drops = re.findall(r"Dropping flat index", content)
        dedup_dropped += len(drops)

    # Count re-publish cycles (generate_html after first publish)
    html_gen_count = sum(1 for c in commands if "generate_html_report" in c["command"])
    re_publish_count = max(0, html_gen_count - 1)

    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Final published items | {inventory.get('total_items', '—')} |")
    lines.append(f"| Harness/validation runs | {len(harness_calls)} |")
    lines.append(f"| Validation failures | {len(harness_failures)} |")
    lines.append(f"| Dedup items flagged | {dedup_flagged} |")
    lines.append(f"| Items dropped (total) | {dedup_dropped} |")
    lines.append(f"| Re-publish cycles | {re_publish_count} |")
    lines.append("")

    # --- 4. User Intervention Effort ---
    lines.append("## 4. User Intervention Effort\n")

    prompt_categories = Counter()
    for p in user_prompts:
        cat = categorise_prompt(p["content_preview"])
        prompt_categories[cat] += 1

    lines.append(f"**Total user prompts: {len(user_prompts)}**")
    lines.append(f"  (Follow-up prompts after initial trigger: {max(0, len(user_prompts) - 1)})\n")

    if prompt_categories:
        lines.append("| Category | Count |")
        lines.append("|---|---|")
        for cat, count in prompt_categories.most_common():
            lines.append(f"| {cat} | {count} |")
        lines.append("")

    # --- 5. Tool & Function Call Census ---
    lines.append("## 5. Tool & Function Call Census\n")

    tool_counter = Counter(tc["name"] for tc in tool_calls)
    lines.append("### Tool Calls by Type\n")
    lines.append("| Tool | Calls |")
    lines.append("|---|---|")
    for name, count in tool_counter.most_common():
        lines.append(f"| `{name}` | {count} |")
    lines.append("")

    # Subagents table
    if subagents:
        lines.append("### Subagents Spawned\n")
        lines.append("| Role | Type | Conversation ID |")
        lines.append("|---|---|---|")
        for sa in subagents:
            short_id = sa["conversation_id"][:12] + "..."
            lines.append(f"| {sa['role']} | `{sa['type']}` | `{short_id}` |")
        lines.append("")

    # Commands executed
    if commands:
        lines.append("### Commands Executed\n")
        lines.append("| # | Command (truncated) | Step |")
        lines.append("|---|---|---|")
        for i, cmd in enumerate(commands, 1):
            cmd_short = cmd["command"][:80] + ("..." if len(cmd["command"]) > 80 else "")
            lines.append(f"| {i} | `{cmd_short}` | {cmd['step']} |")
        lines.append("")

    # --- 6. Error & Retry Log ---
    lines.append("## 6. Error & Retry Log\n")

    if errors:
        lines.append("| Step | Type | Preview |")
        lines.append("|---|---|---|")
        for e in errors:
            preview = e["preview"][:80] + ("..." if len(e["preview"]) > 80 else "")
            lines.append(f"| {e['step']} | {e['type']} | {preview} |")
        lines.append("")
    else:
        lines.append("_No errors recorded._\n")

    # --- 7. Output Inventory ---
    lines.append("## 7. Output Inventory\n")

    lines.append("### Item Counts by Category\n")
    lines.append("| Category | Items |")
    lines.append("|---|---|")
    for cat, count in inventory.get("items_by_category", {}).items():
        lines.append(f"| {cat} | {count} |")
    lines.append(f"| **Total** | **{inventory.get('total_items', 0)}** |")
    lines.append("")

    if inventory.get("files"):
        lines.append("### Generated Files\n")
        lines.append("| File | Type | Size |")
        lines.append("|---|---|---|")
        for f in inventory["files"]:
            lines.append(f"| {f['name']} | {f['type']} | {f['size']} |")
        lines.append("")

    heyzine = inventory.get("heyzine", {})
    if heyzine:
        lines.append("### Heyzine Flipbook Links\n")
        if "en" in heyzine:
            lines.append(f"- **EN**: {heyzine['en'].get('url', '—')}")
        if "vn" in heyzine:
            lines.append(f"- **VN**: {heyzine['vn'].get('url', '—')}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate pipeline trace report")
    parser.add_argument("--conversation-id", required=True, help="Conversation ID of the session")
    parser.add_argument("--base", required=True, help="Report base (e.g. mor_18_06_2026)")
    args = parser.parse_args()

    conv_id = args.conversation_id
    base = args.base

    print(f"Loading transcript for conversation: {conv_id}")
    steps = load_transcript(conv_id)
    if not steps:
        print(f"ERROR: No transcript found for {conv_id}")
        sys.exit(1)
    print(f"  Loaded {len(steps)} steps")

    # Extract metrics
    tool_calls = extract_tool_calls(steps)
    commands = extract_commands(tool_calls)
    subagents = find_subagent_ids(steps, conv_id)
    user_prompts = count_user_prompts(steps)
    errors = find_errors(steps)
    phases = compute_phases(tool_calls, commands, steps)
    inventory = load_output_inventory(base)

    print(f"  Tool calls: {len(tool_calls)}")
    print(f"  Commands: {len(commands)}")
    print(f"  Subagents: {len(subagents)}")
    print(f"  User prompts: {len(user_prompts)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Phases detected: {len(phases)}")
    print(f"  Final items: {inventory.get('total_items', 0)}")

    # Generate report
    report = generate_report(
        conv_id, base, steps, tool_calls, commands,
        subagents, user_prompts, errors, phases, inventory,
    )

    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(VN_TZ).strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"{base}_trace_{timestamp}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nTrace report saved to: {out_path}")


if __name__ == "__main__":
    main()
