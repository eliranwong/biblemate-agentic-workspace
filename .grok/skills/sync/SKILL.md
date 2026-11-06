---
name: sync
description: Fetch origin/main, rebase this checkout onto it, commit local changes, and push. Use when the user runs /sync or requests this BibleMate workflow.
---

# Sync Skill

## Overview

Fetch the latest `origin/main`, rebase this checkout onto it, commit local changes, and push. Sync is two-way: remote commits land on local `main`, and local commits land on the remote.

## Steps

### Phase 1: Fetch and integrate origin/main

1. Run `git status --short` and `git rev-parse --abbrev-ref HEAD`.
2. Run `git fetch origin main`. This updates `origin/main` and does not change the working tree.
3. If the current branch is not `main`, report the branch name and that `origin/main` was fetched. Skip the rebase in this phase. Continue with Phase 2 and Phase 3 for the current branch.
4. On `main`, record both directions:
   - Ahead: `git rev-list --count origin/main..HEAD`
   - Behind: `git rev-list --count HEAD..origin/main`
5. If behind is `0`, continue to Phase 2.
6. If behind is greater than `0` and `git status --short` is empty, run `git pull --rebase origin main`.
7. If behind is greater than `0` and the working tree is dirty, run `git stash push -u -m "sync"`, then `git pull --rebase origin main`, then `git stash pop`.
8. If the rebase or the stash pop stops with conflicts, stop. Report the conflicted files. Leave a saved `sync` stash in place. Do not commit, push, abort, or force-push.

### Phase 2: Commit any uncommitted changes

9. Run `git status --short` again.
10. If there are no uncommitted changes, skip to Phase 3.
11. Run `git add .` to stage all changes in the workspace.
12. Choose the commit message:
    - If the user provided a commit message, use that message.
    - Otherwise review `git diff --cached --stat` and write a concise message that summarizes the modified files. Use `Sync latest changes` when the diff has no clearer summary.
    - Keep the first line under 100 characters. Add a blank line and a short body when the change needs one.
13. Run `git commit -m "<message>"` with that message.

### Phase 3: Push any unpushed commits

14. Run `git rev-list --count @{upstream}..HEAD` to check how many commits are ahead of the remote.
    - If the output is `0` or the command errors (no upstream), also run `git log --oneline origin/main..HEAD` to detect unpushed commits.
15. If there are unpushed commits, run `git push`.
16. If the push is rejected because the remote has newer commits, run `git fetch origin main`, then `git pull --rebase origin main`, then `git push` once more. If that second push fails, stop and report the error.
17. If the push fails for any other reason, stop and report the error.
18. If there are no unpushed commits, report that local commits are already on the remote.

### Phase 4: Report result

19. Report how many commits came in from `origin/main`, the number of files changed (if any), the commit hash (if any), and whether the push succeeded.
20. On `main`, the sync is complete only when both ranges are empty:
    - `git log --oneline origin/main..HEAD`
    - `git log --oneline HEAD..origin/main`
21. Confirm with `git status -sb`. A finished `main` sync shows `main...origin/main` with no ahead or behind count.

## Critical

- Fetch `origin/main` even when there is nothing to commit or push.
- Check for unpushed commits even when there is nothing new to commit.
- Rebase onto `origin/main`. Do not create a merge commit.
- Do not run `git push --force` or `git push --force-with-lease`.
- Stop on a rebase conflict or a stash-pop conflict.
