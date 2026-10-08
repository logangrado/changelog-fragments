from pathlib import Path

import pytest

from changelog_fragments.fragments import (
    FragmentError,
    discover_fragments,
    highest_bump,
    parse_fragment,
    validate_pr_changes,
)
from changelog_fragments.models import Bump, FileChange


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("fix: repair parsing", Bump.PATCH),
        ("refactor(core): simplify parser", Bump.PATCH),
        ("chore: update tooling", Bump.PATCH),
        ("feat(api): add endpoint", Bump.MINOR),
        ("feat!: replace API", Bump.MAJOR),
        ("docs(readme)!: rewrite everything", Bump.MAJOR),
    ],
)
def test_parse_bump(header: str, expected: Bump) -> None:
    assert parse_fragment(header).bump is expected


def test_parse_fragment_fields_and_body() -> None:
    fragment = parse_fragment(
        "\nfeat(search): add fuzzy matching\n\nSupports typo tolerance.\n", "CHANGELOG.d/42.md"
    )

    assert fragment.kind == "feat"
    assert fragment.scope == "search"
    assert fragment.description == "add fuzzy matching"
    assert fragment.body == "Supports typo tolerance."
    assert fragment.source == Path("CHANGELOG.d/42.md")


@pytest.mark.parametrize("content", ["", "hello", "docs: update readme"])
def test_reject_invalid_fragment(content: str) -> None:
    with pytest.raises(FragmentError):
        parse_fragment(content)


def test_validate_single_added_fragment() -> None:
    path = validate_pr_changes(
        [
            FileChange("M", Path("src/app.py")),
            FileChange("A", Path("CHANGELOG.d/42.md")),
        ]
    )

    assert path == Path("CHANGELOG.d/42.md")


@pytest.mark.parametrize(
    "changes",
    [
        [],
        [FileChange("M", Path("CHANGELOG.d/existing.md"))],
        [FileChange("A", Path("CHANGELOG.d/one.md")), FileChange("A", Path("CHANGELOG.d/two.md"))],
        [FileChange("A", Path("CHANGELOG.d/note.txt"))],
    ],
)
def test_reject_invalid_pr_changes(changes: list[FileChange]) -> None:
    with pytest.raises(FragmentError):
        validate_pr_changes(changes)


def test_discover_sorted_fragments_and_highest_bump(tmp_path: Path) -> None:
    directory = tmp_path / "CHANGELOG.d"
    directory.mkdir()
    (directory / "b.md").write_text("fix: second")
    (directory / "a.md").write_text("feat: first")
    (directory / "ignored.txt").write_text("feat!: ignored")

    fragments = discover_fragments(directory)

    assert [fragment.source.name for fragment in fragments] == ["a.md", "b.md"]
    assert highest_bump(fragments) is Bump.MINOR
