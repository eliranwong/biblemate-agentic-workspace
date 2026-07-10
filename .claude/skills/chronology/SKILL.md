---
name: chronology
description: Expound biblical chronology using local datasets and academic-historical knowledge.
---

# Chronology Skill

## Overview
This standalone skill enables any agent to search and expound biblical, royal, and apostolic timelines. It queries a set of local chronology text files to locate matching records, and complements those findings with historical-grammatical scholarship.

## Guidelines & Objectives
When executing this skill:
- Always run the python script located at `.claude/skills/chronology/chronology_query.py` to search the local timeline databases.
- Execute the script using: `python3 .claude/skills/chronology/chronology_query.py "<query>"` where `<query>` is the input prompt, a specific year, name, or event.
- If relevant matching records are found in the local text files, display them with clear headings referencing their source file.
- If the requested chronological information is not found in the dataset, or is incomplete, use your own extensive biblical and historical knowledge to answer, clearly stating that the explanation is augmented by general academic/scholarly knowledge.
