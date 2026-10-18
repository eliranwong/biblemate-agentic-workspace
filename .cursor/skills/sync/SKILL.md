---
name: sync
description: Git add, commit, and push all latest changes to the remote repository. Use when the user runs /sync or requests this BibleMate workflow.
---

# Sync Skill

## Overview
This standalone skill enables the agent to stage, commit, and push all latest workspace changes to the remote Git repository.

## Guidelines & Objectives
When executing this skill:
1. **Analyze Workspace State**: Run a check on the repository using `git status` to see what files have been modified, created, or deleted.
2. **Stage Changes**: Run `git add .` to stage all changes in the current workspace.
3. **Commit Changes**: Create a descriptive commit message that summarizes the main updates. If the user provided a custom commit message (e.g., via the slash command argument), use that message. Otherwise, construct a clean message (e.g., "Sync latest changes" or a list of modified files) and run `git commit -m "<commit_message>"`.
4. **Push to Remote**: Run `git push` to upload the changes to the remote repository.
5. **Verify and Report**: Confirm that the push succeeded and present a clean summary of the synced changes to the user.
