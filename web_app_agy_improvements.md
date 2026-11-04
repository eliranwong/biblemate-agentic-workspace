Ran check agy CLI flags and help output
Ran list available models in agy CLI
Analyzed cli.md:L1-41
Ran check stream-json event fields in agy binary
Ran check stream-json struct tags in agy binary
Ran inspect stream-json step_update fields in agy binary
Ran check thinking/delta/tool json tags in agy binary
Ran inspect StepUpdate struct in agy binary

Because [web_app_agy.py](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py) was already updated more recently than `web_app_gemini_api_key.py`, it **already includes** several of the fixes we just made (updated `MODELS_MAP`, `.agents/skills` scanning in `get_slash_commands`, `run_direct_retriever` fast-path, `--conversation` resumption, and process-group stop handling).

However, inspecting [web_app_agy.py](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py) against the current `agy` CLI reveals **7 concrete improvements and bug fixes** that are applicable to it:

---

### 1. Missing `"Path"` Key in `summarize_tool_input()` Dumps Entire File Contents ([L177-L196](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L177-L196))
- **Issue**: [`summarize_tool_input`](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L183-L189) checks `"TargetFile"`, `"AbsolutePath"`, `"file_path"`, and `"path"` (lowercase), but current `agy` tools (`read_file`, `write_file`, `edit_file`) pass **`"Path"`** (capital `P`). Because `"Path"` isn't in the list, `summarize_tool_input` falls back to `json.dumps(raw_input)`, dumping raw JSON (including the entire markdown `Content` of a study being written) into the tool display and toast notification.
- **Fix**: Add `"Path"` (and subagent keys `"Role"`, `"TypeName"`) to the priority keys in `summarize_tool_input()` (this also benefits `web_app_gemini_api_key.py`).

### 2. Missing Paragraph Break Between Multi-Step Agent Responses ([L398-L403](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L398-L403))
- **Issue**: In [`apply_agy_event`](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L398-L403), every `agent_response` `text_delta` is concatenated directly via `state["text"] += delta`. When the agent outputs an introductory sentence before calling a tool (e.g., `"I will retrieve the passage now."`) and then outputs a Markdown heading after the tool completes (`"# Romans 8 Study"`), the two steps are concatenated with no newline (`"I will retrieve the passage now.# Romans 8 Study"`), breaking Markdown rendering.
- **Fix**: Track when a non-response step (such as `step_type == "tool"`) occurs between `agent_response` chunks and insert `\n\n` before appending the new step's `text_delta`.

### 3. System Instructions Duplicated on Every Resumed Turn ([L952-L970](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L952-L970))
- **Issue**: In [`run_agy_turn`](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L952-L955), the full `[System Instructions]\n{system_rules}` block (persona instructions + mandatory file rules) is prepended to `user_query` on **every turn**, even when resuming an existing conversation with `--conversation <id>`. Over a multi-turn study, this repeatedly injects the same system prompt into the user message history.
- **Fix**: Track the last `(selected_persona, active_skill)` sent for the current `agy_conversation_id` and only prepend `[System Instructions]` on the first turn of a session or when the persona/skill changes.

### 4. Thinking Toast Notification & Dead State Key in `apply_agy_event` ([L405-L416](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L405-L416), [L958-L959](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L958-L959))
- **Issue**:
  - `state["think_streamed"]` is initialized at [L959](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L959) but never used.
  - `state["notified_think"]` ([L410-L411](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L410-L411)) is set to `True` on the first thinking delta and never reset after a tool call finishes, so multi-step agent turns never show updated thinking toast notifications for subsequent reasoning phases, and consecutive thinking blocks run together without a newline separator.
- **Fix**: Reset `notified_think` (and add a `\n\n` separator to `state["thinking"]`) when transitioning from a tool step back to an `agent_response` thinking step.

### 5. Dynamic Model Discovery from `agy models` ([L90-L106](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L90-L106))
- **Issue**: `MODELS_MAP` is hardcoded and requires manual commits whenever Antigravity CLI adds or updates models (like commit `06a4f48`).
- **Fix**: Add a helper that runs `agy models` at startup (with a short timeout) to dynamically populate `MODELS_MAP` with the exact models available to the signed-in account, while keeping the current `MODELS_MAP` as an instant fallback.

### 6. Optional `--effort` Control or Effort-Aware Model Selection
- **Issue**: `agy --help` supports `--effort (low|medium|high|xhigh|max)` alongside `--model`.
- **Fix**: Either keep the current combined model+effort dropdown or optionally expose an Effort selector in the right-hand settings drawer.

### 7. Unused `BIBLE_REF_PATTERN` ([L109-L112](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L109-L112))
- **Issue**: `BIBLE_REF_PATTERN` is defined at [L109-L112](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L109-L112) (and in `web_app_gemini_api_key.py`) but never used.
- **Fix**: Either remove the dead regex or use it (when `selected_skill == 'Auto'` and the user enters a bare reference like `John 3:16`) to fast-path `run_direct_retriever('bible', query)`.

---

Would you like me to apply these improvements to [web_app_agy.py](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py) (and sync the `"Path"` key fix in [web_app_gemini_api_key.py](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_gemini_api_key.py))?