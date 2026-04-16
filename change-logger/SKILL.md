---
name: change-logger
description: Record a persistent, review-friendly activity log for coding work. Use when Codex modifies files, proposes implementation changes, performs code review, gives technical recommendations, or the user asks for an audit trail of engineering assistance. Trigger for bug fixes, refactors, feature work, debugging, reviews, design advice, and similar software tasks where a durable per-task Markdown log file should be created inside a local-date directory.
---

# Change Logger

Append one structured log entry for each substantial coding task.

Treat the log as an audit trail, not a transcript. Prefer Markdown because it is easier for humans to scan and review in git diffs.

Store Markdown logs in per-day directories:

- `.codex/activity-log/YYYY-MM-DD/`
- one `.md` file per logged task
- default filename pattern: `HHMMSS-kind-status.md`

## Logging Rules

Log the task when any of the following is true:

- Modify one or more files.
- Recommend a concrete implementation approach, refactor, or fix.
- Produce code review findings or technical risk analysis.
- Run meaningful verification that supports a coding decision.

Skip logging for:

- Casual chat.
- Purely administrative messages.
- Trivial clarifications that do not lead to an engineering recommendation.

Write exactly one consolidated entry per user task unless the user explicitly asks for finer-grained logs.

## Log Destination

Use `scripts/append_log.py`.

Default destination selection is:

1. `CODEX_ACTIVITY_LOG` if set.
2. `<git-root>/.codex/activity-log/` if inside a git repository.
3. `<cwd>/.codex/activity-log/` otherwise.
4. `/home/$USER/workspace/activity-log/` if that workspace exists; otherwise `~/workspace/activity-log/`.

Default output format is Markdown. Use `--format jsonl` only when another tool explicitly needs machine-oriented records.

Do not write secrets, tokens, passwords, cookies, or full credential-bearing commands into the log. Summarize sensitive values instead of copying them.

## Required Content

Include these fields on every entry:

- `kind`: one of `code_change`, `advice`, `review`, `debugging`, `plan`.
- `request`: short summary of the user request.
- `summary`: short summary of what Codex changed or recommended.
- `files`: modified files or reviewed files when applicable.
- `tests`: verification commands and concise outcomes when applicable.
- `status`: one of `completed`, `partial`, `blocked`.

Add `notes` for important constraints, follow-up items, or reasons work could not be completed.

## Workflow

1. Decide whether the task is loggable under the rules above.
2. Gather the final task summary after edits, review, or recommendations are complete.
3. Run `scripts/append_log.py` once to create one new Markdown file under the current local date directory.
4. If logging fails, mention the failure in the final response.

## Command Pattern

Run the logger from the skill directory or by absolute path. Repeat `--file` and `--test` as needed.

```bash
python scripts/append_log.py \
  --kind code_change \
  --status completed \
  --request "Fix the placement overflow bug in nonlinear placement" \
  --summary "Adjusted the overflow stopping condition and updated the related test." \
  --file AiEDA/third_party/AutoDMP/dreamplace/NonLinearPlace.py \
  --file tests/test_non_linear_place.py \
  --test "pytest tests/test_non_linear_place.py -q (pass)"
```

For recommendation-only tasks, omit `--file` if no file was touched:

```bash
python scripts/append_log.py \
  --kind advice \
  --status completed \
  --request "How should we cache placement metadata?" \
  --summary "Recommended a repo-local SQLite cache with content-hash invalidation." \
  --notes "No code changes were made."
```

If a downstream tool needs JSONL instead of Markdown:

```bash
python scripts/append_log.py \
  --format jsonl \
  --kind advice \
  --status completed \
  --request "How should we cache placement metadata?" \
  --summary "Recommended a repo-local SQLite cache with content-hash invalidation."
```

## Quality Bar

- Keep `request` and `summary` concise.
- Prefer repository-relative paths in `files`.
- Record failed or skipped verification honestly.
- Do not create multiple near-duplicate entries for one task.
- Let the script create a new file for each task instead of appending multiple tasks into one Markdown file.
