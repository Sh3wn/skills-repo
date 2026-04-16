---
name: review-writer
description: Write concise, actionable code review findings for diffs, commits, or changed files. Use when the user asks for a review, PR review, patch review, change risk analysis, or wants issues summarized as severity-ordered findings with file references.
---

# Review Writer

Use this skill when the task is to review code changes rather than to implement them.

Focus on correctness, regressions, security, data loss, broken assumptions, and missing test coverage. Ignore style nits unless the user explicitly asks for them or they hide a real bug.

## Workflow

1. Gather the review surface.
   Read the diff, changed files, recent commits, and any test output or issue context that defines the intended behavior.

2. Look for real behavioral risk.
   Prioritize user-visible breakage, invalid state transitions, contract mismatches, migration issues, missing cleanup, concurrency hazards, and edge cases that are no longer covered.

3. Validate each claim.
   Do not speculate loosely. Point to the exact file and line, and explain the failure mode or regression condition. If a finding depends on an assumption, state that assumption explicitly.

4. Write findings in review form.
   Findings come first. Summaries are secondary.

5. Persist the review when it should be reusable.
   Use `scripts/write_review.py` to write one Markdown review file for the task. If you also need an audit trail entry for the overall engineering activity, follow up with one `change-logger` entry using `kind=review`.

## Review Artifact

Persist review reports as Markdown under:

- `.codex/review-log/YYYY-MM-DD/`
- one `.md` file per review task
- default filename pattern: `HHMMSS-review-status.md`

Default destination selection is:

1. `CODEX_REVIEW_LOG` if set.
2. `<git-root>/.codex/review-log/` if inside a git repository.
3. `<cwd>/.codex/review-log/` otherwise.
4. `/home/$USER/workspace/activity-log/review-log/` if fallback is enabled and the workspace exists; otherwise `~/workspace/activity-log/review-log/`.

Fallback behavior is controlled by `--fallback-mode auto|never` or `CODEX_REVIEW_LOG_FALLBACK`.
The default is `auto`. When fallback is used, the script emits a warning on stderr and prints the final path on stdout.

## Output Rules

- Start with findings, not with praise or a change summary.
- Order findings by severity.
- Keep each finding concise and self-contained.
- Include an exact file reference for every finding.
- Explain why the issue matters in behavior terms, not only in code-style terms.
- Mention missing tests when a risky path changed without targeted coverage.
- If there are no findings, say that explicitly and note residual risks or testing gaps.
- When a persistent artifact is useful, write it with `scripts/write_review.py` instead of burying the only copy inside chat output.

## Suggested Finding Shape

Use a short title followed by 2-5 sentences that cover:

- what is wrong
- when it breaks
- why it matters
- where it is in the code

## Severity Guide

- Blocking: data corruption, security issues, crashes, broken deploy paths, clearly wrong results on common paths
- Major: likely regression, contract mismatch, missing migration, wrong edge-case behavior, incorrect fallback logic
- Moderate: risky validation gaps, fragile logic, missing targeted tests for a changed behavior

## Review Heuristics

- Check initialization and update paths separately.
- Check empty, null, error, and retry paths.
- Check renamed config keys, call sites, and defaults after refactors.
- Check state reset and cleanup behavior.
- Check whether async ordering or retries can duplicate work.
- Check whether tests still cover the changed branch and failure mode.

## Response Pattern

Use a structure like:

1. Findings
2. Open questions or assumptions
3. Short change summary

Keep the review practical. Prefer a small number of strong findings over a long list of weak guesses.

## Command Pattern

Run the writer from the skill directory or by absolute path. Repeat `--finding`, `--question`, `--file`, and `--test` as needed.

```bash
python scripts/write_review.py \
  --status completed \
  --fallback-mode auto \
  --request "Review the cache invalidation patch" \
  --summary "Found one major regression in the stale-read path." \
  --finding "Major: stale cache entries can survive a delete because the invalidation branch skips composite keys in src/cache.py:84." \
  --question "Assuming deletes must invalidate both primary and composite cache keys." \
  --change-summary "The patch refactors cache invalidation and adds one happy-path test." \
  --file src/cache.py \
  --file tests/test_cache.py \
  --test "pytest tests/test_cache.py -q (pass)"
```
