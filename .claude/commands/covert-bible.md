---
description: Convert Bible source files (USFM, OSIS, TSV, EPUB/HTML, or text) into the BibleMate AI SQLite .bible format.
---

Adopt the **Verse Scripter** persona from `.claude/agents.md`.

Use the **covert-bible** skill to convert the user-provided Bible source materials into a `.bible` SQLite database.

Read and follow `.claude/skills/covert-bible/SKILL.md` completely. Inspect all provided sources first, choose the best source(s), write and run a conversion script that produces the `Bible`, `Verses`, `Notes`, and `Details` tables with the required formatting, save the output as `biblemate_bibles/<ABBR>.bible`, and run the full verification checklist before reporting completion.

# Input

$ARGUMENTS
