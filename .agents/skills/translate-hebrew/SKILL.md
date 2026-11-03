---
name: translate-hebrew
description: Translate, transliterate, and provide word-by-word mapping of a Hebrew bible verse. Use when the user runs /translate-hebrew or requests this BibleMate workflow.
---

# Translate Hebrew Skill

## Persona
Adopt the **Biblical Translator** persona from `.agents/agents.md`.

## Overview
This standalone skill enables any agent to perform a high-quality translate hebrew study for a given Bible reference, text, or topic.

## Guidelines & Objectives
When executing this skill:
- Keep explanations biblically accurate and structurally clear.
- Cite specific book, chapter, and verse references for all statements.
- Ensure that the output is comprehensive, addressing all prompt criteria without skipping sections.
- Focus strictly on the requirements of this specific study type.

## Instructions
Translate, transliterate, and analyze a biblical verse:
1. **Transliteration**: Standard academic transliteration of the Hebrew/Greek text.
2. **Literal Contextual Translation**: Poetic, accurate, and elevated translation based on literary context.
3. **Word-by-Word Mapping**: Formatting in pattern: `word | transliteration | meaning`.
4. **Morphological and Syntactical Insights**: Analysis of key verbs, grammar, or structures that impact meaning.

## Formatting & Direct Translation Guidelines
- Translate directly from the Hebrew text provided rather than copying an existing English translation.
- Use `"Transliteration:"`, `"Translation:"`, and `"Mapping:"` as the section titles.
- Format each entry in the mapping section as: `word | transliteration | corresponding translation`.
- When requested as a direct translation without grammatical commentary, do not include parsing codes, extra explanation, or repeat the verse reference.
