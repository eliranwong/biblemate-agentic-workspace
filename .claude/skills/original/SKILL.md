---
name: original
description: Retrieve the original language text of a given Bible verse in Greek or Hebrew (OHGB version).
---

# Original Language Scripture Retrieval Skill

## Overview
This standalone skill enables any agent to retrieve the original language (Greek or Hebrew) text of a given Bible verse by leveraging the local `OHGB` (Open Hebrew Greek Bible) database.

## Guidelines & Objectives
When executing this skill:
- Always run the python retriever script located at `.claude/skills/original/original_retriever.py`.
- Execute the script using: `python3 .claude/skills/original/original_retriever.py "<query>"` where `<query>` is the user input or scripture reference.
- Present the exact output of the script to the user without altering the original language text or transliterations.
