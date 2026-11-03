# Troubleshooting: Antigravity Slash Command (`/`) Autocomplete for `.agents/skills`

**Written:** 2026-11-03  
**Applies to:** Google Antigravity IDE, Antigravity 2.0 desktop app, and Antigravity CLI (`agy`).

---

## TL;DR — The Quick Fix

If typing `/` in the chat input box shows **no autocompletion list** or does not list workspace skills under `.agents/skills/`:

1. **Update to the Latest Antigravity Version**: Older versions of Antigravity only parsed `.agents/workflows/` and lacked native support for discovering `SKILL.md` files as slash commands. Ensure your Antigravity IDE / CLI is up to date.
2. **Re-select your Model after Upgrading**: Upgrading Antigravity frequently resets the active model preference in session storage to `None` on the very first conversation opened. Check the bottom toolbar and explicitly select a model (e.g., `Gemini 4 Argon (Medium)` or `Gemini 3.8 Flash (Medium)`).
3. **Send a first message or switch models to initialize the conversation trajectory**: On brand new, unsaved conversations with no active model selected, the language server cannot resolve the cascade configuration and fails to return slash commands. Switching the model or starting the session immediately resolves it.
4. **Do NOT recreate `.agents/workflows/`**: Workflows have been deprecated in modern Antigravity in favor of `.agents/skills/<name>/SKILL.md`. Antigravity's internal language server now surfaces skills directly via `GetSlashCommands` as `SLASH_COMMAND_TYPE_SKILL`.

---

## Symptoms

- You type `/` into the chat input box, but no autocomplete menu appears, or it only displays a few default commands (or nothing at all).
- The agent is still able to run skills if prompted or if you type the full command `/price NVDA today`, but the UI dropdown does not suggest your workspace skills from `.agents/skills/`.
- The issue often happens right after launching a new chat session or after migrating legacy workflows from `.agents/workflows/` to `.agents/skills/`.

---

## Technical Root Cause Analysis

### 1. Architectural Shift: Workflows Deprecated in Favor of Skills

In earlier versions of Antigravity:
- Slash commands were populated from `.agents/workflows/*.md` (and `~/.gemini/config/global_workflows/*.md`) via the `getAllWorkflows` RPC.
- This was a purely static file listing that did not depend on an active model or conversation state.

In modern Antigravity:
- Workflows are deprecated and migrated to modular skills (`.agents/skills/<name>/SKILL.md`).
- Slash command autocomplete combines three internal RPC endpoints in the IDE workbench (`workbench.desktop.main.js`):
  1. `getAllWorkflows` (legacy fallback; returns empty once workflows are migrated).
  2. `listMcpPrompts` (prompts exposed by MCP servers).
  3. **`getSlashCommands`** (provides both built-in commands like `/plan`, `/goal`, `/schedule` and **all workspace skills** discovered from `.agents/skills/` as `SLASH_COMMAND_TYPE_SKILL`).

### 2. The Failure Mode: Unresolved Cascade Config / Unspecified Model

Unlike simple file scanners, the language server's `GetSlashCommands` RPC resolves the conversation's **cascade configuration** (which binds the selected model, workspace URIs, and trajectory ID).

#### Why Was the Model Set to `None`?
When you install an update or upgrade Antigravity (which touches `.ide_migration` and refreshes available model tiers via `fetchAvailableModels`), the IDE's session storage and active model selection state are often reset or unassigned for new conversations. On the very first conversation opened immediately following an upgrade, the active model selector defaults to **`None`** (unselected) until you manually choose one.

If a new conversation is started where:
- The trajectory file has not yet been saved to disk (brand-new turn), **AND**
- The **Model Selection** is uninitialized, unset, or set to `None`:

The language server fails with errors such as:

```text
E1103 20:16:11.955668 /exa.language_server_pb.LanguageServerService/GetSlashCommands (unknown):
failed to resolve cascade config: failed to ensure trajectory loaded:
failed to load trajectory <CONVERSATION_ID> on-demand:
trajectory <CONVERSATION_ID> not found in any store: file does not exist
```

