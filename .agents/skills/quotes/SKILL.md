---
name: quotes
description: Find and quote multiple relevant bible verses on a specific topic or query. Use when the user runs /quotes or requests this BibleMate workflow.
---

# Quotes Skill

## Persona
Adopt the **Verse Scripter** persona from `.agents/agents.md`.

## Overview
This standalone skill enables any agent to perform a high-quality quotes study for a given Bible reference, text, or topic.

## Guidelines & Objectives
When executing this skill:
- Keep explanations biblically accurate and structurally clear.
- Cite specific book, chapter, and verse references for all statements.
- Ensure that the output is comprehensive, addressing all prompt criteria without skipping sections.
- Focus strictly on the requirements of this specific study type.

## Instructions
Find and quote multiple relevant bible verses on a specific topic or query:
1. **Scripture Quoting**: Provide the full text of verses across Old and New Testaments.
2. **Connection Notes**: Explain briefly how each quoted verse contributes to the overall biblical theology of the topic.
- Quote relevant Bible passages (retrieved via the `bible` skill) in relation to the given content and explain how each passage relates to it.
