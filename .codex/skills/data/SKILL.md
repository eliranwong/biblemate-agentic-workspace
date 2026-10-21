---
name: data
description: List available resource versions (bibles, commentaries, lexicons) by scanning the respective folders dynamically. Use when the user runs /data or requests this BibleMate workflow.
---

# List Available Resources Skill

## Overview
This standalone skill enables any agent to dynamically check and list available versions of Bibles, commentaries, and lexicons stored in the standard (`~/biblemate/data/...`) and custom (`~/biblemate/data_custom/...`) directories.

## Guidelines & Objectives
When executing this skill:
- Always run the python lister script located at `.codex/skills/data/data_lister.py`.
- Execute the script using: `python3 .codex/skills/data/data_lister.py "<resource_type>"` where `<resource_type>` is `bible`, `commentary`, or `lexicon`.
- Present the exact output of the script to the user, maintaining clean markdown and directory context.

## Codex Runtime Notes

- Use this `.codex/skills/data/` copy as the active skill. Do not invoke
  sibling skills from `.agents/`, `.claude/`, `.grok/`, or `.cursor/`.
- Run helper scripts with `exec_command` from the repository root, using the
  `.codex/skills/...` paths named above.
- Use `apply_patch` when creating or editing repository files; use shell
  commands only for execution, inspection, validation, and generated helper
  output.
