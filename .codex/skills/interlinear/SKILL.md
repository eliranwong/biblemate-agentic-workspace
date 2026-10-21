---
name: interlinear
description: Retrieve the interlinear version of a given Bible verse in Greek or Hebrew (OHGBi version). Use when the user runs /interlinear or requests this BibleMate workflow.
---

# Interlinear Language Scripture Retrieval Skill

## Overview
This standalone skill enables any agent to retrieve the interlinear version of a given Bible verse in Greek or Hebrew by leveraging the local `OHGBi` (Open Hebrew Greek Bible Interlinear) database.

## Guidelines & Objectives
When executing this skill:
- Always run the python retriever script located at `.codex/skills/interlinear/interlinear_retriever.py`.
- Execute the script using: `python3 .codex/skills/interlinear/interlinear_retriever.py "<query>"` where `<query>` is the user input or scripture reference.
- Present the exact output of the script to the user, maintaining the interlinear formatting (morphemes and word-by-word glosses).

## Codex Runtime Notes

- Use this `.codex/skills/interlinear/` copy as the active skill. Do not invoke
  sibling skills from `.agents/`, `.claude/`, `.grok/`, or `.cursor/`.
- Run helper scripts with `exec_command` from the repository root, using the
  `.codex/skills/...` paths named above.
- Use `apply_patch` when creating or editing repository files; use shell
  commands only for execution, inspection, validation, and generated helper
  output.
