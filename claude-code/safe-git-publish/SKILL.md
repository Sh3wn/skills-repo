---
name: safe-git-publish
description: Prepare, verify, and publish git changes safely in Claude Code. Use when you want Claude to stage only intended files, fix git author metadata, amend the latest commit safely, or push without publishing unrelated work.
argument-hint: "[publish goal]"
disable-model-invocation: true
---

# Safe Git Publish

Use this skill when git publication safety matters more than speed.

The goal is to publish only the intended changes, with the correct author identity, to the correct remote and branch.

If the skill was invoked manually, use `$ARGUMENTS` to clarify the publish goal when it adds useful context.

## Preflight

Before changing git state, inspect:

- `git status --short --branch`
- `git remote -v`
- `git config --show-origin --get-regexp '^user\.(name|email)$'`

When relevant, also inspect:

- `git diff --cached --name-only`
- `git log -1 --format='commit %H%nAuthor: %an <%ae>%nCommitter: %cn <%ce>%nSubject: %s'`
- `git ls-remote --heads <remote>` when the remote may be empty, recreated, or changed

## Staging Rules

- Stage only the files requested by the user or directly required for the task.
- Prefer explicit paths in `git add`.
- Avoid `git add .` unless the repository is intentionally clean and the user clearly wants everything staged.
- Do not stage unrelated untracked files just because they are present.
- If the worktree is dirty, preserve user changes that are outside the task.

## Identity Rules

- Verify `user.name` and `user.email` before committing.
- If the wrong identity is configured, prefer the smallest safe fix:
  - repo-local `git config user.name/user.email` for one repository
  - global `git config --global user.name/user.email` only when the user wants a new default
- If only the latest commit metadata is wrong and the content is already correct, make sure the index is clean before using `git commit --amend --reset-author --no-edit`.
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

## Response Pattern

When reporting back to the user, state:

- what was committed or amended
- which identity was used
- which remote and branch were updated
- any files intentionally left untracked or uncommitted

Prefer predictable, minimal git operations over clever shortcuts.
