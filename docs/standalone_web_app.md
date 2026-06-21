# Standalone Web Application — Setup & Usage Guide

The **Antigravity BibleMate Web App** is a self-contained, browser-based control centre that lets you run the full suite of BibleMate AI agents, monitor their execution in real time, browse generated study reports, and view AI-generated biblical images — all from any modern web browser on your local machine.

> **Main entry point:** [`web_app.py`](../web_app.py)  
> **Default URL:** [http://localhost:33377](http://localhost:33377)

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Running the Application](#3-running-the-application)
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

### Required Software

| Dependency | Version | Purpose |
| :--- | :--- | :--- |
| Python | ≥ 3.10 | Runtime |
| `google-antigravity` | latest | AI agent SDK |
| `nicegui` | latest | Web UI framework |
| `Pillow` | latest | Image format conversion |

### System Requirements

- A valid **Google Antigravity** account with an active session (`antigravity auth login`)
- The **BibleMate workspace** cloned from the repository with all `.agents/` skills and database files in place

---

## 2. Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/eliranwong/antigravity-biblemate-workspace.git
cd antigravity-biblemate-workspace
```

### Step 2: Install Python Dependencies

```bash
pip install google-antigravity nicegui Pillow
```

> **Tip:** If you use `pyenv` or `venv`, activate your environment first before installing.

### Step 3: Authenticate with Google Antigravity

The web app uses the Antigravity SDK to run AI agents. Make sure you are authenticated:

```bash
antigravity auth login
```

Follow the browser prompts to complete authentication. The session is stored locally and reused automatically by the web app.

---

## 3. Running the Application

Navigate to the root of the workspace directory and run:

```bash
python3 web_app.py
```

The server will start and output:

```
NiceGUI ready to go on http://localhost:33377
```

Open your browser and navigate to:

**[http://localhost:33377](http://localhost:33377)**

> **Note:** The app **does not open a browser automatically** by design. You must open the URL manually. The server runs in the foreground — press `Ctrl+C` to stop it.

### Running in the Background (Optional)

To keep the server running after closing the terminal:

```bash
nohup python3 web_app.py > web_app.log 2>&1 &
```

To stop it later:

```bash
kill $(pgrep -f "web_app.py")
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

### Chat Workspace (Default Tab)

The primary area for submitting study requests and viewing agent responses.

- **User messages** appear as right-aligned indigo bubbles
- **Agent responses** are rendered as formatted Markdown on the left
- The **Agent Progress Console** (expandable panels) shows:
  - **Agent Thinking Monologue** — real-time reasoning/planning steps
  - **Currently Executed Tool/Skill** — the active script and its stdout output
  - **System Logs** — a live terminal window with logger events

### Document Reader Tab

Displays the contents of any file selected from the left-hand file tree. Supports:

- **Markdown files** (`.md`) — rendered with full formatting
- **Image files** (`.png`, `.jpg`, `.jpeg`) — displayed inline with rounded styling

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

> **See Also:** [`docs/slash_commands.md`](slash_commands.md) for the complete reference of all 114+ commands.

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

The `/image` slash command uses the Antigravity SDK's built-in image generation capability to create **Bible-related images** on demand.

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

1. The agent invokes the `.agents/skills/image/image_generator.py` script
2. The script calls the Antigravity `generate_image` tool via a dedicated Agent session
3. The generated image is saved to the `images/` directory with a timestamped filename

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

## 7. File Tree & Document Reader

The left drawer contains a dynamic file tree showing all saved study outputs and generated images, organized into three root folders:

| Folder | Contents |
| :--- | :--- |
| `biblemate/` | Markdown study outputs saved by BibleMate skills |
| `export/` | Exported `.md` and `.docx` files |
| `images/` | AI-generated Bible images (`.png`, `.jpg`, `.jpeg`) |

### Selecting a File

- Click any **`.md`** file to open and render it in the Document Reader tab
- Click any **image file** to display it inline in the Document Reader tab
- The app switches to the **Reader tab** automatically upon selection

### Refreshing the Tree

After a study run, click the **↻** button in the drawer header to reload the tree and see newly generated files.

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

Select from the available Gemini models:

| Label | SDK Model String |
| :--- | :--- |
| Gemini 3.5 Flash | `gemini-3.5-flash` |
| Gemini 3.5 Pro | `gemini-3.5-pro` |
| Gemini 2.0 Flash | `gemini-2.0-flash` |
| Gemini 1.5 Pro | `gemini-1.5-pro` |
| Gemini 1.5 Flash | `gemini-1.5-flash` |

### Active Persona

Choose a specialized AI study persona or leave on **Auto** (recommended for most tasks). Personas are dynamically parsed from `.agents/agents.md` at startup.

See [`docs/ai_team_personas.md`](ai_team_personas.md) for the full list and descriptions.

### Enforced Skill

Force the agent to use a specific skill (e.g., `bible`, `commentary`, `sermon`) regardless of the query type. Leave on **Auto** to allow the agent to pick the best skill dynamically.

### Appearance

Toggle **Dark Mode / Light Mode** using the switch in the settings panel.

---

## 10. Troubleshooting

### Agent keeps spinning without producing output

**Cause:** The Antigravity SDK session may not be authenticated, or the workspace's `.agents/` directory is not being picked up.

**Fix:**
1. Re-authenticate: `antigravity auth login`
2. Ensure you run `python3 web_app.py` from the **workspace root** (the same directory containing `.agents/`)
3. Check the **System Logs** panel in the UI for specific error messages

---

### Input text is invisible (white on white)

**Cause:** A browser or OS theme conflict with the NiceGUI textarea styling.

**Fix:** Toggle **Dark Mode** in the Settings drawer. In dark mode the textarea text renders correctly as white text on a dark background. If using light mode, try a different browser (Chrome is recommended).

---

### Images not appearing in the file tree

**Cause:** The file tree was not refreshed after generation.

**Fix:** Click the **↻ Refresh** button at the top of the left drawer. If the image still doesn't appear, check that the `images/` directory exists in the workspace root and that `image_generator.py` completed without errors (check System Logs).

---

### Port 33377 is already in use

**Fix:** Kill the existing process occupying the port:

```bash
lsof -ti tcp:33377 | xargs kill -9
```

Then restart the app.

---

### `google-antigravity` not found

**Fix:**

```bash
pip install google-antigravity
```

If using a virtual environment or pyenv, ensure the correct Python interpreter is active:

```bash
which python3
pip install google-antigravity nicegui Pillow
```

---

*For further information on skills, personas, and slash commands, see the other files in this `docs/` directory.*
