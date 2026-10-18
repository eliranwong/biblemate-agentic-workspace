---
name: original
description: Retrieve the original language text of a given Bible verse in Greek or Hebrew (OHGB version). Use when the user runs /original or requests this BibleMate workflow.
---

# Original Language Scripture Retrieval Skill

## Overview
This standalone skill enables any agent to retrieve the original language (Greek or Hebrew) text of a given Bible verse by leveraging the local `OHGB` (Open Hebrew Greek Bible) database.

## Guidelines & Objectives
When executing this skill:
- Always run the python retriever script located at `.cursor/skills/original/original_retriever.py`.
- Execute the script using: `python3 .cursor/skills/original/original_retriever.py "<query>"` where `<query>` is the user input or scripture reference.
- Present the exact output of the script to the user without altering the original language text or transliterations.
