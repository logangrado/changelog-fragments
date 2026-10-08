"""Deterministic Markdown changelog rendering."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date

from .models import Fragment, Version

_SECTION_TITLES = {
    "feat": "Features",
    "fix": "Fixes",
    "perf": "Performance",
    "refactor": "Refactors",
    "revert": "Reverts",
    "test": "Tests",
    "chore": "Chores",
}
_SECTION_ORDER = tuple(_SECTION_TITLES)


def render_release(version: Version, fragments: Iterable[Fragment], released_on: date) -> str:
    """Render one release section, grouping entries by conventional type."""
    grouped: dict[str, list[Fragment]] = defaultdict(list)
    for fragment in fragments:
        grouped[fragment.kind].append(fragment)

    lines = [f"# {version.tag} - {released_on.isoformat()}"]
    for kind in _SECTION_ORDER:
        entries = grouped.get(kind, [])
        if not entries:
            continue
        lines.extend(("", f"## {_SECTION_TITLES[kind]}", ""))
        for fragment in sorted(entries, key=lambda item: (item.description.lower(), item.source)):
            scope = f"**{fragment.scope}:** " if fragment.scope else ""
            link = ""
            if fragment.pr_number is not None and fragment.pr_url:
                link = f" ([#{fragment.pr_number}]({fragment.pr_url}))"
            elif fragment.pr_number is not None:
                link = f" (#{fragment.pr_number})"
            lines.append(f"- {scope}{fragment.description}{link}")
            if fragment.body:
                lines.extend(f"  {line}" if line else "" for line in fragment.body.splitlines())
    return "\n".join(lines).rstrip() + "\n"


def prepend_release(existing: str, release: str) -> str:
    """Prepend a release while preserving older changelog text."""
    return release.rstrip() + ("\n\n" + existing.lstrip() if existing.strip() else "\n")
