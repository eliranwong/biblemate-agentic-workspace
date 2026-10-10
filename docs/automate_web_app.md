# Automating Web App Startup & Headless Deployment

This guide explains how to configure **automatic background startup** for the BibleMate NiceGUI web applications in headless Linux servers, cloud virtual machines, Grok Bot instances, Docker containers, or persistent remote workspaces (e.g. `/workspace/`).

With this setup, the web application runs in the background on its assigned port, automatically starts upon shell login or container initialization if not already listening, logs output to a file, and remains accessible from your browser.

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Shell Startup Automation (`~/.bashrc` / `~/.profile`)](#2-shell-startup-automation-bashrc--profile)
   - [How It Works](#how-it-works)
   - [Recommended Script for Claude Code (`web_app_claude.py`)](#recommended-script-for-claude-code-web_app_claudepy)
   - [Unified Script for Any Platform Variant](#unified-script-for-any-platform-variant)
   - [Port Reference](#port-reference)
3. [Managing Background Services](#3-managing-background-services)
   - [Checking Service Status](#checking-service-status)
   - [Viewing Live Logs](#viewing-live-logs)
   - [Stopping the Server](#stopping-the-server)
4. [Alternative: Systemd Service (Persistent Daemons)](#4-alternative-systemd-service-persistent-daemons)
5. [Troubleshooting & Best Practices](#5-troubleshooting--best-practices)

---

## 1. Environment Setup

### Step 1: Create a Dedicated Virtual Environment

Create an isolated virtual environment (e.g., at `/workspace/ai` or `~/.venv/biblemate`) and install the required dependencies:

```bash
cd /workspace/
python3 -m venv ai
source ai/bin/activate
pip install --upgrade biblematedata nicegui Pillow
```

### Step 2: Download Local Scripture Databases

Run the `biblematedata` CLI once to initialize the local SQLite Bible databases in `~/biblemate/data`:

```bash
biblematedata
```

### Step 3: Clone or Verify the BibleMate Workspace

Ensure your BibleMate workspace is cloned and located at a known path, such as `/workspace/biblemate_studies`:

```bash
git clone https://github.com/eliranwong/antigravity-biblemate-workspace.git /workspace/biblemate_studies
```

---

## 2. Shell Startup Automation (`~/.bashrc` / `~/.profile`)

### How It Works

Adding startup logic to your login configuration file (`~/.bashrc` or `~/.profile`) guarantees that:
1. **Port Detection**: It checks whether the target port (e.g. `33379`) is currently in use with `ss -H -ltn`.
2. **Conditional Launch**: If the port is **not** listening, it starts the web app in the background via `nohup` using the virtual environment's Python interpreter.
3. **Idempotence**: If the service is already running, it prints a notice and avoids launching duplicate processes.
4. **Log Redirection**: Output and errors are captured in `/tmp/` for effortless debugging.

> [!TIP]
> **Using the Virtual Environment's Python Binary:**
> Executing `/workspace/ai/bin/python3` directly ensures NiceGUI and its dependencies are loaded cleanly regardless of the system Python version or environment changes, without needing brittle hardcoded `PYTHONPATH` strings pointing to specific Python minor versions.

---

### Recommended Script for Claude Code (`web_app_claude.py`)

Add the following block to your `~/.bashrc` or `~/.profile`:

```bash
# ==============================================================================
# BibleMate Web App Auto-Start (Claude Code Variant)
# ==============================================================================
BIBLEMATE_DIR="/workspace/biblemate_studies"
BIBLEMATE_VENV_PY="/workspace/ai/bin/python3"
BIBLEMATE_PORT=33379
BIBLEMATE_LOG="/tmp/biblemate-claude-${BIBLEMATE_PORT}.log"

start_biblemate_claude() {
  echo "Starting BibleMate Claude on port ${BIBLEMATE_PORT}..."
  
  if [ -x "${BIBLEMATE_VENV_PY}" ]; then
    nohup "${BIBLEMATE_VENV_PY}" "${BIBLEMATE_DIR}/web_app_claude.py" >> "${BIBLEMATE_LOG}" 2>&1 &
  else
    # Fallback if venv python binary is not directly executable
    PYTHONPATH="/workspace/ai/lib/python3.13/site-packages${PYTHONPATH:+:$PYTHONPATH}" \
      nohup /usr/bin/python3 "${BIBLEMATE_DIR}/web_app_claude.py" >> "${BIBLEMATE_LOG}" 2>&1 &
  fi
  
  echo "BibleMate Claude started (PID: $!). Logs: ${BIBLEMATE_LOG}"
}

# Start only when port 33379 is not already listening
if ! ss -H -ltn "sport = :${BIBLEMATE_PORT}" 2>/dev/null | grep -q .; then
  start_biblemate_claude
else
  echo "BibleMate Claude is already listening on port ${BIBLEMATE_PORT}."
fi
```

---

### Unified Script for Any Platform Variant

If you run another platform variant (or switch between them), use this adaptable script:

```bash
# ==============================================================================
# BibleMate Web App Auto-Start (Configurable)
# ==============================================================================
# Target script: web_app_agy.py | web_app_claude.py | web_app_grok.py | web_app_gemini_api_key.py
APP_SCRIPT="web_app_claude.py"
APP_PORT=33379
WORKSPACE_DIR="/workspace/biblemate_studies"
PYTHON_BIN="/workspace/ai/bin/python3"
LOG_FILE="/tmp/biblemate-${APP_PORT}.log"

start_biblemate() {
  echo "Starting BibleMate (${APP_SCRIPT}) on port ${APP_PORT}..."
  nohup "${PYTHON_BIN}" "${WORKSPACE_DIR}/${APP_SCRIPT}" >> "${LOG_FILE}" 2>&1 &
  echo "Service started in background (PID: $!). Logs: ${LOG_FILE}"
}

# Check if the port is already listening
if ! ss -H -ltn "sport = :${APP_PORT}" 2>/dev/null | grep -q .; then
  start_biblemate
else
  echo "BibleMate (${APP_SCRIPT}) is already active on port ${APP_PORT}."
fi
```

### Port Reference

| Platform | Script | Port | Env Override |
| :--- | :--- | :--- | :--- |
| **Antigravity CLI** | `web_app_agy.py` | `33380` | `BIBLEMATE_AGY_PORT` |
| **Claude Code** | `web_app_claude.py` | `33379` | `BIBLEMATE_CLAUDE_PORT` |
| **Grok Build** | `web_app_grok.py` | `33378` | `BIBLEMATE_GROK_PORT` |
| **Google Antigravity SDK** | `web_app_gemini_api_key.py` | `33377` | *(fixed)* |

---

## 3. Managing Background Services

You can define quick alias functions in `~/.bashrc` to control and monitor the application:

```bash
# Check if BibleMate port is listening
alias bm-status="ss -tulpn | grep -E '33377|33378|33379|33380'"

# Follow live server logs
alias bm-logs="tail -f /tmp/biblemate-*.log"

# Stop all running BibleMate web app instances
stop_biblemate() {
  pkill -f "web_app_(claude|agy|grok|gemini_api_key)\.py" && echo "BibleMate services stopped." || echo "No BibleMate services found."
}
```

### Checking Service Status

To verify that the service is running and listening:

```bash
ss -H -ltn 'sport = :33379'
# or:
lsof -i :33379
```

### Viewing Live Logs

To inspect stdout/stderr or debug agent errors:

```bash
tail -f /tmp/biblemate-claude-33379.log
```

### Stopping the Server

```bash
# Terminate by process name:
pkill -f "web_app_claude.py"

# Or terminate by port:
fuser -k 33379/tcp
```

---

## 4. Alternative: Systemd Service (Persistent Daemons)

For dedicated Linux servers or virtual machines with `systemd` enabled, creating a service unit is cleaner and runs independently of user login sessions.

Create `/etc/systemd/system/biblemate-claude.service`:

```ini
[Unit]
Description=BibleMate Claude Code Web App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/workspace/biblemate_studies
ExecStart=/workspace/ai/bin/python3 /workspace/biblemate_studies/web_app_claude.py
Restart=always
RestartSec=5
StandardOutput=append:/tmp/biblemate-claude.log
StandardError=append:/tmp/biblemate-claude.log
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
systemctl daemon-reload
systemctl enable --now biblemate-claude.service
systemctl status biblemate-claude.service
```

---

## 5. Troubleshooting & Best Practices

1. **Port Already in Use (`Errno 98: Address already in use`)**:
   - Verify existing processes with `lsof -i :<PORT>` or `ss -tulpn | grep :<PORT>`.
   - Terminate old processes with `pkill -f "web_app_claude.py"` before restarting.

2. **Module Not Found (`No module named 'nicegui'`)**:
   - Ensure you are calling the Python executable inside the virtual environment (`/workspace/ai/bin/python3`) rather than the bare system `/usr/bin/python3`.

3. **Missing Local Scripture Databases**:
   - If verse retrieval fails with missing SQLite files, activate the venv and run `biblematedata` once to download the required datasets into `~/biblemate/data`.

4. **CLI Authentication Inside Headless Environments**:
   - **For Claude Code (`web_app_claude.py`)**: Run `claude --version` and ensure you are logged into Claude.
   - **For Grok Build (`web_app_grok.py`)**: Run `grok login` once so that `~/.grok/auth.json` is populated.
   - **For Antigravity CLI (`web_app_agy.py`)**: Run `agy auth login` or verify `agy models`.