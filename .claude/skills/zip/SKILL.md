---
name: zip
description: Create manual_setup.zip containing .claude/, preferences/, and .grok/ folders, and the AGENTS.md and CLAUDE.md files for manual repository setup.
---

# Zip Archive Skill

## Overview
This skill packages the `.claude/` configuration, `preferences/`, and `.grok/` directories, and the `AGENTS.md` and `CLAUDE.md` files into a single `manual_setup.zip` file at the repository root. This archive provides users with a convenient way to manually import the customized AI team personas, skills, workflows, database preferences, Claude Code configurations, and Grok Build configurations into their own new repositories.

## Guidelines & Objectives
When executing this skill:
1. **Remove Existing Archive**: Before creating a new zip file, always check for the existence of `manual_setup.zip` in the root of the repository. If it exists, delete it first to ensure the archive is built fresh.
2. **Execute Python Helper**: Run the zip creator script located at `.claude/skills/zip/zip_creator.py` by calling:
   ```bash
   python3 .claude/skills/zip/zip_creator.py
   ```
3. **Git Integration**: The script will automatically detect if the repository is a Git repository. If it is, and `manual_setup.zip` has modifications, it will stage, commit, and push it to the remote repository.
4. **Report Status**: Once the ZIP archive is successfully created and Git integration has run, output a clear summary confirming the creation of `manual_setup.zip` and the Git synchronization status.

