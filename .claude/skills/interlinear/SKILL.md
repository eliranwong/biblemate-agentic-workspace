---
name: interlinear
description: Retrieve the interlinear version of a given Bible verse in Greek or Hebrew (OHGBi version).
---

# Interlinear Language Scripture Retrieval Skill

## Overview
This standalone skill enables any agent to retrieve the interlinear version of a given Bible verse in Greek or Hebrew by leveraging the local `OHGBi` (Open Hebrew Greek Bible Interlinear) database.

## Guidelines & Objectives
When executing this skill:
- Always run the python retriever script located at `.claude/skills/interlinear/interlinear_retriever.py`.
- Execute the script using: `python3 .claude/skills/interlinear/interlinear_retriever.py "<query>"` where `<query>` is the user input or scripture reference.
- Present the exact output of the script to the user, maintaining the interlinear formatting (morphemes and word-by-word glosses).
