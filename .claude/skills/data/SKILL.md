---
name: data
description: List available resource versions (bibles, commentaries, lexicons) by scanning the respective folders dynamically.
---

# List Available Resources Skill

## Overview
This standalone skill enables any agent to dynamically check and list available versions of Bibles, commentaries, and lexicons stored in the standard (`~/biblemate/data/...`) and custom (`~/biblemate/data_custom/...`) directories.

## Guidelines & Objectives
When executing this skill:
- Always run the python lister script located at `.claude/skills/data/data_lister.py`.
- Execute the script using: `python3 .claude/skills/data/data_lister.py "<resource_type>"` where `<resource_type>` is `bible`, `commentary`, or `lexicon`.
- Present the exact output of the script to the user, maintaining clean markdown and directory context.
