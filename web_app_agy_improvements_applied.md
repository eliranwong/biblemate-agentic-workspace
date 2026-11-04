Analyzed web_app_agy.py:L80-480
Analyzed web_app_agy.py:L910-1125
Edited web_app_agy.py
Edited web_app_agy.py
Analyzed web_app_agy.py:L200-500
Edited web_app_agy.py
Edited web_app_agy.py
Edited web_app_agy.py
Analyzed web_app_agy.py:L960-1160
Edited web_app_agy.py
Edited web_app_agy.py
Analyzed web_app_gemini_api_key.py:L100-180
Analyzed web_app_gemini_api_key.py:L940-1000
Edited web_app_gemini_api_key.py
Edited web_app_gemini_api_key.py
Edited web_app_gemini_api_key.py
Ran verify syntax and model discovery in web_app_agy.py · Exited with code 1
Ran test model discovery in web_app_agy.py
Ran inspect agy models stdout/stderr when piped
Edited web_app_agy.py
Ran verify dynamic model discovery with tab separator

All improvements have been applied to [web_app_agy.py](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py) (and synced with [web_app_gemini_api_key.py](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_gemini_api_key.py)):

1. **Dynamic Model Discovery (`discover_agy_models`)** ([web_app_agy.py#L91-L140](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L91-L140))
   - Queries `agy models` at startup (parsing tab/space-delimited `<id>\t<label>` lines) to populate `MODELS_MAP` automatically from the signed-in account, with `FALLBACK_MODELS_MAP` as an offline fallback.
2. **Improved Tool Call Input Summarization (`summarize_tool_input`)** ([web_app_agy.py#L205-L224](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L205-L224), [web_app_gemini_api_key.py#L152-L171](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_gemini_api_key.py#L152-L171))
   - Added `"Path"`, `"Queries"`, `"Role"`, and `"TypeName"` so `read_file`, `write_file`, `edit_file`, and `invoke_subagent` display clean target paths/roles instead of dumping full JSON payloads.
3. **Multi-Step Response & Thinking Separation** ([web_app_agy.py#L421-L465](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L421-L465), [web_app_gemini_api_key.py#L941-L980](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_gemini_api_key.py#L941-L980))
   - Inserts `\n\n` breaks between `agent_response` and `thinking` blocks that are separated by tool calls, and resets `notified_think` after tool calls so subsequent reasoning phases surface updated progress notifications.
4. **Deduplicated `[System Instructions]` on Resumed Sessions & `--disable-slash-commands`** ([web_app_agy.py#L985-L1026](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L985-L1026), [L1158-L1165](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L1158-L1165))
   - Tracks `self.agy_last_rules_key = (self.selected_persona, active_skill)` so `[System Instructions]` is only prepended on the first turn of a session or when the persona/skill changes, and passes `--disable-slash-commands` to `agy -p`.
5. **Removed Unused `BIBLE_REF_PATTERN`** ([web_app_agy.py#L140](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_agy.py#L140), [web_app_gemini_api_key.py#L104](file:///home/eliran/dev/biblemate-agentic-workspace/web_app_gemini_api_key.py#L104)).