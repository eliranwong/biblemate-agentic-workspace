---
description: Export a Bible from the SQLite Bible table into Markdown files organized by book sub-folders and chapter files.
---

Adopt the **Verse Scripter** persona from `.claude/agents.md`.

Use the **export-bible** skill to export the requested Bible version to Markdown.

Read and follow `.claude/skills/export-bible/SKILL.md`. Run the helper script with the user's requested Bible version name or abbreviation:

```bash
python3 .claude/skills/export-bible/export_bible.py "<version>"
```

If the requested version is ambiguous or not found, report the available versions listed by the script. Report the output directory path, number of books, and total chapter `.md` files exported.

# Input

$ARGUMENTS
