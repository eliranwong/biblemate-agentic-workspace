# Standalone Web Application: NiceGUI & Antigravity SDK

This document describes the design, directory layout, and execution instructions for the standalone web app configured in the workspace root.

## Overview
The web application provides a responsive, web-based control center for running local Bible study agents, monitoring their execution in real-time, and browsing generated exegesis reports.

- **Main File**: [web_app.py](file:///Users/admin/dev/antigravity-biblemate-workspace/web_app.py)
- **Default Port**: `33377`
- **Theme**: Dark Mode (default), toggleable to Light Mode.

---

## Key Features & UI Layout

1. **Responsive Flex Grid**: Adapts dynamically to desktop, tablet, and mobile browsers.
2. **Left Drawer (Collapsible Saved Studies Tree)**:
   - Displays files in the [biblemate/](file:///Users/admin/dev/antigravity-biblemate-workspace/biblemate) and [export/](file:///Users/admin/dev/antigravity-biblemate-workspace/export) folders recursively.
   - Shows only Markdown files (`.md`).
   - Includes a **Refresh** button to update the tree dynamically when new study outputs are created.
   - Selecting a file automatically loads it and switches the user to the **Document Reader** tab.
3. **Right Drawer (Settings Panel)**:
   - **AI Model**: Selection dropdown (defaults to `Gemini 3.5 Flash (High)`).
   - **Active Persona**: Dynmically parsed from [.agents/agents.md](file:///Users/admin/dev/antigravity-biblemate-workspace/.agents/agents.md) on startup. Defaults to `Auto`.
   - **Enforced Skill**: Dynamically scanned from [.agents/skills/](file:///Users/admin/dev/antigravity-biblemate-workspace/.agents/skills) directories on startup. Defaults to `Auto`.
4. **Chat Panel (Multi-line Input)**:
   - A multi-line textarea allowing long-form study prompt submissions.
   - Chat bubbles render output in clean, formatted Markdown.
5. **Agent Progress Console**:
   - Submitting a query activates a real-time monitor panel.
   - **Thinking Monologue**: Displays the agent's internal thoughts and reasoning in real time.
   - **Executed Tools/Skills**: Displays the active command-line script running under the hood (e.g. `bible_retriever.py` or `commentary_retriever.py`) and its raw terminal output.
   - **System Logs**: A dark retro terminal window showing logging events.
6. **Auto-Approve Policy**:
   - Integrates the Antigravity `policy.allow_all()` hook to allow the agent to run the python SQLite retrievers autonomously without prompting the user.

---

## Getting Started

### 1. Prerequisites
Ensure you have the required dependencies:
```bash
pip install google-antigravity nicegui
```

### 2. Run the Web Application
Execute the script from the root of the workspace:
```bash
python3 web_app.py
```

Open your browser and navigate to:
[http://localhost:33377](http://localhost:33377)

## Follow up

The UI looks nice, except, when I type my request in the request field, my entered text is white in colour against white backgrounds, which makes my typing invisible unless I select it manually with a mouse.

The agent is not running, I just tried with a simple request: John 3:16, always spinning with the message `Agent Running - Live Execution Pipeline`, no result at all.