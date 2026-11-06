---
description: Fetch origin/main, rebase main, commit local changes, and push. Use a custom commit message when provided.
---

Adopt the **Verse Scripter** persona from `.claude/agents.md`.

Read and follow `.claude/skills/sync/SKILL.md` completely. Use Claude Code's `Bash` tool for Git operations from the repository root.

Perform all four sync phases: fetch and integrate `origin/main`, commit local changes, push unpushed commits, and verify both directions on `main`. Stop on rebase or stash-pop conflicts; do not create merge commits or force-push.

If a commit message is provided as input, use it. Otherwise, generate a descriptive message from the staged diff.

# Input

$ARGUMENTS
