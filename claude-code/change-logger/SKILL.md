---
name: change-logger
description: Record a persistent, review-friendly activity log for Claude Code work. Use when Claude modifies files, produces review findings, runs meaningful verification, or the user asks for a durable audit trail of engineering work.
argument-hint: "[request summary]"
disable-model-invocation: true
---

# Change Logger

Use this skill to write one structured Markdown activity log entry for a substantial Claude Code task.

Treat the log as an audit trail, not a transcript. Keep the entry concise, factual, and safe to store in git.

## When To Log

Log the task when any of the following is true:

- files were modified
- a concrete implementation or fix was recommended
- code review findings or technical risk analysis were produced
- meaningful verification informed an engineering decision

Skip logging for:

- casual chat
- purely administrative messages
- trivial clarifications that do not lead to an engineering recommendation

Write exactly one consolidated entry per user task unless the user explicitly wants finer-grained logs.

## Default Destination

Use `scripts/append_log.py`.

Default destination selection is:

1. `CLAUDE_ACTIVITY_LOG` if set.
2. `<git-root>/.claude/activity-log/` if inside a git repository.
3. `<cwd>/.claude/activity-log/` otherwise.
4. `/home/$USER/workspace/activity-log/claude-code/` if fallback is enabled and the workspace exists; otherwise `~/workspace/activity-log/claude-code/`.

Fallback behavior is controlled by `--fallback-mode auto|never` or `CLAUDE_ACTIVITY_LOG_FALLBACK`.
The default is `auto`. When fallback is used, the script emits a warning on stderr and prints the final path on stdout.

## Required Content

Include these fields on every entry:

- `kind`: one of `code_change`, `advice`, `review`, `debugging`, `plan`
- `request`: short summary of the user request
- `summary`: short summary of what Claude changed or recommended
- `files`: modified or reviewed files when applicable
- `tests`: verification commands and concise outcomes when applicable
- `status`: one of `completed`, `partial`, `blocked`

Add `notes` for important constraints, follow-up items, or reasons work could not be completed.

Do not write secrets, tokens, passwords, cookies, or full credential-bearing commands into the log.

## Workflow

1. Gather the final task summary after edits, review, or recommendations are complete.
2. Normalize the request, summary, files, tests, and notes.
3. Run `python3 scripts/append_log.py` once to create one new Markdown file for the task.
4. Report the written path back to the user when it is useful.

## Command Pattern

If the skill was invoked manually, use `$ARGUMENTS` as the request summary when it accurately names the task.

```bash
python3 scripts/append_log.py \
  --kind code_change \
  --status completed \
  --fallback-mode auto \
  --request "Fix the placement overflow bug in nonlinear placement" \
  --summary "Adjusted the overflow stopping condition and updated the related test." \
  --file src/placement/nonlinear.py \
  --file tests/test_non_linear_place.py \
  --test "pytest tests/test_non_linear_place.py -q (pass)"
```

For recommendation-only tasks, omit `--file` if no file was touched:

```bash
python3 scripts/append_log.py \
  --kind advice \
  --status completed \
  --fallback-mode auto \
  --request "How should we cache placement metadata?" \
  --summary "Recommended a repo-local SQLite cache with content-hash invalidation." \
  --notes "No code changes were made."
```
