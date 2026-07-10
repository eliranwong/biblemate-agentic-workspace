---
name: names
description: Retrieve and compare the meanings of names in the Bible.
---

# Names Skill

## Overview
This standalone skill enables any agent to search and expound the etymological and spiritual meanings of biblical names. It queries a local database of Bible names and their associated meanings, supporting spelling flexibility for misspelled queries.

## Guidelines & Objectives
When executing this skill:
- Always run the python script located at `.claude/skills/names/names_query.py` to search the local name definitions database.
- Execute the script using: `python3 .claude/skills/names/names_query.py "<query>"` where `<query>` is the name or search terms.
- If relevant matching records are found in the local database, display them clearly.
- If the requested name is not found in the dataset, or you wish to elaborate, use your own extensive linguistic and biblical knowledge (including Hebrew/Greek roots and historical significance) to answer, clearly stating that the information is augmented by general biblical-linguistic knowledge.
