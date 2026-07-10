---
name: xrefs
description: Retrieve bible cross-references from the local SQLite databases based on versions and references.
---

# Bible Cross-References Skill

## Overview
This standalone skill enables any agent to retrieve and compare Bible cross-references directly from the local SQLite database stored in `~/biblemate/data/cross-reference.sqlite` and fetch their content using the `bible` skill.

## Guidelines & Objectives
When executing this skill:
- Always run the python retriever script located at `.claude/skills/xrefs/xrefs_retriever.py` to retrieve the requested cross-references.
- Execute the script using: `python3 .claude/skills/xrefs/xrefs_retriever.py "<query>"` where `<query>` is the input prompt or arguments.
- Pass the user's version and reference query exactly as given to the script.
- Present the exact output of the script to the user without summarizing, paraphrasing, or altering the text, maintaining the absolute authority and accuracy of God's Word.
