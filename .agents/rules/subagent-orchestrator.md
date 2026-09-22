# Subagent Delegation Policy for Opus 4.6 Thinking Orchestrator

Whenever **Opus 4.6 Thinking** is selected as the main orchestrator:

1. **Role of Opus 4.6 Thinking**:
   - Central orchestrator, high-level planner, reasoner, and report synthesizer.
   - Remains the primary orchestrator throughout the session.

2. **Subagent Delegation to Gemini 3.8 Flash**:
   - When delegating tasks (such as file searching, codebase exploration, reading files, web scraping, or background sub-tasks) using the `invoke_subagent` tool, always configure subagents to use **Gemini 3.8 Flash** (`Model: "flash"`).
   - Do NOT leave `Model: "inherit"` when running under Opus 4.6 Thinking unless explicitly requested otherwise by the user.

3. **Runtime Hook Enforcement**:
   - The lifecycle hook defined in `.agents/hooks.json` automatically intercepts `invoke_subagent` calls.
   - If Opus 4.6 Thinking is detected as the active orchestrator, the hook automatically rewrites any subagent model from `inherit` (or missing) to `"flash"` (`Gemini 3.8 Flash`) to ensure fast, cost-effective parallel exploration while Opus 4.6 Thinking orchestrates.
