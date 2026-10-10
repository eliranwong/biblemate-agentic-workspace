---
name: zip
description: Create manual_setup.zip containing .grok/, preferences/, AGENTS.md, CLAUDE.md, and the standalone web apps (web_app_agy.py, web_app_claude.py, web_app_grok.py, web_app_gemini_api_key.py) for manual Grok Build repository setup. Use when the user runs /zip or requests this BibleMate workflow.
---

# Zip Archive Skill (Grok Build)

## Overview
This skill packages the `.grok/` configuration, root `preferences/`, root
`AGENTS.md`, root `CLAUDE.md`, and the standalone web applications into a
single `manual_setup.zip` at the repository root. That archive lets users
manually import the Grok Build BibleMate personas, skills, slash commands,
database preferences, and browser apps into a new repository.

Root files included in the archive:

- `AGENTS.md`
- `CLAUDE.md`
- `web_app_agy.py`
- `web_app_claude.py`
- `web_app_grok.py`
- `web_app_gemini_api_key.py`

## Guidelines & Objectives
When executing this skill:
1. **Remove Existing Archive**: Before creating a new zip file, always check for
   the existence of `manual_setup.zip` in the root of the repository. If it
   exists, delete it first to ensure the archive is built fresh.
2. **Execute Python Helper**: Run the zip creator script:
   ```bash
   python3 .grok/skills/zip/zip_creator.py
   ```
3. **Git Integration**: The script will automatically detect if the repository
   is a Git repository. If it is, and `manual_setup.zip` has modifications, it
   will stage, commit, and push it to the remote repository.
4. **Report Status**: Once the ZIP archive is successfully created and Git
   integration has run, output a clear summary confirming the creation of
   `manual_setup.zip` and the Git synchronization status.
