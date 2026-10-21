---
name: perspective
description: Interpret contemporary topics, news, or articles through a biblical worldview and gospel lens. Use when the user runs /perspective or requests this BibleMate workflow.
---

# Perspective Skill

## Overview
This standalone skill enables any agent to perform a high-quality perspective study for a given Bible reference, text, or topic.

## Guidelines & Objectives
When executing this skill:
- Keep explanations biblically accurate and structurally clear.
- Cite specific book, chapter, and verse references for all statements.
- Ensure that the output is comprehensive, addressing all prompt criteria without skipping sections.
- Focus strictly on the requirements of this specific study type.

## Instructions
Interpret contemporary content (articles, ideologies, quotes, culture) through a biblical worldview and gospel lens:
1. **Ideological Analysis**: Deconstruct the core assumptions, values, and worldviews present in the user's content.
2. **Biblical Contrast**: Contrast these secular concepts with foundational biblical truths (e.g., God's creation design, the reality of sin).
3. **Gospel Integration**: Weave in the message of salvation through Jesus Christ as the final answer and hope for the issue.

## Codex Runtime Notes

- Use this `.codex/skills/perspective/` copy as the active skill. Do not invoke
  sibling skills from `.agents/`, `.claude/`, `.grok/`, or `.cursor/`.
- Run helper scripts with `exec_command` from the repository root, using the
  `.codex/skills/...` paths named above.
- Use `apply_patch` when creating or editing repository files; use shell
  commands only for execution, inspection, validation, and generated helper
  output.
