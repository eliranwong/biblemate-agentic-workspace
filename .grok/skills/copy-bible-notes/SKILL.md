---
name: copy-bible-notes
description: Copy the Notes table and inline <sup> note links in the Bible table from one SQLite .bible file to another .bible file (same translation or a similar translation, tagged or untagged). Use when the user runs /copy-bible-notes or asks to copy Bible notes and note links between .bible files.
---

# Copy Bible Notes Skill

## Overview
This skill copies the `Notes` table and all inline `<sup>...</sup>` note links (e.g. `<sup><ref onclick='bn(...)'>&oplus;</ref></sup>`) in the `Bible` table from a **source** `.bible` SQLite file to a **target** `.bible` SQLite file — whether they are the **same translation** or a **similar translation** (e.g. `CNET.bible` → `CUV.bible`, `NET.bible` → `NKJV.bible` / `ASV.bible`).

Helper script: `.grok/skills/copy-bible-notes/copy_bible_notes.py`

---

## How Inline Link Placement Works
For every note link in the source `Bible` table, the script locates the corresponding `(Book, Chapter, Verse)` slice in the target `Bible` table (via `<vid id="vB.C.V" ...>`) and places the link inline using a 6-tier strategy:

1. **`exact_word_id`**: If both source and target are morphologically tagged (`<zh|en|w id="wh.../w...">`), match the immediately preceding `wh.../w...` ID.
2. **`headword`**: Extract the leading `<b>headword</b>` from `Notes.Note` (with optional CJK normalization such as `神` ↔ `上帝`) and match it inside the target verse.
3. **`nearby_word_id`**: Match the nearest preceding `<zh|en|w id="wh.../w...">` within 15 plain-text characters of the link in the source verse.
4. **`nearest_wid`**: Find the closest numeric `wh.../w...` WordID in the same target verse (within `±15` words).
5. **`rel_pos`**: Map the link's relative plain-text character offset (`pos / verse_len`) onto the target verse and snap to the nearest `</zh>` / `</en>` / `</w>` tag boundary (or word boundary for untagged Bibles).
6. **`verse_end` / `chapter_end`**: Fall back to just before `</verse>` (or end of chapter if `<vid>` is absent).

---

## Usage

```bash
# Copy notes and links in-place (creates <target>.bak automatically)
python3 .grok/skills/copy-bible-notes/copy_bible_notes.py <source.bible> <target.bible>

# Write to a separate output file instead of modifying target in-place
python3 .grok/skills/copy-bible-notes/copy_bible_notes.py <source.bible> <target.bible> --out <output.bible>

# Dry-run without modifying any files
python3 .grok/skills/copy-bible-notes/copy_bible_notes.py <source.bible> <target.bible> --dry-run
```

---

## Safety & Verification
- Creates a backup `<target>.bak` before modifying `<target>` in-place (unless `--no-backup` or `--out` is used).
- Strips any existing `<sup><ref onclick='bn(...)'>...</ref></sup>` links in the target `Bible` table only if `--replace-links` is passed; otherwise refuses to double-insert if links already exist.
- Verifies after writing:
  1. `Notes` row count matches source `Notes`.
  2. Inserted `<sup>` link count in target `Bible` matches source `Bible`.
  3. **0 text mismatches** when stripping the inserted `<sup>` links from target `Bible.Scripture`.

## Grok Build Runtime

Use this `.grok/skills/copy-bible-notes/` copy. Do not run sibling copies under
`.agents/`, `.claude/`, `.codex/`, or `.cursor/`.

- Run the commands in this skill with `run_terminal_command` from the repository root.
- Inspect sources and outputs with `read_file`, `grep`, and `list_dir`.
- Do not save a `biblemate/` study file. Confirm the output path and the verification counts.