Or when called without an active model:

```json
{
  "code": "unknown",
  "message": "failed to resolve cascade config: plan model not specified; you must specify a valid model"
}
```

Because `GetSlashCommands` errors out silently in the background, the UI autocomplete hook receives an empty list and displays nothing when typing `/`.

### 3. Version Compatibility: Older vs Modern Antigravity

- **Legacy Antigravity versions** only supported `.agents/workflows/*.md`. If you run modern `.agents/skills/<name>/SKILL.md` structures on an older release, the slash command menu will not recognize them because older language servers only executed `getAllWorkflows`.
- **Modern Antigravity versions** introduce native support for progressive disclosure and slash command indexing directly from `skills/<name>/SKILL.md` via `GetSlashCommands` (`SLASH_COMMAND_TYPE_SKILL`).
- Always update Antigravity (via the built-in updater, package manager, or downloading the latest build) so that the application knows how to index modern `SKILL.md` files.

---

## Diagnostic Playbook

If `/` autocomplete stops showing your skills, follow these diagnosis steps:

### 1. Check Model Selection in the UI
Look at the bottom toolbar of the Antigravity chat panel:
- Is a model actively chosen?
- If it displays `None`, click the selector and choose an active model.
- If a model is already selected, click the dropdown and switch to another model, then switch back. This forces the UI to re-trigger `GetSlashCommands`.

### 2. Inspect the Language Server Daemon Log
Check the Antigravity CLI/daemon log for RPC errors:

```bash
tail -n 50 ~/.gemini/antigravity/cli.log
```

Look for lines mentioning `GetSlashCommands` or `failed to resolve cascade config`. If present, this confirms that the autocomplete endpoint failed due to an uninitialized conversation or model state.

### 3. Verify Local Language Server Health
You can verify that the language server itself can discover your skills by testing the `GetSlashCommands` endpoint locally:

```bash
# Get the active HTTP port and CSRF token from the daemon discovery file
PORT=$(jq -r .httpPort ~/.gemini/antigravity/daemon/hub_*.json 2>/dev/null | head -n 1)
TOKEN=$(jq -r .csrfToken ~/.gemini/antigravity/daemon/hub_*.json 2>/dev/null | head -n 1)

# Query GetSlashCommands
curl -sk -X POST https://localhost:$PORT/exa.language_server_pb.LanguageServerService/GetSlashCommands \
  -H "Content-Type: application/json" \
  -H "x-codeium-csrf-token: $TOKEN" \
  -d '{"workspaceUris": ["file://'"$PWD"'"]}' | jq '.commands[] | select(.info.type=="SLASH_COMMAND_TYPE_SKILL") | .title'
```

If skills appear in the output, the skill files and scanner are healthy.

---

## Frontmatter Formatting Rules for `.agents/skills`

For a skill to be indexed and presented properly in the `/` command menu:

1. **Path structure**: Each skill must live in `.agents/skills/<skill-name>/SKILL.md`.
2. **Valid `name` attribute**:
   - Must be **lowercase and hyphenated** (e.g., `name: base-breakout-scanner`).
   - Do **NOT** use spaces, title casing, or underscores in the `name:` field (e.g., avoid `name: Base Breakout Scanner`), as this can break slash-command slug parsing.
3. **Valid `description` attribute**:
   - Provide a clear, concise third-person description so both the UI menu and autonomous invocation know when to trigger the skill.

Example:

```markdown
---
name: base-breakout-scanner
description: Scan for stocks breaking out of technical chart patterns.
---

# Base Breakout Scanner
...
```

---

## Summary Checklist

- [x] Ensure you are running the **latest Antigravity version** with native skill-to-slash-command support.
- [x] Select a valid model in the Antigravity chat panel.
- [x] If autocomplete is blank on a brand-new tab, switch models once or send a message to initialize the conversation trajectory.
- [x] Verify `.agents/skills/<name>/SKILL.md` uses valid lowercase-hyphenated names.
- [x] Keep `.agents/workflows/` deleted—Antigravity natively uses `.agents/skills/`.

