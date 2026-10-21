---
name: morphology
description: Retrieve bible morphology data from the local morphology database for verse references or specific word/phrase queries. Use when the user runs /morphology or requests this BibleMate workflow.
---

# Bible Morphology Retrieval Skill

## Overview
This standalone skill enables any agent to retrieve word-by-word morphology details from the local SQLite database `~/biblemate/data/morphology.sqlite`.

## Guidelines & Objectives
When executing this skill:
- Always run the python retriever script located at `.codex/skills/morphology/morphology_retriever.py`.
- Execute the script using: `python3 .codex/skills/morphology/morphology_retriever.py "<query>"` where `<query>` is the user input.
- Present the exact output of the script to the user, maintaining formatting.

## Codex Runtime Notes

- Use this `.codex/skills/morphology/` copy as the active skill. Do not invoke
  sibling skills from `.agents/`, `.claude/`, `.grok/`, or `.cursor/`.
- Run helper scripts with `exec_command` from the repository root, using the
  `.codex/skills/...` paths named above.
- Use `apply_patch` when creating or editing repository files; use shell
  commands only for execution, inspection, validation, and generated helper
  output.
