# Skills Repo

This repository hosts reusable skills for coding agents. The repository is organized by platform first, then by concrete skill.

The same skill name can appear under both platforms, but the contents are platform-native rather than interchangeable.

## Platforms

### codex

Codex skills live under `codex/<skill-name>/`.

Current Codex skills:

- `change-logger`
- `review-writer`
- `safe-git-publish`

These skills follow the Codex `SKILL.md` plus `agents/openai.yaml` layout, and may also include helper scripts or references.

### claude-code

Claude Code skills live under `claude-code/<skill-name>/`.

Current Claude Code skills:

- `change-logger`
- `safe-git-publish`

These skills are written for Claude Code's `SKILL.md` format. The Claude Code version of `change-logger` also includes a helper script that writes logs under `.claude/activity-log/YYYY-MM-DD/` by default.

## Skill Notes

### change-logger

- Codex version: stored in `codex/change-logger/`
- Claude Code version: stored in `claude-code/change-logger/`
- Both versions are designed to create one durable log entry per substantial engineering task, but each version uses platform-appropriate default directories and configuration variables

### review-writer

- Currently available only for Codex in `codex/review-writer/`
- Produces concise, severity-ordered review findings and can persist review artifacts

### safe-git-publish

- Codex version: stored in `codex/safe-git-publish/`
- Claude Code version: stored in `claude-code/safe-git-publish/`
- Both versions focus on safe staging, author verification, and cautious push behavior

## Repository Layout

```text
.
|-- README.md
|-- claude-code/
|   |-- change-logger/
|   |   |-- SKILL.md
|   |   `-- scripts/
|   `-- safe-git-publish/
|       `-- SKILL.md
`-- codex/
    |-- change-logger/
    |   |-- SKILL.md
    |   |-- agents/
    |   `-- scripts/
    |-- review-writer/
    |   |-- SKILL.md
    |   |-- agents/
    |   `-- scripts/
    `-- safe-git-publish/
        |-- SKILL.md
        `-- agents/
```
