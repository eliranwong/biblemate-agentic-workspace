---
name: names
description: Retrieve and compare the meanings of names in the Bible. Use when the user runs /names or requests this BibleMate workflow.
---

# Names Skill

## Overview
This standalone skill enables any agent to search and expound the etymological and spiritual meanings of biblical names. It queries a local database of Bible names and their associated meanings, supporting spelling flexibility for misspelled queries.

## Guidelines & Objectives
When executing this skill:
- Always run the python script located at `.codex/skills/names/names_query.py` to search the local name definitions database.
- Execute the script using: `python3 .codex/skills/names/names_query.py "<query>"` where `<query>` is the name or search terms.
- If relevant matching records are found in the local database, display them clearly.
- If the requested name is not found in the dataset, or you wish to elaborate, use your own extensive linguistic and biblical knowledge (including Hebrew/Greek roots and historical significance) to answer, clearly stating that the information is augmented by general biblical-linguistic knowledge.

## Codex Runtime Notes

- Use this `.codex/skills/names/` copy as the active skill. Do not invoke
  sibling skills from `.agents/`, `.claude/`, `.grok/`, or `.cursor/`.
- Run helper scripts with `exec_command` from the repository root, using the
  `.codex/skills/...` paths named above.
- Use `apply_patch` when creating or editing repository files; use shell
  commands only for execution, inspection, validation, and generated helper
  output.
