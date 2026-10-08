"""Changelog fragment parsing and pull-request validation."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from .models import Bump, FileChange, Fragment

_HEADER = re.compile(
    r"^(?P<kind>[a-z][a-z0-9-]*)(?:\((?P<scope>[^)\r\n]+)\))?"
    r"(?P<breaking>!)?:\s+(?P<description>\S.*)$"
)
_PATCH_KINDS = frozenset({"fix", "refactor", "chore", "perf", "revert", "test"})


class FragmentError(ValueError):
    """A fragment or fragment change set is invalid."""


def parse_fragment(content: str, source: Path | str = Path("<fragment>")) -> Fragment:
    """Parse a conventional-commit header followed by optional Markdown details."""
    path = Path(source)
    lines = content.splitlines()
    try:
        header_index = next(index for index, line in enumerate(lines) if line.strip())
    except StopIteration as error:
        raise FragmentError(f"{path}: fragment is empty") from error

    header = lines[header_index].strip()
    match = _HEADER.fullmatch(header)
    if match is None:
        raise FragmentError(
            f"{path}: first non-empty line must be a conventional header, "
            "for example 'fix: correct the result'"
        )

    kind = match["kind"]
    if match["breaking"]:
        bump = Bump.MAJOR
    elif kind == "feat":
        bump = Bump.MINOR
    elif kind in _PATCH_KINDS:
        bump = Bump.PATCH
    else:
        supported = ", ".join(sorted(_PATCH_KINDS | {"feat"}))
        raise FragmentError(
            f"{path}: unsupported change type {kind!r}; expected one of {supported}"
        )

    body = "\n".join(lines[header_index + 1 :]).strip()
    return Fragment(
        kind=kind,
        scope=match["scope"],
        description=match["description"],
        bump=bump,
        body=body,
        source=path,
    )


def discover_fragments(directory: Path) -> list[Fragment]:
    """Parse all Markdown fragments in lexical path order."""
    if not directory.is_dir():
        return []
    return [parse_fragment(path.read_text(), path) for path in sorted(directory.glob("*.md"))]


def validate_pr_changes(
    changes: Iterable[FileChange], fragment_directory: Path = Path("CHANGELOG.d")
) -> Path:
    """Require exactly one added fragment and reject edits to existing fragments."""
    prefix = fragment_directory.as_posix().rstrip("/") + "/"
    fragment_changes = [
        change for change in changes if change.path.as_posix().startswith(prefix)
    ]
    added = [
        change
        for change in fragment_changes
        if change.status == "A" and change.path.suffix.lower() == ".md"
    ]
    invalid = [change for change in fragment_changes if change not in added]

    if invalid:
        details = ", ".join(f"{change.status} {change.path}" for change in invalid)
        raise FragmentError(f"existing or non-Markdown fragments cannot be changed: {details}")
    if len(added) != 1:
        raise FragmentError(
            f"pull request must add exactly one changelog fragment; found {len(added)}"
        )
    return added[0].path


def highest_bump(fragments: Iterable[Fragment]) -> Bump:
    """Return the highest required bump, or ``none`` for an empty collection."""
    return max((fragment.bump for fragment in fragments), default=Bump.NONE)
