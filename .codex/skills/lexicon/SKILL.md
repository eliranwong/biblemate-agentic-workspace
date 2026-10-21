---
name: lexicon
description: Retrieve and compare definitions for Strong's numbers or original language keys from local lexicon databases. Use when the user runs /lexicon or requests this BibleMate workflow.
---

# Bible Lexicon Retrieval Skill

## Overview
This standalone skill enables any agent to retrieve and compare definitions for Strong's numbers (e.g. H148, G2479) or other lexicon keys directly from local SQLite databases stored in `~/biblemate/data/lexicons` or `~/biblemate/data_custom/lexicons`.

## Guidelines & Objectives
When executing this skill:
- Always run the python retriever script located at `.codex/skills/lexicon/lexicon_retriever.py` to retrieve the requested entries.
- Execute the script using: `python3 .codex/skills/lexicon/lexicon_retriever.py "<query>"` where `<query>` is the input prompt or arguments.
- Pass the user's version and entries query exactly as given to the script.
- Present the exact output of the script to the user without summarizing, paraphrasing, or altering the definition text, maintaining absolute accuracy.

## Codex Runtime Notes

- Use this `.codex/skills/lexicon/` copy as the active skill. Do not invoke
  sibling skills from `.agents/`, `.claude/`, `.grok/`, or `.cursor/`.
- Run helper scripts with `exec_command` from the repository root, using the
  `.codex/skills/...` paths named above.
- Use `apply_patch` when creating or editing repository files; use shell
  commands only for execution, inspection, validation, and generated helper
  output.
