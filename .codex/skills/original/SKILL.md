---
name: original
description: Retrieve the original language text of a given Bible verse in Greek or Hebrew (OHGB version). Use when the user runs /original or requests this BibleMate workflow.
---

# Original Language Scripture Retrieval Skill

## Overview
This standalone skill enables any agent to retrieve the original language (Greek or Hebrew) text of a given Bible verse by leveraging the local `OHGB` (Open Hebrew Greek Bible) database.

## Guidelines & Objectives
When executing this skill:
- Always run the python retriever script located at `.codex/skills/original/original_retriever.py`.
- Execute the script using: `python3 .codex/skills/original/original_retriever.py "<query>"` where `<query>` is the user input or scripture reference.
- Present the exact output of the script to the user without altering the original language text or transliterations.

## Codex Runtime Notes

- Use this `.codex/skills/original/` copy as the active skill. Do not invoke
  sibling skills from `.agents/`, `.claude/`, `.grok/`, or `.cursor/`.
- Run helper scripts with `exec_command` from the repository root, using the
  `.codex/skills/...` paths named above.
- Use `apply_patch` when creating or editing repository files; use shell
  commands only for execution, inspection, validation, and generated helper
  output.
