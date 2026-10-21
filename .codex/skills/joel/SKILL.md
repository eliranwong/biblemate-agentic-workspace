---
name: joel
description: Search for given words or phrases in the book of Joel in one or multiple bibles, with wildcards (*, ?) and logical combinations (+, |) supported. Use when the user runs /Joel or requests this BibleMate workflow.
---

# Bible Search Skill - Joel

## Overview
This standalone skill enables any agent to search for words or phrases inside the book of Joel in local SQLite Bible databases stored in `~/biblemate/data/bibles` or `~/biblemate/data_custom/bibles`.

## Guidelines & Objectives
When executing this skill:
- Always run the python retriever script located at `.codex/skills/search/search_retriever.py` with the `--book Joel` option to perform the search.
- Execute the script using: `python3 .codex/skills/search/search_retriever.py --book Joel "<query>"` where `<query>` is the input prompt or arguments.
- Pass the user's version and search query exactly as given to the script.
- Present the exact output of the script to the user without summarizing, paraphrasing, or altering the text, maintaining the absolute authority and accuracy of God's Word.

## Codex Runtime Notes

- Use this `.codex/skills/joel/` copy as the active skill. Do not invoke
  sibling skills from `.agents/`, `.claude/`, `.grok/`, or `.cursor/`.
- Run helper scripts with `exec_command` from the repository root, using the
  `.codex/skills/...` paths named above.
- Use `apply_patch` when creating or editing repository files; use shell
  commands only for execution, inspection, validation, and generated helper
  output.
