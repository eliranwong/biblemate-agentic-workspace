---
name: md
description: Convert a specified file to markdown format, or export the last response/whole conversation to export/md.
---

# Markdown Conversion & Export Skill

## Overview
This standalone skill enables any agent to perform file markdown conversions or export conversation dialogue to the designated export directory.

## Guidelines & Objectives
When executing this skill:
- Always run the python converter script located at `.claude/skills/md/md_converter.py` to perform the conversion or export.
- Execute the script using: `python3 .claude/skills/md/md_converter.py "<query>"` where `<query>` is the input prompt or arguments containing the file path or export directives (e.g. `whole`, `conversation`).
- Present the exact output of the script to the user, confirming the paths and file status of the output.
