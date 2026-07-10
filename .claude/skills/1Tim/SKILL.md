---
name: 1Tim
description: Search for given words or phrases in the book of 1 Timothy in one or multiple bibles, with wildcards (*, ?) and logical combinations (+, |) supported.
---

# Bible Search Skill - 1 Timothy

## Overview
This standalone skill enables any agent to search for words or phrases inside the book of 1 Timothy in local SQLite Bible databases stored in `~/biblemate/data/bibles` or `~/biblemate/data_custom/bibles`.

## Guidelines & Objectives
When executing this skill:
- Always run the python retriever script located at `.claude/skills/search/search_retriever.py` with the `--book 1Tim` option to perform the search.
- Execute the script using: `python3 .claude/skills/search/search_retriever.py --book 1Tim "<query>"` where `<query>` is the input prompt or arguments.
- Pass the user's version and search query exactly as given to the script.
- Present the exact output of the script to the user without summarizing, paraphrasing, or altering the text, maintaining the absolute authority and accuracy of God's Word.
