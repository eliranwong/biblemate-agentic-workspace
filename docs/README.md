## Documentation

For in-depth details about the ecosystems, standalone web applications, workflows, slash commands, and team structure, please refer to the files under the current directory:

- **[standalone_web_app.md](standalone_web_app.md)**: A complete setup and usage guide for the standalone NiceGUI web applications:
  - **`web_app_agy.py`** (Default port `33380`): Backed by your signed-in Antigravity CLI (`agy -p` headless mode; reuses your active Google subscription with **no Gemini API key required**).
  - **`web_app_gemini_api_key.py`** (Default port `33377`): Backed by the `google-antigravity` Python SDK (requires a Gemini API key exported as `GEMINI_API_KEY`).
  - **`web_app_claude.py`** (Default port `33379`): Backed by your signed-in Claude Code CLI (`claude -p` headless mode; no separate Anthropic API key needed).
  - **`web_app_grok.py`** (Default port `33378`): Backed by your signed-in Grok Build session via `grok login` (headless mode; no separate xAI API key needed).
  Covers installation, launching, live agent pipeline consoles, slash commands, local database direct retrieval, inline markdown editing, image generation, and troubleshooting.
- **[automate_web_app.md](automate_web_app.md)**: A guide for automating headless background startup for BibleMate web apps on Linux servers, cloud VMs, Grok Bot instances, and containers via shell profiles (`~/.bashrc`) or `systemd`.
- **[claude_code_ecosystem.md](claude_code_ecosystem.md)**: How to use the Claude Code (Anthropic) BibleMate ecosystem under `.claude/`—setup, slash commands, subagents/personas, scripture rules, regeneration, and troubleshooting.
- **[grok_build_ecosystem.md](grok_build_ecosystem.md)**: How to use the Grok Build (xAI) BibleMate ecosystem under `.grok/`—setup, slash commands, personas/agents, scripture rules, regeneration, and troubleshooting.
- **[ai_team_personas.md](ai_team_personas.md)**: Detailed profiles, guidelines, and expertise profiles for each of the 15 custom AI study personas.
- **[slash_commands.md](slash_commands.md)**: A complete reference guide for all 125 custom slash commands (workflows), organized by study category with syntax examples.
- **[study_outputs.md](study_outputs.md)**: A guide explaining where and how study outputs, images, and Word exports are saved within your workspace, highlighting benefits for pastoral and scholarly workflows.