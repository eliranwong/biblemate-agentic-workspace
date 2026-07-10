---
name: update
description: Refresh the BibleMate Claude Code ecosystem by re-running the local generator against the latest .agents/preferences source.
---

# Update Skill (Claude Code)

## Overview
This skill refreshes the self-contained `.claude` BibleMate ecosystem for Claude
Code. It (1) downloads the latest `manual_setup.zip` bundle (which ships the
`.agents/` personas/skills/workflows and `preferences/`), (2) extracts it into
the workspace, and (3) regenerates `.claude/` by running the local generator
`python3 .claude/build_claude.py`.

Everything this skill needs lives inside `.claude/` (the generator) plus the
remote bundle; it does not depend on any other local files outside `.claude/`.

## Guidelines & Objectives
1. **Verify Operating System**: Only supported on macOS or Linux.
2. **Verify Workspace Folder**: The updater refuses to run inside a workspace
   named `antigravity-biblemate-workspace` (the source repository) to avoid
   overwriting source files. Run it in your own copy/fork instead.
3. **Download & Extract**: Run the updater helper:
   ```bash
   python3 .claude/skills/update/updater.py
   ```
   This fetches `manual_setup.zip` and extracts `.agents/` and `preferences/`
   into the workspace root.
4. **Regenerate `.claude`**: Rebuild the Claude Code ecosystem from the freshly
   extracted source:
   ```bash
   python3 .claude/build_claude.py
   ```
5. **Report Status**: Summarise whether the download, extraction, and rebuild
   succeeded, and list the number of skills/commands/agents regenerated.
