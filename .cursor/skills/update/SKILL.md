---
name: update
description: Refresh the BibleMate Cursor skills by regenerating .cursor from the Grok sources in this repository. Use when the user runs /update or asks to regenerate the .cursor skills.
---

# Update Skill (Cursor)

## Overview
This skill refreshes the Cursor BibleMate skills in `.cursor/`. Content comes
from `.grok/skills/` (itself generated from `.claude/`). The generator rewrites
paths and tool names so the copies run in Cursor.

## Guidelines & Objectives
1. **Verify Operating System**: Only supported on macOS or Linux.
2. **Verify Workspace Folder**: Confirm with the user before a refresh inside a
   workspace named `antigravity-biblemate-workspace`.
3. **Refresh upstream trees when they are missing or stale**:
   ```bash
   python3 .claude/build_claude.py
   python3 .grok/build_grok.py
   ```
   Optional remote download, only when the user wants a fresh upstream bundle:
   ```bash
   python3 .cursor/skills/update/updater.py
   ```
4. **Regenerate `.cursor`**:
   ```bash
   python3 .cursor/build_cursor.py
   ```
5. **Report Status**: Say whether regeneration succeeded, how many skills were
   written, and confirm `.cursor/rules/biblemate-skills.mdc` is present.
