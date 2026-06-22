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
2. **Left Drawer (Collapsible Workspace Tree)**:
   - Displays files recursively in folders: [biblemate/](file:///Users/admin/dev/antigravity-biblemate-workspace/biblemate), [export/](file:///Users/admin/dev/antigravity-biblemate-workspace/export), [images/](file:///Users/admin/dev/antigravity-biblemate-workspace/images), and [docs/](file:///Users/admin/dev/antigravity-biblemate-workspace/docs).
   - Dynamically filters Markdown (`.md`), images (`.png`, `.jpg`, `.jpeg`), and Word (`.docx`) documents.
   - Clicking `.md` or images loads them in the Document Reader, while clicking `.docx` files triggers an instant client download.
   - **Refresh Button**: Dynamically reloads the sidebar file tree to display new files.
   - **🗑 Delete Button (Red)**: Context-aware delete button. Securely restricts folder/file deletion to nested folders. All `README.md` files (case-insensitive) and the `docs/` documentation directory/files are explicitly protected from deletion.
   - **📥 Export Button (Blue)**: Shows only when a Markdown (`*.md`) file is selected. Invokes `pandoc` asynchronously to compile it to a Word document inside `export/docx/`, prefixed with a `YYYY-MM-DD-HH-MM-SS_` timestamp.
3. **Right Drawer (Settings Panel)**:
   - **AI Model**: Selection dropdown mapping to active Gemini API models.
   - **Active Persona**: Dynamically parsed from [.agents/agents.md](file:///Users/admin/dev/antigravity-biblemate-workspace/.agents/agents.md) on startup.
   - **Enforced Skill**: Dynamically scanned from [.agents/skills/](file:///Users/admin/dev/antigravity-biblemate-workspace/.agents/skills) directories on startup.
4. **Chat Panel (Interactive Input)**:
   - **Autocomplete Dropdown**: When Enforced Skill is `'Auto'` and user types `/`, a scrollable dropdown suggestions menu displays matching command names in real time. Clicking a command inserts it with a trailing space and focuses the textarea.
   - **Keyboard Shortcuts**: Pressing `Ctrl+S` (or `Cmd+S` on Mac) while typing inside the textarea triggers the send action immediately and blocks default browser Save As dialogs.
   - Chat bubbles render output in clean, formatted Markdown.
5. **Dynamic Skill Enforcement**:
   - When the Settings dropdown is set to `'Auto'` and the query starts with a matched slash command (e.g. `/meaning`, `/character`, `/bible`, etc.), the app extracts the command and enforces it dynamically as the critical task requirement for the agent.
6. **Agent Progress Console**:
   - Submitting a query activates a real-time monitor panel.
   - **Thinking Monologue**: Displays the agent's internal thoughts and reasoning in real time.
   - **Executed Tools/Skills**: Displays the active command-line script running under the hood and its raw terminal output.
   - **System Logs**: A dark retro terminal window showing logging events.
7. **Auto-Approve Policy**:
   - Integrates the Antigravity `policy.allow_all()` hook to allow the agent to run the python SQLite retrievers autonomously without prompting the user.

---

## Getting Started

### 1. Prerequisites
Ensure you have the required dependencies installed:
```bash
pip install google-antigravity nicegui Pillow
```
Also ensure `pandoc` is installed on your system to enable Word exports.

### 2. Run the Web Application
Execute the script from the root of the workspace:
```bash
python3 web_app.py
```

Open your browser and navigate to:
[http://localhost:33377](http://localhost:33377)