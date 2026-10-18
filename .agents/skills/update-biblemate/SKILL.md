---
name: update-biblemate
description: Download and extract the manual setup zip to initialize workspace directories.
---

# Update BibleMate Skill

## Overview
This standalone skill enables the agent to update or initialize a workspace by downloading a manual setup zip file, extracting it, and creating the necessary workspace directories (such as `biblemate`, `notes`, `images`, `export`).

## Guidelines & Objectives
When executing this skill:
1. **Verify Operating System**: The update process is only supported on macOS or Linux systems.
2. **Verify Workspace Folder**: The update process must NOT run if the current workspace folder name is `antigravity-biblemate-workspace`, to prevent overwriting files in the source repository.
3. **Execute Python Helper**: Run the updater script located at `.agents/skills/update-biblemate/updater.py` by calling:
   ```bash
   python3 .agents/skills/update-biblemate/updater.py
   ```
4. **Report Status**: Confirm whether the update was successful, or output the specific condition/error message if it was skipped or failed.
