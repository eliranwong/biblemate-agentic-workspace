---
name: bible
description: Retrieve bible verses from the local SQLite databases based on versions and references. Use when the user runs /bible or requests this BibleMate workflow.
---

# Bible Retrieval Skill

## Overview
This standalone skill enables any agent to retrieve and compare Bible verses directly from the local SQLite databases stored in `~/biblemate/data/bibles` or `~/biblemate/data_custom/bibles`.

## Guidelines & Objectives
When executing this skill:
- Always run the python retriever script located at `.codex/skills/bible/bible_retriever.py` to retrieve the requested verses.
- Execute the script using: `python3 .codex/skills/bible/bible_retriever.py "<query>"` where `<query>` is the input prompt or arguments.
- Pass the user's version and reference query exactly as given to the script.
- Present the exact output of the script to the user without summarizing, paraphrasing, or altering the biblical text, maintaining the absolute authority and accuracy of God's Word.

## Codex Runtime Notes

- Use this `.codex/skills/bible/` copy as the active skill. Do not invoke
  sibling skills from `.agents/`, `.claude/`, `.grok/`, or `.cursor/`.
- Run helper scripts with `exec_command` from the repository root, using the
  `.codex/skills/...` paths named above.
- Use `apply_patch` when creating or editing repository files; use shell
  commands only for execution, inspection, validation, and generated helper
  output.
