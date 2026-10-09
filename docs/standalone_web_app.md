# Standalone Web Applications — Setup & Usage Guide

The **BibleMate Agentic Web App** is a self-contained, browser-based control centre built with [NiceGUI](https://nicegui.io) that lets you run the full suite of BibleMate AI agents, monitor their execution in real time, browse generated study reports, and view AI-generated biblical images — all from any modern web browser on your local machine.

This workspace provides **four platform-native web applications** sharing the identical UI and feature set:

| Platform | Entry Script | Default Port | Port Override Env | Backend / Credentials |
| :--- | :--- | :--- | :--- | :--- |
| **Antigravity CLI (`agy`)** | [`web_app_agy.py`](../web_app_agy.py) | `33380` | `BIBLEMATE_AGY_PORT` | Signed-in Antigravity CLI (`agy -p` headless mode; Google subscription, no API key needed) |
| **Google Antigravity (SDK)** | [`web_app_gemini_api_key.py`](../web_app_gemini_api_key.py) | `33377` | *(fixed)* | `google-antigravity` SDK (requires `GEMINI_API_KEY`) |
| **Claude Code** | [`web_app_claude.py`](../web_app_claude.py) | `33379` | `BIBLEMATE_CLAUDE_PORT` | Signed-in Claude Code CLI (`claude -p` headless mode; no API key needed) |
| **Grok Build** | [`web_app_grok.py`](../web_app_grok.py) | `33378` | `BIBLEMATE_GROK_PORT` | Signed-in Grok Build session via `grok login` (headless mode; no API key needed) |

<img width="1511" height="860" alt="Image" src="https://github.com/user-attachments/assets/c76d8e4b-5188-4f02-92aa-79d985f68523" />

> [!TIP]
> **Choosing Between `web_app_agy.py` and `web_app_gemini_api_key.py`:**
> - **Use `web_app_agy.py` (Recommended)** if you are logged into the Antigravity CLI (`agy`) with your Google subscription (e.g. Gemini Advanced or Google One AI Premium). It uses the CLI's headless print stream mode (`agy -p --output-format stream-json --dangerously-skip-permissions`), reuses your active login session automatically, supports multi-turn chat continuation via `--conversation <id>`, and **requires NO Gemini API key**.
> - **Use `web_app_gemini_api_key.py`** if you prefer running against the `google-antigravity` Python SDK directly with an explicit `GEMINI_API_KEY`.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Running the Applications](#3-running-the-applications)
4. [UI Layout & Features](#4-ui-layout--features)
5. [Slash Commands in the Chat Bar](#5-slash-commands-in-the-chat-bar)
6. [Image Generation (`/image`)](#6-image-generation-image)
7. [File Tree & Document Reader](#7-file-tree--document-reader)
8. [Stopping Agent Execution](#8-stopping-agent-execution)
9. [Configuration & Settings](#9-configuration--settings)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Prerequisites

Before running the web app, ensure the following dependencies are installed on your machine.

### Required Software (Common)

| Dependency | Version | Purpose |
| :--- | :--- | :--- |
| Python | ≥ 3.10 | Runtime |
| `nicegui` | latest | Web UI framework |
| `Pillow` | latest | Image format conversion |
| `biblematedata` | latest | Local scripture database manager |

### Platform-Specific Requirements

- **For Google Antigravity SDK (`web_app_gemini_api_key.py`)**:
  - `google-antigravity` Python package installed
  - `GEMINI_API_KEY` exported in your environment (`export GEMINI_API_KEY="your-api-key"`)
- **For Antigravity CLI (`web_app_agy.py`)**:
  - `agy` CLI installed on `PATH` or at `~/.local/bin/agy`
  - Signed in with your Google subscription (no API key needed)
- **For Claude Code (`web_app_claude.py`)**:
  - Claude Code CLI installed on `PATH`
  - Active Claude Code sign-in (reused automatically; no separate Anthropic API key needed)
- **For Grok Build (`web_app_grok.py`)**:
  - Grok Build CLI installed on `PATH` or at `~/.grok/bin/grok`
  - Signed in via `grok login` (`~/.grok/auth.json` reused automatically; no separate xAI API key needed)
- **Shared Data**: Installed and initialized local Bible databases via `biblematedata`

---

## 2. Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/eliranwong/antigravity-biblemate-workspace.git
cd antigravity-biblemate-workspace
```

### Step 2: Install Common Python Dependencies & Databases

```bash
pip install --upgrade biblematedata nicegui Pillow
biblematedata
```

### Step 3: Install Platform Backend & Authenticate

- **For Antigravity SDK (`web_app_gemini_api_key.py`)**:
  ```bash
  pip install google-antigravity
  export GEMINI_API_KEY="your-gemini-api-key"
  ```
- **For Antigravity CLI (`web_app_agy.py`)**:
  Ensure the `agy` CLI is installed and signed into your Google subscription account.
- **For Claude Code (`web_app_claude.py`)**: Ensure the `claude` CLI is installed and you are signed in.
- **For Grok Build (`web_app_grok.py`)**: Ensure the `grok` CLI is installed and authenticate with `grok login`.

---

## 3. Running the Applications

Run the script corresponding to your platform from the workspace root directory:

### Option A: Antigravity CLI Web App (Port 33380) — *Recommended for Google Subscription*
```bash
python3 web_app_agy.py
```
Open **[http://localhost:33380](http://localhost:33380)** in your browser. (Override port with `BIBLEMATE_AGY_PORT=<port>`). Uses your signed-in Antigravity CLI session without requiring an API key.

### Option B: Claude Code Web App (Port 33379)
```bash
python3 web_app_claude.py
```
Open **[http://localhost:33379](http://localhost:33379)** in your browser. (Override port with `BIBLEMATE_CLAUDE_PORT=<port>`).

### Option C: Grok Build Web App (Port 33378)
```bash
python3 web_app_grok.py
```
Open **[http://localhost:33378](http://localhost:33378)** in your browser. (Override port with `BIBLEMATE_GROK_PORT=<port>`).

### Option D: Google Antigravity SDK Web App (Port 33377)
```bash
export GEMINI_API_KEY="your-gemini-api-key"
python3 web_app_gemini_api_key.py
```
Open **[http://localhost:33377](http://localhost:33377)** in your browser.

> **Note:** The web apps **do not open a browser automatically** by design. You must open the URL manually. The server runs in the foreground — press `Ctrl+C` to stop it. Because each variant uses a distinct port, you can run multiple apps concurrently!

### Running in the Background (Optional)

To keep a server running after closing the terminal:

```bash
# Example for Antigravity CLI web app:
nohup python3 web_app_agy.py > web_app_agy.log 2>&1 &

# Example for Claude Code web app:
nohup python3 web_app_claude.py > web_app_claude.log 2>&1 &

# Example for Grok Build web app:
nohup python3 web_app_grok.py > web_app_grok.log 2>&1 &

# Example for Antigravity SDK web app:
nohup python3 web_app_gemini_api_key.py > web_app_gemini_api_key.log 2>&1 &
```

To stop a background server:

```bash
kill $(pgrep -f "web_app_agy.py")
# or: kill $(pgrep -f "web_app_claude.py")
# or: kill $(pgrep -f "web_app_grok.py")
# or: kill $(pgrep -f "web_app_gemini_api_key.py")
```

---

## 4. UI Layout & Features

The interface is divided into several key areas:

### Header Bar

| Element | Description |
| :--- | :--- |
| **☰ Menu** | Toggles the left-side file tree drawer |
| **BibleMate Logo** | Application title |
| **+ (New Conversation)** | Clears the current chat history |
| **Chat / Reader Tabs** | Switches between the chat workspace and the document reader |
| **⚙ Settings** | Toggles the right-side settings drawer |

### Left Sidebar Drawer (File Tree)

Displays all files in your workspace. It features context-aware controls:
- **↻ Refresh Button**: Refreshes the file tree dynamically to load new files.
- **🗑 Delete Button (Red)**: Displays when a deletable file or folder is selected. Prompts with a confirmation modal. Folder/file deletion is strictly restricted to nested workspace contents under `biblemate/`, `images/`, `export/`, and `notes/`. All `README.md` files (case-insensitive) and the `docs/` folder/documentation files are protected and cannot be deleted.
- **📥 Export Button (Blue)**: Displays only when a Markdown (`*.md`) file is selected. Clicking this button converts the markdown file into a Word Document (`.docx`) using `pandoc`. The exported file is named with the format `YYYY-MM-DD-HH-MM-SS_<original_name>.docx` and saved in `export/docx/`.
- **Edit Button (Green pencil)**: Displays when a deletable markdown file is selected. Opens the file in the browser-based inline text editor for modification.
- **Add File/Folder Buttons**: Display when selecting the `notes` folder or any nested subfolder inside it, allowing user-driven file and folder creation.


### Chat Workspace (Default Tab)

The primary area for submitting study requests and viewing agent responses.

- **User messages** appear as right-aligned bubbles.
- **Agent responses** are rendered as formatted Markdown on the left.
- **Slash Command Autocomplete Dropdown**: When typing a slash (`/`) inside the input bar (only if the Enforced Skill is set to `'Auto'`), a scrollable autocomplete dropdown displays matching commands in real time. Clicking an option inserts it and focuses the input.
- **Ctrl+S / Cmd+S Send Shortcut**: Pressing `Ctrl+S` (or `Cmd+S` on Mac) while typing in the textarea immediately sends the request, avoiding browser save dialogs.
- **Agent Progress Console** (expandable panels) shows:
  - **Agent Thinking Monologue** — real-time reasoning/planning steps.
  - **Currently Executed Tool/Skill** — the active script and its stdout output.
  - **System Logs** — a live terminal window with logger events.

### Document Reader Tab

Displays selected workspace files. Supports:
- **Markdown files** (`.md`) — rendered with full formatting.
- **Image files** (`.png`, `.jpg`, `.jpeg`) — displayed inline.
- **DOCX files** (`.docx`) — selecting a `.docx` file triggers a client-side download instead of viewing.

---

## 5. Slash Commands in the Chat Bar

All slash commands from the `.agents/workflows/` directory are fully supported in the chat input bar. Simply type a slash command followed by your query.

### Examples

```
/bible NET KJV John 3:16-18
/sermon Romans 8:28-39
/translate-greek John 1:1
/commentary John 3:16
/devotion Psalm 23
/image The Good Shepherd in golden light
/search love+mercy in NET
```

> **See Also:** [`docs/slash_commands.md`](slash_commands.md) for the complete reference of all 120 commands.

### Direct Retrieval Commands

The following commands bypass the full AI agent pipeline and call local SQLite scripts directly for instant results:

| Command | Action |
| :--- | :--- |
| `/bible` | Retrieves verse text from local Bible databases |
| `/commentary` | Retrieves commentary text from local databases |
| `/xrefs` | Retrieves cross-references |
| `/lexicon` | Retrieves Strong's number definitions |
| `/morphology` | Retrieves morphology/grammar data |
| `/interlinear` | Retrieves interlinear Greek/Hebrew text |
| `/original` | Retrieves original language (OHGB) text |

---

## 6. Image Generation (`/image`)

The `/image` slash command creates **Bible-related images** on demand across the web applications.

### Usage

```
/image <description of the image>
```

### Examples

```
/image The Sermon on the Mount with golden light rays breaking through clouds
/image Jesus walking on water at night, moonlit, painterly style
/image The Last Supper, renaissance painting style
```

### How It Works

1. In **`web_app_agy.py`** and **`web_app_gemini_api_key.py`**: The agent invokes the built-in `generate_image` tool or `.agents/skills/image/image_generator.py` script.
2. In **`web_app_grok.py`**: The agent uses Grok's image generation tool and places the file using `.grok/skills/image/image_placer.py`.
3. In **`web_app_claude.py`**: The agent uses the configured image creation skill.
4. The generated image is saved to the workspace `images/` directory with a timestamped filename.

### Filename Format

```
YYYY-MM-DD-HH-MM-SS_<image-title>.png
```

**Example:** `2026-06-21-20-45-00_sermon_on_the_mount.png`

### Viewing Generated Images

After generation completes:

1. Click the **☰ menu** to open the left drawer
2. Expand the **`images`** folder in the file tree
3. Click on any image filename to display it in the **Document Reader** tab

> **Tip:** If you don't see the new image, click the **↻ Refresh** button at the top of the file tree drawer.

---

## 7. File Tree, Document Reader & Editor

The left drawer contains a dynamic file tree showing all saved study outputs, generated images, notes, and documentation, organized into five root folders:

| Folder | Contents |
| :--- | :--- |
| `biblemate/` | Markdown study outputs saved by BibleMate skills |
| `export/` | Exported `.md` and `.docx` files |
| `images/` | AI-generated Bible images (`.png`, `.jpg`, `.jpeg`) |
| `notes/` | User-created notes, subfolders, and documents |
| `docs/` | System setup and usage documentation |

### Selecting a File & Previewing

- Click any **`.md`** file (e.g. from `biblemate/`, `export/`, `notes/`, or `docs/`) to open and render it in the Document Reader tab.
- Click any **image file** to display it inline in the Document Reader tab.
- Click any **`.docx`** file to trigger a client-side download automatically.
- Selecting a file switches the app to the **Reader tab** (except for `.docx` files, which download directly).

### Editing Markdown Files Inline

You can edit any user-modifiable markdown file (located under `biblemate/`, `export/`, or `notes/`, excluding `README.md` files) directly in your browser:
1. Select the markdown file in the sidebar file tree.
2. Click the green **Edit (pencil icon)** button in the sidebar header.
3. The Document Reader panel transforms into an interactive text editor.
4. Modify the markdown content, and click **Save** to write changes to disk and return to the preview layout, or click **Cancel** to discard edits.

### File & Folder Creation in `notes/`

When you select the root `notes/` directory or any subfolder within it, two new action buttons appear in the sidebar header:
* **Add File** (📄 icon): Prompts you for a filename, creates a new markdown file (automatically appends `.md` if omitted), and saves it under the selected directory.
* **Add Folder** (📁 icon): Prompts you for a folder name and creates a new subfolder under the selected directory. Empty subfolders display immediately in the file tree.

### Protected Folders and Files

To prevent accidental data loss, the web application explicitly blocks deletion of:
- Root directories (`biblemate`, `images`, `export`, `docs`, `notes`)
- Any `README.md` file (case-insensitive) in any directory
- Any file or subdirectory inside the `docs/` folder

### Refreshing the Tree

After a study run, file creation, or export, click the **↻** button in the drawer header to reload the tree and see newly generated files/folders.


---

## 8. Stopping Agent Execution

While an agent is running, the **Send** button in the footer changes into a **Stop** button (red, `■` icon).

- Click **Stop** to cancel the currently running agent task immediately
- The chat will display: *"Agent execution stopped by user."*
- The button automatically reverts to **Send** when the agent finishes or is stopped

> **Note:** Stopping cancels the AI inference stream. Any partially streamed content will remain visible in the chat.

---

## 9. Configuration & Settings

Open the **⚙ Settings** drawer (top-right) to adjust:

### AI Model

Model choices in the **⚙ Settings** drawer adapt to the web application you are running:

#### Google Antigravity (`web_app_gemini_api_key.py`)
| Label | SDK Model String |
| :--- | :--- |
| Gemini 3.5 Flash | `gemini-3.5-flash` |
| Gemini 3.5 Pro | `gemini-3.5-pro` |
| Gemini 2.0 Flash | `gemini-2.0-flash` |
| Gemini 1.5 Pro | `gemini-1.5-pro` |
| Gemini 1.5 Flash | `gemini-1.5-flash` |

#### Antigravity CLI (`web_app_agy.py`)
| Label | Model ID | Description |
| :--- | :--- | :--- |
| Default (session default) | `None` | Uses the session default configured in Antigravity CLI |
| Gemini 3.6 Flash (Medium) | `gemini-3.6-flash-medium` | Fast and highly capable everyday study model (Default) |
| Gemini 3.6 Flash (High) | `gemini-3.6-flash-high` | Flash model with higher reasoning depth |
| Gemini 3.6 Flash (Low) | `gemini-3.6-flash-low` | Rapid turnaround for quick verse lookups |
| Gemini 3.1 Pro (High) | `gemini-3.1-pro-high` | Flagship reasoning and complex theological synthesis |
| Claude Opus 5.5 (Medium) | `claude-opus-5-5-medium` | Anthropic Opus via your Antigravity Google subscription |
| Claude Sonnet 5.5 (Medium) | `claude-sonnet-5-5-medium` | Balanced Claude model via Google subscription |
| GPT-OSS 120B (Medium) | `gpt-oss-120b-medium` | Open-source large language model |

#### Claude Code (`web_app_claude.py`)
| Label | Model / Flag | Description |
| :--- | :--- | :--- |
| Default (session default) | `None` | Uses the session default configured in Claude Code |
| `opus` | `opus` | Top-tier intelligence for deep biblical synthesis |
| `sonnet` | `sonnet` | Fast and capable balance for sermons and studies |
| `fable` | `fable` | Fable family models |
| `haiku` | `haiku` | Ultra-fast responses for quick verse lookups |

#### Grok Build (`web_app_grok.py`)
| Label | Model ID | Description |
| :--- | :--- | :--- |
| Grok 4.7 | `grok-4.7` | Flagship reasoning and biblical exegesis |
| Grok 4.7 Build Fast | `grok-4.7-build-fast` | High speed build variant |
| Grok 4.6 | `grok-4.6` | Stable high-intelligence generation |
| Grok 4.5 | `grok-4.5` | Standard reasoning model |

### Active Persona

Choose a specialized AI study persona or leave on **Auto** (recommended for most tasks). Personas are dynamically parsed at startup:
- `.agents/agents.md` in `web_app_gemini_api_key.py` and `web_app_agy.py`
- `.claude/agents.md` in `web_app_claude.py`
- `.grok/agents.md` in `web_app_grok.py`

See [`docs/ai_team_personas.md`](ai_team_personas.md) for the full list and descriptions.

### Enforced Skill

Force the agent to use a specific skill (e.g., `bible`, `commentary`, `sermon`) regardless of the query type. Leave on **Auto** to allow the agent to pick the best skill dynamically. Skills are dynamically discovered from `.agents/skills`, `.claude/skills`, or `.grok/skills`.

### Appearance

Toggle **Dark Mode / Light Mode** using the switch in the settings panel.

---

## 10. Troubleshooting

### Agent keeps spinning without producing output

**Cause:** The backend session may not be authenticated, or the workspace directory is not being picked up.

**Fix:**
- **For `web_app_agy.py`**: Ensure `agy` CLI is on PATH or at `~/.local/bin/agy` and authenticated with your Google subscription. Run `agy models` in terminal to verify access.
- **For `web_app_gemini_api_key.py`**: Ensure `GEMINI_API_KEY` is exported and `.agents/` is present.
- **For `web_app_claude.py`**: Ensure `claude` CLI is on PATH and signed in. Run `claude --version` in terminal.
- **For `web_app_grok.py`**: Ensure `grok` CLI is on PATH or at `~/.grok/bin/grok` and run `grok login`.
- Ensure you run the web app script from the **workspace root**.
- Check the **System Logs** panel in the UI for specific error messages.

---

### Input text is invisible (white on white)

**Cause:** A browser or OS theme conflict with the NiceGUI textarea styling.

**Fix:** Toggle **Dark Mode** in the Settings drawer. In dark mode the textarea text renders correctly as white text on a dark background. If using light mode, try a different browser (Chrome is recommended).

---

### Images not appearing in the file tree

**Cause:** The file tree was not refreshed after generation.

**Fix:** Click the **↻ Refresh** button at the top of the left drawer. If the image still doesn't appear, check that the `images/` directory exists in the workspace root and that `image_generator.py` completed without errors (check System Logs).

---

### Port is already in use

**Fix:** Kill the existing process occupying the port, or use an environment variable to change the port:

```bash
# Check and free default ports:
lsof -ti tcp:33380 | xargs kill -9  # web_app_agy.py
lsof -ti tcp:33379 | xargs kill -9  # web_app_claude.py
lsof -ti tcp:33378 | xargs kill -9  # web_app_grok.py
lsof -ti tcp:33377 | xargs kill -9  # web_app_gemini_api_key.py

# Or launch with a custom port:
BIBLEMATE_AGY_PORT=33390 python3 web_app_agy.py
BIBLEMATE_CLAUDE_PORT=33391 python3 web_app_claude.py
BIBLEMATE_GROK_PORT=33392 python3 web_app_grok.py
```

---

### `google-antigravity` not found or no API key available

If you do not have a Gemini API key or `google-antigravity` SDK installed, use **`web_app_agy.py`** instead! It reuses your signed-in Antigravity CLI Google subscription session directly and requires no API key:

```bash
python3 web_app_agy.py
```

If you explicitly want to use the SDK version (`web_app_gemini_api_key.py`):

```bash
pip install google-antigravity
export GEMINI_API_KEY="your-gemini-api-key"
python3 web_app_gemini_api_key.py
```

---

*For further information on skills, personas, and slash commands, see the other files in this `docs/` directory.*
