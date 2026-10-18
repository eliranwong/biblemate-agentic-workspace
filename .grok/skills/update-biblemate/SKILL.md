---
name: update-biblemate
description: Refresh the BibleMate Grok Build ecosystem by re-running the local generator against the latest Claude Code (or antigravity) source. Use when the user runs /update-biblemate or asks to regenerate the .grok ecosystem.
---

# Update BibleMate Skill (Grok Build)

## Overview
This skill refreshes the self-contained `.grok` BibleMate ecosystem for Grok
Build. Preferred path when `.claude/` is already present: regenerate directly
from Claude Code sources. Optional path: download the remote `manual_setup.zip`
bundle first (ships `.agents/` + `preferences/`), rebuild Claude via
`python3 .claude/build_claude.py` if available, then rebuild Grok.

Everything this skill needs for the Grok rebuild lives inside `.grok/` (this
generator) plus the `.claude/` tree as source.

## Guidelines & Objectives
1. **Verify Operating System**: Only supported on macOS or Linux.
2. **Verify Workspace Folder**: Prefer not to run destructive updates inside a
   workspace named `antigravity-biblemate-workspace` (the source repository)
   unless you intentionally maintain this repo. Confirm with the user first.
3. **Optional download & extract** (if `.claude/` is missing or stale and the
   user wants a remote refresh):
   ```bash
   python3 .grok/skills/update-biblemate/updater.py
   ```
   If the Claude updater exists, you may also run:
   ```bash
   python3 .claude/skills/update/updater.py
   python3 .claude/build_claude.py
   ```
4. **Regenerate `.grok`**: Rebuild the Grok Build ecosystem from `.claude/`:
   ```bash
   python3 .grok/build_grok.py
   ```
5. **Report Status**: Summarise whether regeneration succeeded, and list the
   number of skills/commands/agents/personas regenerated.
