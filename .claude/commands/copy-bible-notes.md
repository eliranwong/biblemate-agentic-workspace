---
description: Copy the Notes table and inline note links in the Bible table from one .bible file to another.
---

Adopt the **Verse Scripter** persona from `.claude/agents.md`.

Use the **copy-bible-notes** skill to copy Bible notes and note links between `.bible` files.

Read and follow `.claude/skills/copy-bible-notes/SKILL.md`. Run the helper script with the source and target `.bible` files provided by the user:

```bash
python3 .claude/skills/copy-bible-notes/copy_bible_notes.py <source.bible> <target.bible>
```

Prefer a dry run first unless the user asks for an in-place copy. Report the verification results (Notes row count, inserted link count, text-mismatch count) before reporting completion.

# Input

$ARGUMENTS
