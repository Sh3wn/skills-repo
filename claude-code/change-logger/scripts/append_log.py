#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


VALID_KINDS = {"code_change", "advice", "review", "debugging", "plan"}
VALID_STATUS = {"completed", "partial", "blocked"}
VALID_FORMATS = {"markdown", "jsonl"}
VALID_FALLBACK_MODES = {"auto", "never"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append a structured Claude Code activity log entry.")
    parser.add_argument(
        "--format",
        choices=sorted(VALID_FORMATS),
        default="",
        help="Output format. Defaults to markdown unless the path ends in .jsonl.",
    )
    parser.add_argument("--kind", required=True, choices=sorted(VALID_KINDS))
    parser.add_argument("--status", required=True, choices=sorted(VALID_STATUS))
    parser.add_argument("--request", required=True, help="Short summary of the user request.")
    parser.add_argument("--summary", required=True, help="Short summary of work performed or advice given.")
    parser.add_argument(
        "--file",
        action="append",
        dest="files",
        default=[],
        help="Repository-relative file path. Repeat for multiple files.",
    )
    parser.add_argument(
        "--test",
        action="append",
        dest="tests",
        default=[],
        help="Verification command and outcome. Repeat for multiple test runs.",
    )
    parser.add_argument("--notes", default="", help="Optional follow-up notes or constraints.")
    parser.add_argument(
        "--cwd",
        default=os.getcwd(),
        help="Working directory used to resolve the default log destination.",
    )
    parser.add_argument(
        "--log-path",
        default="",
        help="Override output path. For markdown this can be a directory or a .md file. Defaults to CLAUDE_ACTIVITY_LOG or .claude/activity-log/.",
    )
    parser.add_argument(
        "--fallback-mode",
        choices=sorted(VALID_FALLBACK_MODES),
        default="",
        help="Behavior when the default target cannot be written. Defaults to CLAUDE_ACTIVITY_LOG_FALLBACK or auto.",
    )
    return parser.parse_args()


def git_root(cwd: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    root = result.stdout.strip()
    return Path(root) if root else None


def resolve_explicit_target(args: argparse.Namespace) -> Path | None:
    if args.log_path:
        return Path(args.log_path).expanduser().resolve()

    env_path = os.environ.get("CLAUDE_ACTIVITY_LOG")
    if env_path:
        return Path(env_path).expanduser().resolve()

    return None


def default_log_target(cwd: Path, output_format: str) -> Path:
    repo_root = git_root(cwd)
    base = repo_root if repo_root is not None else cwd
    if output_format == "jsonl":
        return (base / ".claude" / "activity-log.jsonl").resolve()
    return (base / ".claude" / "activity-log").resolve()


def fallback_workspace_dir() -> Path:
    local_workspace_dir = Path("/home") / Path.home().name / "workspace"
    if local_workspace_dir.exists():
        return local_workspace_dir
    return Path.home() / "workspace"


def fallback_log_target(output_format: str) -> Path:
    workspace_dir = fallback_workspace_dir() / "activity-log" / "claude-code"
    if output_format == "jsonl":
        return (workspace_dir / "activity-log.jsonl").resolve()
    return workspace_dir.resolve()


def resolve_fallback_mode(args: argparse.Namespace) -> str:
    if args.fallback_mode:
        return args.fallback_mode

    env_value = os.environ.get("CLAUDE_ACTIVITY_LOG_FALLBACK", "").strip().lower()
    if env_value in VALID_FALLBACK_MODES:
        return env_value
    return "auto"


def normalize_list(items: list[str]) -> list[str]:
    cleaned = []
    seen = set()
    for item in items:
        value = item.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        cleaned.append(value)
    return cleaned


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def resolve_format(args: argparse.Namespace, target: Path | None) -> str:
    if args.format:
        return args.format
    if target is not None and target.suffix == ".jsonl":
        return "jsonl"
    return "markdown"


def write_unique_markdown(day_dir: Path, stem: str, content: str) -> Path:
    day_dir.mkdir(parents=True, exist_ok=True)
    for index in range(1, 10000):
        suffix = "" if index == 1 else f"-{index}"
        candidate = day_dir / f"{stem}{suffix}.md"
        try:
            with candidate.open("x", encoding="utf-8") as handle:
                handle.write(content)
            return candidate
        except FileExistsError:
            continue
    raise FileExistsError(f"Unable to allocate a unique Markdown path for stem '{stem}'.")


def render_markdown_document(entry: dict) -> str:
    lines = []
    lines.append(f"# {entry['timestamp_local']} | {entry['kind']} | {entry['status']}")
    lines.append("")
    lines.append(f"- Local Time: `{entry['timestamp_local']}`")
    lines.append(f"- UTC Time: `{entry['timestamp_utc']}`")
    lines.append(f"- Kind: `{entry['kind']}`")
    lines.append(f"- Status: `{entry['status']}`")
    lines.append("")
    lines.append("## Request")
    lines.append("")
    lines.append(entry["request"])
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(entry["summary"])
    lines.append("")

    lines.append("## Files")
    lines.append("")
    if entry["files"]:
        for file_path in entry["files"]:
            lines.append(f"- `{file_path}`")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Tests")
    lines.append("")
    if entry["tests"]:
        for test in entry["tests"]:
            lines.append(f"- `{test}`")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append(entry["notes"] or "none")
    lines.append("")
    lines.append("## Working Directory")
    lines.append("")
    lines.append(f"`{entry['cwd']}`")
    lines.append("")
    return "\n".join(lines)


def write_markdown(target: Path, entry: dict) -> Path:
    content = render_markdown_document(entry)
    if target.suffix == ".md":
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    stem = f"{entry['time_compact']}-{entry['kind'].replace('_', '-')}-{entry['status']}"
    return write_unique_markdown(target / entry["date_local"], stem, content)


def persist_entry(log_target: Path, entry: dict, output_format: str) -> Path:
    if output_format == "jsonl":
        log_target.parent.mkdir(parents=True, exist_ok=True)
        with log_target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=True) + "\n")
        return log_target
    return write_markdown(log_target, entry)


def main() -> int:
    args = parse_args()
    cwd = Path(args.cwd).expanduser().resolve()
    explicit_target = resolve_explicit_target(args)
    output_format = resolve_format(args, explicit_target)
    fallback_mode = resolve_fallback_mode(args)
    log_target = explicit_target if explicit_target is not None else default_log_target(cwd, output_format)
    local_now = datetime.now().astimezone()
    utc_now = local_now.astimezone(timezone.utc)

    entry = {
        "timestamp_utc": utc_now.isoformat(timespec="seconds"),
        "timestamp_local": local_now.isoformat(timespec="seconds"),
        "date_local": local_now.date().isoformat(),
        "time_local": local_now.timetz().isoformat(timespec="seconds"),
        "time_compact": local_now.strftime("%H%M%S"),
        "kind": args.kind,
        "status": args.status,
        "request": normalize_text(args.request),
        "summary": normalize_text(args.summary),
        "files": normalize_list(args.files),
        "tests": normalize_list(args.tests),
        "notes": normalize_text(args.notes),
        "cwd": str(cwd),
    }

    try:
        final_path = persist_entry(log_target, entry, output_format)
    except OSError as exc:
        if explicit_target is not None or fallback_mode == "never":
            raise
        final_path = persist_entry(fallback_log_target(output_format), entry, output_format)
        print(
            f"[claude-change-logger] default log target unavailable ({exc}); wrote to {final_path}",
            file=sys.stderr,
        )

    print(str(final_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
