"""Small, explicit Git adapter used by the CLI."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .models import FileChange, Version

_PR_PATTERNS = (
    re.compile(r"\(#(?P<number>[1-9][0-9]*)\)$"),
    re.compile(r"^Merge pull request #(?P<number>[1-9][0-9]*)\b"),
)


def run_git(*arguments: str) -> str:
    """Run Git and return its standard output."""
    result = subprocess.run(
        ("git", *arguments),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def changed_files(base: str, head: str) -> list[FileChange]:
    """Return name/status changes between a PR base and head."""
    output = run_git("diff", "--name-status", "--no-renames", "-z", f"{base}...{head}")
    fields = output.rstrip("\0").split("\0") if output else []
    if len(fields) % 2:
        raise RuntimeError("unexpected output from git diff --name-status")
    return [
        FileChange(status=fields[index], path=Path(fields[index + 1]))
        for index in range(0, len(fields), 2)
    ]


def file_at(ref: str, path: Path) -> str:
    """Read a UTF-8 file at a Git revision without checking it out."""
    return run_git("show", f"{ref}:{path.as_posix()}")


def latest_version() -> Version:
    """Find the highest stable ``vX.Y.Z`` tag, defaulting to 0.0.0."""
    versions: list[Version] = []
    for tag in run_git("tag", "--list", "v*").splitlines():
        try:
            versions.append(Version.parse(tag))
        except ValueError:
            continue
    return max(versions, default=Version(0, 0, 0))


def resolve_sha(ref: str = "HEAD") -> str:
    """Resolve a Git ref to a full commit SHA."""
    return run_git("rev-parse", ref).strip()


def introducing_commit(path: Path) -> tuple[str, str] | None:
    """Return the commit and subject that first added a path."""
    output = run_git(
        "log",
        "--diff-filter=A",
        "--follow",
        "--format=%H%x00%s",
        "--",
        path.as_posix(),
    ).strip()
    if not output:
        return None
    line = output.splitlines()[-1]
    sha, subject = line.split("\0", 1)
    return sha, subject


def pr_number_from_subject(subject: str) -> int | None:
    """Extract a GitHub PR number from common merge/squash subjects."""
    for pattern in _PR_PATTERNS:
        if match := pattern.search(subject):
            return int(match["number"])
    return None
