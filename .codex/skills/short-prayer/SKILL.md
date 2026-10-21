---
name: short-prayer
description: Draft a short, direct scriptural prayer (one paragraph) based on a passage. Use when the user runs /short-prayer or requests this BibleMate workflow.
---

# Short Prayer Skill

## Overview
This standalone skill enables any agent to perform a high-quality short prayer study for a given Bible reference, text, or topic.

## Guidelines & Objectives
When executing this skill:
- Keep explanations biblically accurate and structurally clear.
- Cite specific book, chapter, and verse references for all statements.
- Ensure that the output is comprehensive, addressing all prompt criteria without skipping sections.
- Focus strictly on the requirements of this specific study type.

## Instructions
Draft a short scriptural prayer based on a passage, focusing on a single paragraph:
1. Praise God for his attributes in the text.
2. Confess and petition for help to live in alignment with the scripture's truths.

## Codex Runtime Notes

- Use this `.codex/skills/short-prayer/` copy as the active skill. Do not invoke
  sibling skills from `.agents/`, `.claude/`, `.grok/`, or `.cursor/`.
- Run helper scripts with `exec_command` from the repository root, using the
  `.codex/skills/...` paths named above.
- Use `apply_patch` when creating or editing repository files; use shell
  commands only for execution, inspection, validation, and generated helper
  output.
