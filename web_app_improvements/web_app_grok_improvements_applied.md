# Improvements applied to `web_app_grok.py`

These changes port the Antigravity web-app fixes that fit the signed-in Grok Build CLI. The source notes are [web_app_agy_improvements.md](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy_improvements.md) and [web_app_agy_improvements_applied.md](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy_improvements_applied.md). The Grok app was compared with `grok --help`, `grok models`, and the `streaming-json` event shape in the Grok Build headless-mode guide before anything was copied.

Only [web_app_grok.py](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_grok.py) was edited. The other web apps were left as they were.

## 1. Dynamic model discovery (`discover_grok_models`)

[web_app_grok.py#L89-L146](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_grok.py#L89-L146)

**Problem.** The model dropdown was a hardcoded `MODELS_MAP`. A new Grok Build model required a code change before the web app could offer it.

**Change.** At import, `discover_grok_models()` runs `grok models` with a 5-second timeout and builds the dropdown from the signed-in account.

- `subprocess` was added to the imports so the query can run at startup.
- The command is `[GROK_BIN, "models"]`, with `capture_output=True`, `text=True`, `timeout=5`, and `cwd=WORKSPACE_DIR`.
- `grok models` does not print Antigravity's `<id><tab><label>` rows. It prints bullets such as `* grok-4.7 (default)` and `- grok-4.6`. Each line is stripped of a trailing `\r`, then matched with `^[*+-]\s+(\S+)`. Prose lines (`You are logged in…`, `Default model: …`, `Available models:`) are ignored.
- A known id keeps its existing dropdown label through `_label_for_grok_model()`. An unknown id is title-cased from its hyphenated name (`grok-9-preview` becomes `Grok 9 Preview`). Numeric tokens such as `4.7` stay unchanged. If two different ids would share one label, the second label is disambiguated as `Label (model-id)`.
- Any failure (timeout, non-zero exit, empty parse, or exception) returns a copy of `FALLBACK_MODELS_MAP`:
  - `Grok 4.7` → `grok-4.7`
  - `Grok 4.7 Build Fast` → `grok-4.7-build-fast`
  - `Grok 4.6` → `grok-4.6`
  - `Grok 4.5` → `grok-4.5`
- `DEFAULT_MODEL` stays `Grok 4.7` when that label is present. Otherwise it is the first discovered label. On this machine the live query returned exactly the four fallback models, with `Grok 4.7` first.

## 2. Tool-call summaries no longer dump large payloads (`summarize_tool_input`)

[web_app_grok.py#L211-L234](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_grok.py#L211-L234)

**Problem.** The Antigravity bug was a missing `"Path"` key, so `write_file` fell through to `json.dumps` and put the whole file body in the tool panel and toast. Grok's own tools already used `file_path` and `target_file`, so that exact key was not the Grok failure. Two Grok cases still dumped too much:

- `write` and `search_replace` carry `content`, `old_string`, or `new_string` beside the path. The path keys were already preferred, but PascalCase aliases such as `Path` were not.
- `spawn_subagent` carries a long `prompt` plus a short `description`. The old key order matched `prompt` first, so the toast showed the full subagent brief.
- `list_dir` sends `target_directory`, which was not in the list, so the panel showed the raw JSON object.

**Change.** The first non-empty string wins, and short identifiers are checked before `prompt`:

1. `command`, `cmd`
2. `target_file`, `file_path`, `path`, `Path`, `TargetFile`, `AbsolutePath`, `target_directory`, `DirectoryPath`
3. `pattern`, `query`, `Query`, `Queries`, `url`, `Url`
4. `description`, `subagent_type`, `Role`, `TypeName`
5. `script_path`
6. `prompt`, `Prompt`

`content`, `old_string`, and `new_string` are never selected. If nothing matches, the function still falls back to `json.dumps`.

Checked results:

| Payload | Shown text |
| --- | --- |
| `write` with `file_path` and a long `content` | the file path |
| `Path` plus `Content` | the path |
| `list_dir` `target_directory` | the directory |
| `spawn_subagent` with `prompt`, `description`, and `subagent_type` | the short description |
| `image_gen` with only `prompt` | the image prompt |
| `run_terminal_command` with `command` and `description` | the command |

`Queries`, `Role`, and `TypeName` are included so a payload that uses the Antigravity names still summarizes cleanly. Grok's live tools use the snake_case names above. List values are not joined; only a string value is returned.

## 3. Blank lines between text and thinking that a tool call separates

[web_app_grok.py#L400-L449](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_grok.py#L400-L449) and the per-turn state at [web_app_grok.py#L970-L977](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_grok.py#L970-L977)

**Problem.** `streaming-json` emits `text` and `thought` chunks, then a `tool_call`, then later chunks. `apply_grok_event` appended every chunk directly. A sentence before a tool and a Markdown heading after it became `I will retrieve the passage now.# Romans 8 Study`. `notified_think` was set on the first thought and never cleared, so a later reasoning phase produced no new "Grok thinking" toast and ran into the previous thinking text.

**Change.** Each turn starts with `needs_paragraph_break` and `needs_think_break` set to false.

- A `tool_call` sets both flags and sets `notified_think` back to false.
- The next `text` chunk, when `state["text"]` is non-empty and does not already end in `\n\n`, strips trailing newlines and appends `\n\n` before the new chunk. The flag is then cleared, so later chunks of the same reply stay contiguous.
- The next `thought` chunk does the same for `state["thinking"]` before the 8000-character clip. Because `notified_think` was cleared by the tool call, that new thinking phase sends one progress toast again.

An empty reply does not gain a leading break. A tool call before any text only arms the flag.

Checked sequence:

1. `text`: `I will retrieve the passage now.`
2. `thought`: `Looking up Romans 8.` (`notified_think` becomes true)
3. `tool_call` `write` with a 5000-character `content` (`notified_think` becomes false; the runtime log contains `biblemate/romans.md` and not the body)
4. `thought`: `Now writing the study.`
5. `text`: `# Romans 8 Study`
6. another `text` chunk in the same step: `\n\nBody.`

Resulting reply text: `I will retrieve the passage now.\n\n# Romans 8 Study\n\nBody.`

Resulting thinking text: `Looking up Romans 8.\n\nNow writing the study.`

## 4. Removed the unused `BIBLE_REF_PATTERN`

The scripture-reference regex that used to sit beside `MODELS_MAP` was never read. The Antigravity app removed it rather than wiring a bare-reference fast path, and the same removal was applied here. `re` stays imported because persona parsing and the `grok models` line matcher still use it.

Direct slash commands such as `/bible John 3:16` still go through `parse_direct_command()` and `run_direct_retriever()`. A bare `John 3:16` with skill `Auto` still goes to Grok.

## Not ported

### System-instruction dedup and `--disable-slash-commands`

Antigravity prepended `[System Instructions]` to the user message on every resumed turn, so the same rules piled up in the conversation. It now tracks `(persona, skill)` and sends that block only on the first turn or when the pair changes, and it passes `--disable-slash-commands`.

Grok does not put those rules in the user prompt. [run_grok_turn](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_grok.py#L962-L995) writes only the user's text to the prompt file and passes BibleMate rules with `--rules` on every invocation, including `--resume`. Grok rebuilds the system prompt for that process and wraps `--rules` in a `<human_rules>` block. The rules are not stored as user turns in the session summary or prompt context. Omitting `--rules` after the first turn would drop the persona and enforced-skill instructions on later turns. `grok --help` has no `--disable-slash-commands` flag. Headless prompts are sent as text, and the page already has its own slash-command autocomplete.

### Effort selector

The Antigravity notes listed `--effort` as optional, and the applied Antigravity change did not add a selector. Grok model ids do not encode effort the way Antigravity ids such as `gemini-3.8-flash-medium` do. `grok` accepts `--reasoning-effort` / `--effort` with `low`, `medium`, `high`, and `xhigh` for the current models (the CLI also documents `none`, `minimal`, and `max` when a model advertises them). The settings drawer still has only the model dropdown. No effort flag is passed, so each turn uses the CLI default for that model.

## Verification

Checked with `/home/eliran/ai/bin/python` (the environment that has NiceGUI), without starting the server:

- Importing the module ran `discover_grok_models()`. `MODELS_MAP` was `Grok 4.7`, `Grok 4.7 Build Fast`, `Grok 4.6`, and `Grok 4.5`. `DEFAULT_MODEL` was `Grok 4.7`.
- `BIBLE_REF_PATTERN` is no longer a module attribute.
- The `summarize_tool_input` cases in the table above passed.
- A `BibleMateApp` instance fed the six-event sequence above produced the reply text, thinking text, toast-reset flag, and tool log described in section 3.
- `_label_for_grok_model("grok-9-preview", FALLBACK_MODELS_MAP)` returned `Grok 9 Preview`.
