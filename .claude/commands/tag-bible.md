---
description: Tag a .bible file (Verses, Bible, and VersesPlain tables) with word IDs aligned to tagged_translations.sqlite.
---

Adopt the **Verse Scripter** persona from `.claude/agents.md`.

Use the **tag-bible** skill to tag the requested `.bible` file with word IDs and populate the corresponding column in `tagged_translations.sqlite`.

Read and follow `.claude/skills/tag-bible/SKILL.md` completely. Back up `tagged_translations.sqlite` before tagging, run the helper script with the appropriate case (helping materials, standalone, or `--transfer-from` sibling transfer), and complete the verification checklist (`0` text mismatches on `Verses` and `Bible`, `VersesPlain` row count and tag stripping, sample-verse inspection) before reporting completion.

# Input

$ARGUMENTS
