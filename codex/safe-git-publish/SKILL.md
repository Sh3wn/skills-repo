---
name: safe-git-publish
description: Prepare, verify, and publish git changes safely. Use when the user wants to commit, amend, rewrite author metadata, set the correct git identity, or push to a remote without accidentally staging unrelated files or damaging history.
---

# Safe Git Publish

Use this skill for git commit and push tasks where safety matters more than speed.

The goal is to publish only the intended changes, with the correct author identity, to the correct remote and branch.

## Preflight

Before changing git state, inspect:

- `git status --short --branch`
- `git remote -v`
- `git config --show-origin --get-regexp '^user\\.(name|email)$'`

When relevant, also inspect:

- `git log -1 --format=...` for the latest commit identity
- `git diff --cached --name-only` for the staged set
- `git ls-remote --heads <remote>` when the remote may have changed, been recreated, or might be empty

## Staging Rules

- Stage only the files requested by the user or directly required for the task.
- Prefer explicit paths in `git add`.
- Avoid `git add .` unless the repository is intentionally clean and the user clearly wants everything staged.
- Do not scoop up unrelated untracked files just because they are present.
- If the worktree is dirty, read the touched files carefully and preserve user changes that are outside the task.

## Identity Rules

- Verify `user.name` and `user.email` before committing.
- If the wrong identity is configured, prefer the smallest safe fix:
  - repo-local `git config user.name/user.email` for one repository
  - global `git config --global user.name/user.email` only when the user wants a new default
- If only the latest commit metadata is wrong and the content is already correct, prefer `git commit --amend --reset-author --no-edit`.
- Do not rewrite history unless it is necessary for the task or explicitly approved.

## Commit Rules

- Use a focused commit message tied to the actual change.
- Check the staged file list before committing.
- If the repository does not exist yet and the task requires publishing, initialize it explicitly and choose the target branch deliberately.
- Do not amend old commits or squash history unless the user asked for that outcome.

## Push Rules

- Confirm the intended remote and branch before pushing.
- For a new branch or empty remote, use upstream tracking such as `git push -u origin main`.
- For ordinary updates, use a normal push.
- If history was rewritten, prefer `git push --force-with-lease` instead of `--force`.
- If push fails, distinguish among reachability, authentication, authorization, and non-fast-forward conflicts before deciding the next step.

## Safety Checklist

Before push, verify all of these:

- correct staged files
- correct branch
- correct author identity
- correct remote URL
- correct push mode

After push, verify at least one of:

- `git status --short --branch`
- `git ls-remote --heads <remote>`

## Response Pattern

When reporting back to the user, state:

- what was committed or amended
- which identity was used
- which remote and branch were updated
- any files intentionally left untracked or uncommitted

Prefer predictable, minimal git operations over clever shortcuts.
