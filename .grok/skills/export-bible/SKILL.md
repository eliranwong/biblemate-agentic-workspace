---
name: export-bible
description: Export a Bible from the SQLite `Bible` table into Markdown files organized by book sub-folders (`00-Intro`, `01-Gen` ... `66-Rev`) and chapter files (`001.md`, `002.md`, ...), given a Bible version name or abbreviation. Use when the user runs /export-bible or asks to export a Bible to Markdown.
---

# Export Bible Skill

## Persona
Adopt the **Verse Scripter** persona from `.grok/agents.md`.

## Overview
This skill exports a Bible from the `Bible` table of a local `.bible` SQLite database into clean Markdown files.
Given a Bible version name or abbreviation (e.g., `BSB`, `Berean Study Bible`, `ASV`, `NET`, `CUV`), it automatically saves the exported folder in `bibles/<ABBR>/` at the repository root (creating `bibles/` if it does not exist, resolved portably relative to the repository), containing:
- Book sub-folders: `00-Intro` (if `Book = 0` exists), `01-Gen`, `02-Exod`, ..., `66-Rev`
- Chapter Markdown files: `001.md`, `002.md`, `003.md`, ...

Helper script: `.grok/skills/export-bible/export_bible.py`

## Usage

```bash
# Export by abbreviation (saves to bibles/BSB/01-Gen/001.md, ...)
python3 .grok/skills/export-bible/export_bible.py "BSB"

# Export by full version name
python3 .grok/skills/export-bible/export_bible.py "Berean Study Bible"

# Export to a custom parent directory (creates <out-dir>/<ABBR>/...)
python3 .grok/skills/export-bible/export_bible.py "NET" --out-dir custom_dir
```

## Guidelines & Objectives
- Run `.grok/skills/export-bible/export_bible.py` with the user's requested Bible version or abbreviation.
- If the requested version is ambiguous or not found, report the available versions listed by the script.
- Report the output directory path, number of books, and total chapter `.md` files exported.

## Grok Build Runtime

Use this `.grok/skills/export-bible/` copy. Do not run sibling copies under
`.agents/`, `.claude/`, `.codex/`, or `.cursor/`.

- Run the commands in this skill with `run_terminal_command` from the repository root.
- Inspect sources and outputs with `read_file`, `grep`, and `list_dir`.
- Do not save a `biblemate/` study file. Confirm the output path and the verification counts.
