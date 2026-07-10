---
name: commentary
description: Retrieve bible commentaries from the local SQLite databases based on versions and references.
---

# Bible Commentary Skill

## Overview
This standalone skill enables any agent to retrieve and compare Bible commentaries directly from the local SQLite databases stored in `~/biblemate/data/commentaries` or `~/biblemate/data_custom/commentaries`.

## Guidelines & Objectives
When executing this skill:
- Always run the python retriever script located at `.claude/skills/commentary/commentary_retriever.py` to retrieve the requested commentaries.
- Execute the script using: `python3 .claude/skills/commentary/commentary_retriever.py "<query>"` where `<query>` is the input prompt or arguments.
- Pass the user's version and reference query exactly as given to the script.
- Present the exact output of the script to the user without summarizing, paraphrasing, or altering the text, so they can directly read the insights of the commentators.
