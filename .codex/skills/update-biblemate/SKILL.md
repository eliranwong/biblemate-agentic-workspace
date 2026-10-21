---
name: update-biblemate
description: Refresh the BibleMate Codex skills by regenerating .codex from this repository's maintained skill sources. Use when the user runs /update-biblemate or asks to regenerate the .codex skills.
---

# Update BibleMate Skill (Codex)

## Overview
This skill refreshes the Codex BibleMate skills in `.codex/`. Content comes from
this repository's maintained skill source tree, then the generator rewrites
paths and tool names so the copies run in Codex.

## Guidelines & Objectives
1. Verify the workspace is this BibleMate repository.
2. Regenerate `.codex`:
   ```bash
   python3 .codex/build_codex.py
   ```
3. Report whether regeneration succeeded, how many skills were written, and
   whether the audit was clean.

## Codex Runtime Notes

- Do not modify `.agents/`, `.claude/`, `.grok/`, or `.cursor/` while refreshing
  the Codex tree.
- Use `exec_command` for the generator and validation commands.
