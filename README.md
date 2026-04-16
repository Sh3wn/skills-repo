# Skills Repo

This repository hosts reusable skills for coding agents.

At the moment, the repository contains one published skill:

## change-logger

`change-logger` records a persistent, review-friendly activity log for substantial coding tasks.

Use it when an agent:

- modifies files
- proposes a concrete implementation or fix
- performs code review or technical risk analysis
- runs meaningful verification that supports an engineering decision

The skill writes one structured log entry per task, typically as Markdown under:

- `.codex/activity-log/YYYY-MM-DD/`

It includes a helper script at `change-logger/scripts/append_log.py` for creating entries with consistent fields such as:

- `kind`
- `request`
- `summary`
- `files`
- `tests`
- `status`

The goal is to keep an auditable engineering trail that is easy to review in git diffs.

## Repository Layout

```text
.
|-- README.md
`-- change-logger/
    |-- SKILL.md
    |-- agents/
    `-- scripts/
```
