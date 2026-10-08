from datetime import date
from pathlib import Path

from changelog_fragments.changelog import prepend_release, render_release
from changelog_fragments.models import Bump, Fragment, Version


def fragment(kind: str, description: str, **kwargs: object) -> Fragment:
    bumps = {
        "feat": Bump.MINOR,
        "fix": Bump.PATCH,
        "chore": Bump.PATCH,
        "docs": Bump.MAJOR,
    }
    return Fragment(
        kind=kind,
        description=description,
        bump=bumps[kind],
        source=Path(f"CHANGELOG.d/{description}.md"),
        **kwargs,
    )


def test_render_release_is_grouped_sorted_and_linked() -> None:
    rendered = render_release(
        Version(1, 3, 0),
        [
            fragment("fix", "Zulu"),
            fragment(
                "feat",
                "Add search",
                scope="api",
                body="More detail.\n\n- Supports filters",
                pr_number=42,
                pr_url="https://github.com/acme/example/pull/42",
            ),
            fragment("fix", "alpha", pr_number=7),
            fragment("docs", "Rewrite guide"),
        ],
        date(2026, 10, 8),
    )

    assert rendered == (
        "# v1.3.0 - 2026-10-08\n\n"
        "## Features\n\n"
        "- **api:** Add search ([#42](https://github.com/acme/example/pull/42))\n"
        "  More detail.\n\n"
        "  - Supports filters\n\n"
        "## Fixes\n\n"
        "- alpha (#7)\n"
        "- Zulu\n\n"
        "## Docs\n\n"
        "- Rewrite guide\n"
    )


def test_prepend_release() -> None:
    assert prepend_release("# v1.0.0\n", "# v1.1.0\n") == "# v1.1.0\n\n# v1.0.0\n"
    assert prepend_release("", "# v1.0.0\n") == "# v1.0.0\n"
