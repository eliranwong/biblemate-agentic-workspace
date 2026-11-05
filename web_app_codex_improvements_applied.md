Analyzed web_app_agy_improvements.md (7 suggested improvements)
Analyzed web_app_agy.py and web_app_claude.py (applied reference implementations)
Analyzed web_app_codex.py (target file, Codex CLI backend)
Edited web_app_codex.py (all seven improvements, committed in a8da1de together with tests/test_web_app_codex.py)
Ran verify syntax with `python3 -m py_compile web_app_codex.py`
Ran `python3 -m unittest discover -s tests` (25 tests, all passing)
Ran smoke-test summarize_tool_input (capitalized keys, JSON-encoded arguments, list values) with a stubbed `nicegui` import
Ran live model discovery with the installed Codex CLI (app-server `model/list`)
Ran smoke check of the actual UI with the installed NiceGUI environment

The 7 improvements recorded in [web_app_agy_improvements.md](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy_improvements.md) were applied to [web_app_codex.py](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py) in commit `a8da1de` (2026-11-04, together with the regression suite [tests/test_web_app_codex.py](file:///home/eliran/dev/biblemate-agentic-workspace/tests/test_web_app_codex.py)). This file is the detailed record of what was applied, re-verified against the current code on 2026-11-05 (25/25 tests passing, compile clean).

---

## Applied improvements

### 1. Extended Tool-Call Input Summarization (`summarize_tool_input`) ([web_app_codex.py#L253-L280](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L253-L280))

**From agy improvement #1, extended beyond the agy fix.**

- **Issue**: The priority-key list was too narrow, so tool payloads using capitalized or alternative key names fell through to `json.dumps(raw_input)`, dumping raw JSON — including entire file contents — into the tool display and toast.
- **Applied**: The priority-key tuple now covers `"command"`, `"cmd"`, `"CommandLine"`, `"target_file"`, `"TargetFile"`, `"file_path"`, `"path"`, `"Path"`, `"AbsolutePath"`, `"notebook_path"`, `"pattern"`, `"query"`, `"Query"`, `"queries"`, `"Queries"`, `"url"`, `"Url"`, `"prompt"`, `"Prompt"`, `"script_path"`, `"skill"`, `"description"`, `"Role"`, `"TypeName"`, and `"DirectoryPath"`.
- **Codex-specific extensions** beyond the agy fix:
  - The function first tries `json.loads` on string payloads, because Codex tool-call `arguments` arrive JSON-encoded in some event shapes ([web_app_codex.py#L255-L262](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L255-L262)).
  - List-of-strings values (e.g. a list of queries) are joined with `', '` instead of falling through to the raw dump ([web_app_codex.py#L275-L276](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L275-L276)).
  - Used in `apply_codex_event`'s tool branch, where the displayed detail combines the tool name and its summarized input (`tool: detail`), with MCP server prefixes and per-change `file_change` listings ([web_app_codex.py#L548-L580](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L548-L580)).
- **Verified**: `{'Path': ..., 'Content': <huge>}` summarizes to the path; a JSON-encoded `'{"Path": ...}'` string summarizes to the path; `{'queries': ['John 3:16', 'Romans 8:28']}` summarizes to `'John 3:16, Romans 8:28'`; `{'Role': ..., 'Prompt': ...}` summarizes to the prompt.

### 2. Paragraph Breaks Between Multi-Step Agent Responses — already satisfied by the item-snapshot design ([web_app_codex.py#L513-L523](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L513-L523))

**From agy improvement #2.**

- **Issue (in the agy design)**: response `text_delta`s separated by tool calls concatenated with no separator, breaking Markdown.
- **Codex outcome**: not reproduced as a bug — the Codex event model delivers `agent_message` items as full per-item snapshots, not deltas. The app stores each message in `state["messages"]` keyed by item ID (so `item.updated`/`item.completed` repeats replace rather than duplicate) and joins them with `"\n\n"` when rendering ([web_app_codex.py#L514-L523](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L514-L523)). Paragraph breaks between steps are therefore inherent.
- **Also relevant**: reasoning/progress commentary is tracked separately in `state["thoughts"]` (also keyed by item ID, also deduplicated), joined with `"\n\n"` by `_refresh_thinking` ([web_app_codex.py#L607-L609](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L607-L609)), and a message promoted to final answer is removed from the thoughts map so it is not shown twice ([web_app_codex.py#L519-L521](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L519-L521), [L612-L619](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L612-L619)).
- **Verified**: the item-transition scenario is covered by the regression suite; no code change was required beyond the existing snapshot maps.

### 3. Deduplicated Session Instructions on Resumed Turns ([web_app_codex.py#L1099-L1113](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L1099-L1113), [L1179-L1181](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L1179-L1181), [L1298-L1300](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L1298-L1300))

**From agy improvement #3, adapted with retry handling.**

- **Issue**: The agy app prepended the full `[System Instructions]` block to every turn's user message, re-injecting it into the resumed conversation each time.
- **Applied** (Codex uses `codex exec resume <id>`, so instructions must be sent as prompt text — the Claude-style CLI-flag approach is not available):
  - `self.codex_last_rules_key = (selected_persona, active_skill)` tracks the last rules combination sent.
  - `self.codex_rules_session_id` additionally scopes that memory to a specific Codex session/thread.
  - `send_rules` is True only when: there is no session yet, the session ID changed, or the persona/skill combination changed ([web_app_codex.py#L1100-L1104](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L1100-L1104)). Otherwise the prompt is just the user's request.
  - When rules are sent, the block is headed `## BibleMate Web App Instructions` and explicitly states it *replaces previous BibleMate Web App Instructions in this conversation*, so a rules change supersedes the earlier block instead of stacking.
  - The remembered key/session are updated **only after a successful CLI invocation** (`returncode == 0` and no error, [web_app_codex.py#L1178-L1181](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L1178-L1181)) — a failed or stopped turn retries the rules on the next turn rather than silently dropping them.
  - `clear_conversation()` resets both the session ID and the remembered settings ([web_app_codex.py#L1298-L1300](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L1298-L1300)).
- **Not copied**: Antigravity's `--disable-slash-commands` flag from the agy fix — the Codex CLI does not expose that flag.

### 4. Thinking Toast Reset Between Reasoning Phases ([web_app_codex.py#L546-L547](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L546-L547))

**From agy improvement #4 (partial — the dead-key half does not apply).**

- **Issue**: `state["notified_think"]` set on the first reasoning item and never reset meant later reasoning phases (after tool calls) never produced a fresh "Codex thinking: …" toast.
- **Applied**: in the tool-item branch, both `item.started` and `item.completed` events reset `state['notified_think'] = False`, so every reasoning phase after a tool step notifies again.
- **Reasoning-block separation**: already inherent — consecutive reasoning items are separate entries in the thoughts map, joined with `"\n\n"` by `_refresh_thinking` (no separator fix needed).
- **Not applicable**: agy's dead `state["think_streamed"]` key has no counterpart here; the Codex state dict ([web_app_codex.py#L1116](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L1116)) never contained it.

### 5. Dynamic Model Discovery from the CLI ([web_app_codex.py#L104-L188](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L104-L188), [L1515-L1517](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L1515-L1517))

**From agy improvement #5, using Codex's own discovery mechanism.**

- **Issue**: `FALLBACK_MODELS_MAP` was hardcoded (`gpt-5-codex`, `gpt-5`, `gpt-5-mini`) and required manual commits whenever the CLI's model catalog changed.
- **Applied**: async `discover_codex_models()` queries the signed-in CLI without starting an agent turn:
  - Starts `codex app-server --listen stdio://` as a temporary subprocess, performs the `initialize` handshake, then reads the paginated `model/list` catalog (`limit` 100, following `nextCursor`).
  - Populates `MODELS_MAP` from `displayName` → model ID; duplicate display names are disambiguated as `'<label> (<model_id>)'`.
  - Populates `MODEL_EFFORTS` (model ID → list of `reasoningEffort` values from `supportedReasoningEfforts`) for the effort dropdown (improvement 6).
  - A 5-second timeout, plus `OSError`/`RuntimeError`/`ValueError`/`KeyError`/`TypeError`/`AttributeError` guards, keep older CLIs and offline startups usable — in every failure case the previous/fallback map is preserved.
  - The temporary server process is terminated and reaped on both success and failure (`terminate` → wait → `kill` fallback).
  - Runs once at startup, before the UI is constructed, when launched as a script ([web_app_codex.py#L1517](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L1517)); a hidden-model guard skips `hidden` entries.
- **Reference docs used to verify the integration**: [App Server: initialization and model/list](https://developers.openai.com/codex/app-server/), [Configuration reference: model_reasoning_effort](https://developers.openai.com/codex/config-reference/).
- **Verified**: live discovery with the installed CLI returned nine visible models and their effort metadata; failure paths are covered by the test suite's fixture processes.

### 6. Reasoning-Effort Control ([web_app_codex.py#L483-L494](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L483-L494), [L1098](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L1098), [L1127-L1128](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L1127-L1128), [L1391-L1393](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_codex.py#L1391-L1393))

**From agy improvement #6, effort-aware rather than a fixed list.**

- **Applied**:
  - A **Reasoning Effort** dropdown in the settings drawer, whose options come from `effort_options()`: the levels the *selected* model advertises via `MODEL_EFFORTS` (from improvement 5), prefixed with `Default (session default)`.
  - Switching models calls `update_effort_options()`, which rebuilds the dropdown and resets an unsupported selection back to the default — the session-default model and fallback models with unknown effort support offer only the default.
  - `run_codex_turn` validates the selected effort against the current options before use, then passes an explicit effort as `-c 'model_reasoning_effort="<level>"'` for both new and resumed turns; the default sends no override.
- **Verified**: a smoke check with the installed NiceGUI environment constructed the actual UI, updated effort options for a discovered model, and reset them on returning to the session-default model.

### 7. Removed Unused `BIBLE_REF_PATTERN`

**From agy improvement #7 (same option the agy and claude apps took: removal).**

- **Issue**: the scripture-reference regex was defined but never used.
- **Applied**: deleted; the current file contains no `BIBLE_REF_PATTERN` (verified by grep). The `re` import is retained — it is still used by `parse_personas`.

---

## Verification summary

Re-verified against the current code on 2026-11-05:

- `python3 -m unittest discover -s tests` — **25/25 tests pass** (agent-turn tests use fixture CLI processes; no live study turn needed).
- `python3 -m py_compile web_app_codex.py` — passes.
- `summarize_tool_input` smoke test (with `nicegui` stubbed in the shell's default Python): capitalized keys, JSON-encoded argument strings, and list-of-queries values all summarize correctly; `BIBLE_REF_PATTERN` confirmed absent; `DEFAULT_EFFORT` plumbing confirmed.
- Earlier verification from the original application (commit `a8da1de`): live model discovery returned nine visible models with effort metadata; a NiceGUI UI smoke check exercised the effort dropdown; `git diff --check` passed. No live browser-driven interaction was performed.
