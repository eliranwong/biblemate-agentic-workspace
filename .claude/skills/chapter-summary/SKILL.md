---
name: chapter-summary
description: Generate a detailed summary, structure, and theological interpretation of a bible chapter.
---

# Chapter Summary Skill

## Overview
This standalone skill enables any agent to perform a high-quality chapter summary study for a given Bible reference, text, or topic.

## Guidelines & Objectives
When executing this skill:
- Always run the python script located at `.claude/skills/chapter-summary/chapter_summary_retriever.py` to search the local database for baseline chapter summaries.
- Execute the script using: `python3 .claude/skills/chapter-summary/chapter_summary_retriever.py "<Book> <Chapter>"` (you can also pass language options like `--sc` or `--tc` if a Chinese translation is preferred, or the script will auto-detect Chinese characters).
- Retrieve and use the local database output as the baseline information. Combine it with your assigned persona, theological perspective, and relevant Scripture references to fully expound the chapter in detail.
- Keep explanations biblically accurate and structurally clear.
- Cite specific book, chapter, and verse references for all statements.
- Ensure that the output is comprehensive, addressing all prompt criteria without skipping sections.
- Focus strictly on the requirements of this specific study type.

## Instructions
Write a detailed, scholarly interpretation on a bible chapter. Provide a structured and comprehensive analysis using these sections:
1. **Overview & Context**: Setting the chapter's historical, cultural, and literary location in the book. Expand upon the retrieved baseline summary's overview.
2. **Structural Outline**: Detailed division of the chapter into passages, highlighting logical progression and chiasms. Elaborate on the structural outline retrieved from the database.
3. **Thematic Exegesis**: In-depth analysis of major theological themes, quoting key words or phrases from the original text (or standard English/Chinese versions). Deepen the themes retrieved from the database.
4. **Comparative Interpretations**: How major historical and contemporary scholars or theologians have interpreted key debates within this chapter.
5. **Canonical & Covenantal Links**: Connecting this chapter to the broader redemptive storyline of Scripture.
6. **Pastoral & Practical Application**: Life applications grounded in the chapter's theological message.

