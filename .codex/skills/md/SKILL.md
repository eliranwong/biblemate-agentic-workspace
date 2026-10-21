---
name: md
description: Convert a specified file to markdown format, or export the last response/whole conversation to export/md.
---

# Markdown Conversion & Export Skill

## Overview
This standalone skill enables any agent to perform file markdown conversions or export conversation dialogue to the designated export directory.

## Guidelines & Objectives
When executing this skill:
- Always run the python converter script located at `.codex/skills/md/md_converter.py` to perform the conversion or export.
- Execute the script using: `python3 .codex/skills/md/md_converter.py "<query>"` where `<query>` is the input prompt or arguments containing the file path or export directives (e.g. `whole`, `conversation`).
- Present the exact output of the script to the user, confirming the paths and file status of the output.

## Codex Runtime Notes

- Use this `.codex/skills/md/` copy as the active skill. Do not invoke
  sibling skills from `.agents/`, `.claude/`, `.grok/`, or `.cursor/`.
- Run helper scripts with `exec_command` from the repository root, using the
  `.codex/skills/...` paths named above.
- Use `apply_patch` when creating or editing repository files; use shell
  commands only for execution, inspection, validation, and generated helper
  output.
