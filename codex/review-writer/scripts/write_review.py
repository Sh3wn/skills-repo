#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


VALID_STATUS = {"completed", "partial", "blocked"}
VALID_FALLBACK_MODES = {"auto", "never"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write a structured Codex review report.")
    parser.add_argument("--status", choices=sorted(VALID_STATUS), default="completed")
    parser.add_argument("--request", required=True, help="Short summary of the review request.")
    parser.add_argument("--summary", required=True, help="Short summary of the review outcome.")
    parser.add_argument(
        "--finding",
        action="append",
        dest="findings",
        default=[],
        help="Review finding text. Repeat for multiple findings.",
    )
    parser.add_argument(
        "--question",
        action="append",
        dest="questions",
        default=[],
        help="Open question or assumption. Repeat as needed.",
    )
    parser.add_argument(
        "--change-summary",
        default="",
        help="Optional short recap of the reviewed change.",
    )
    parser.add_argument(
        "--file",
        action="append",
        dest="files",
        default=[],
        help="Reviewed file path. Repeat for multiple files.",
    )
    parser.add_argument(
        "--test",
        action="append",
        dest="tests",
        default=[],
        help="Validation command, output, or evidence. Repeat for multiple items.",
    )
    parser.add_argument("--notes", default="", help="Optional review notes or limitations.")
    parser.add_argument(
        "--cwd",
        default=os.getcwd(),
        help="Working directory used to resolve the default review destination.",
    )
    parser.add_argument(
        "--review-path",
        default="",
        help="Override output path. This can be a directory or a .md file. Defaults to CODEX_REVIEW_LOG or .codex/review-log/.",
    )
    parser.add_argument(
        "--fallback-mode",
        choices=sorted(VALID_FALLBACK_MODES),
        default="",
        help="Behavior when the default target cannot be written. Defaults to CODEX_REVIEW_LOG_FALLBACK or auto.",
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
    if args.review_path:
        return Path(args.review_path).expanduser().resolve()

    env_path = os.environ.get("CODEX_REVIEW_LOG")
    if env_path:
        return Path(env_path).expanduser().resolve()

    return None


def default_review_target(cwd: Path) -> Path:
    repo_root = git_root(cwd)
    base = repo_root if repo_root is not None else cwd
    return (base / ".codex" / "review-log").resolve()


def fallback_workspace_dir() -> Path:
    local_workspace_dir = Path("/home") / Path.home().name / "workspace"
    if local_workspace_dir.exists():
        return local_workspace_dir
    return Path.home() / "workspace"


def fallback_review_target() -> Path:
    return (fallback_workspace_dir() / "activity-log" / "review-log").resolve()


def resolve_fallback_mode(args: argparse.Namespace) -> str:
    if args.fallback_mode:
        return args.fallback_mode

    env_value = os.environ.get("CODEX_REVIEW_LOG_FALLBACK", "").strip().lower()
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
    lines.append(f"# {entry['timestamp_local']} | review | {entry['status']}")
    lines.append("")
    lines.append(f"- Local Time: `{entry['timestamp_local']}`")
    lines.append(f"- UTC Time: `{entry['timestamp_utc']}`")
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
    lines.append("## Findings")
    lines.append("")
    if entry["findings"]:
        for finding in entry["findings"]:
            lines.append(f"- {finding}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Open Questions")
    lines.append("")
    if entry["questions"]:
        for question in entry["questions"]:
            lines.append(f"- {question}")
    else:
        lines.append("- none")
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
    lines.append("## Change Summary")
    lines.append("")
    lines.append(entry["change_summary"] or "none")
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

    stem = f"{entry['time_compact']}-review-{entry['status']}"
    return write_unique_markdown(target / entry["date_local"], stem, content)


def main() -> int:
    args = parse_args()
    cwd = Path(args.cwd).expanduser().resolve()
    explicit_target = resolve_explicit_target(args)
    fallback_mode = resolve_fallback_mode(args)
    review_target = explicit_target if explicit_target is not None else default_review_target(cwd)
    local_now = datetime.now().astimezone()
    utc_now = local_now.astimezone(timezone.utc)

    entry = {
        "timestamp_utc": utc_now.isoformat(timespec="seconds"),
        "timestamp_local": local_now.isoformat(timespec="seconds"),
        "date_local": local_now.date().isoformat(),
        "time_compact": local_now.strftime("%H%M%S"),
        "status": args.status,
        "request": normalize_text(args.request),
        "summary": normalize_text(args.summary),
        "findings": normalize_list(args.findings),
        "questions": normalize_list(args.questions),
        "change_summary": normalize_text(args.change_summary),
        "files": normalize_list(args.files),
        "tests": normalize_list(args.tests),
        "notes": normalize_text(args.notes),
        "cwd": str(cwd),
    }

    try:
        final_path = write_markdown(review_target, entry)
    except OSError as exc:
        if explicit_target is not None or fallback_mode == "never":
            raise
        final_path = write_markdown(fallback_review_target(), entry)
        print(
            f"[review-writer] default review target unavailable ({exc}); wrote to {final_path}",
            file=sys.stderr,
        )

    print(str(final_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
