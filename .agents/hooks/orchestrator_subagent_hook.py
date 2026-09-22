#!/usr/bin/env python3
"""
Lifecycle Hook for Antigravity:
Enforces Gemini 3.8 Flash ('flash') for subagents whenever Opus 4.6 Thinking
is acting as the main orchestrator.
"""

import sys
import os
import json
import re

def is_opus_orchestrator(payload: dict) -> bool:
    """
    Determines if the active orchestrator model is Opus 4.6 Thinking.
    Checks:
    1. payload['modelName']
    2. Environment variables (AGY_MODEL, MODEL_NAME, etc.)
    3. Transcript file at payload['transcriptPath'] (most recent Model Selection)
    """
    # Force flag override if set
    if os.environ.get("FORCE_SUBAGENT_FLASH", "").strip() in ("1", "true", "yes"):
        return True

    # 1. Check modelName directly from hook payload
    model_name = (payload.get("modelName") or "").strip().lower()
    if model_name and model_name != "auto":
        return "opus" in model_name

    # 2. Check environment variables
    for env_var in ("AGY_MODEL", "MODEL_NAME", "ORCHESTRATOR_MODEL", "ANTIGRAVITY_MODEL"):
        val = os.environ.get(env_var, "").strip().lower()
        if val:
            return "opus" in val

    # 3. Check transcript for recent user model selection
    transcript_path = payload.get("transcriptPath")
    if transcript_path and os.path.isfile(transcript_path):
        try:
            with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            for line in reversed(lines):
                # Check for settings change in user input or system events
                # e.g., "The user changed setting Model Selection from ... to Opus 4.6 Thinking"
                match = re.search(r"Model Selection[`\s]*from\s+.*?to\s+([^.\n<]+)", line, re.IGNORECASE)
                if match:
                    selected_model = match.group(1).lower()
                    return "opus" in selected_model
                if "model selection" in line.lower() and "opus" in line.lower():
                    return True
        except Exception:
            pass

    return False


def handle_pre_tool_use(payload: dict):
    """
    PreToolUse hook for invoke_subagent.
    If Opus 4.6 Thinking is the orchestrator, ensure all subagents use 'flash' (Gemini 3.8 Flash).
    """
    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name")
    args = tool_call.get("args", {})

    if tool_name == "invoke_subagent" and is_opus_orchestrator(payload):
        subagents = args.get("Subagents", [])
        if isinstance(subagents, list) and subagents:
            modified = False
            new_subagents = []
            for sub in subagents:
                if isinstance(sub, dict):
                    sub_copy = dict(sub)
                    # When Opus 4.6 is orchestrator, set subagent Model to 'flash' (Gemini 3.8 Flash)
                    if sub_copy.get("Model") != "flash":
                        sub_copy["Model"] = "flash"
                        modified = True
                    new_subagents.append(sub_copy)
                else:
                    new_subagents.append(sub)

            if modified:
                response = {
                    "decision": "allow",
                    "reason": "Enforced Gemini 3.8 Flash ('flash') for subagents under Opus 4.6 Thinking orchestrator.",
                    "overwrite": {
                        "Subagents": new_subagents
                    }
                }
                print(json.dumps(response))
                return

    # Default: allow unchanged
    print(json.dumps({"decision": "allow"}))


def handle_pre_invocation(payload: dict):
    """
    PreInvocation hook before model runs.
    Injects a transient reminder when Opus 4.6 Thinking is the active orchestrator.
    """
    if is_opus_orchestrator(payload):
        response = {
            "injectSteps": [
                {
                    "ephemeralMessage": (
                        "Notice: Opus 4.6 Thinking is active as the main orchestrator. "
                        "When delegating tasks (file search, exploring, research, etc.) via invoke_subagent, "
                        "subagents run on Gemini 3.8 Flash (Model: 'flash') while you remain the primary orchestrator."
                    )
                }
            ]
        }
        print(json.dumps(response))
    else:
        print(json.dumps({"injectSteps": []}))


def main():
    try:
        # Read payload from stdin
        input_data = sys.stdin.read()
        if not input_data.strip():
            # Empty input safety
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(input_data)

        # Detect hook mode from CLI args or payload shape
        is_pre_tool = "--pre-tool" in sys.argv or "toolCall" in payload
        is_pre_invocation = "--pre-invocation" in sys.argv or ("toolCall" not in payload and "invocationNum" in payload)

        if is_pre_invocation and not is_pre_tool:
            handle_pre_invocation(payload)
        else:
            handle_pre_tool_use(payload)

    except Exception as exc:
        # Never crash the agent loop on hook failure
        sys.stderr.write(f"Hook warning: {exc}\n")
        print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
