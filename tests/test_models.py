import pytest

from changelog_fragments.models import Bump, Version


def test_parse_version_and_tag() -> None:
    version = Version.parse("v1.2.3")

    assert str(version) == "1.2.3"
    assert version.tag == "v1.2.3"


@pytest.mark.parametrize("value", ["1.2", "1.2.3.4", "1.2.x", "vv1.2.3", "01.2.3"])
def test_reject_invalid_version(value: str) -> None:
    with pytest.raises(ValueError, match="invalid stable semantic version"):
        Version.parse(value)


@pytest.mark.parametrize(
    ("bump", "expected"),
    [
        (Bump.NONE, "1.2.3"),
        (Bump.PATCH, "1.2.4"),
        (Bump.MINOR, "1.3.0"),
        (Bump.MAJOR, "2.0.0"),
    ],
)
def test_bump(bump: Bump, expected: str) -> None:
    assert str(Version(1, 2, 3).bump(bump)) == expected


def test_snapshot_version() -> None:
    assert Version(1, 3, 0).snapshot("ABC123") == "1.3.0+abc123"


@pytest.mark.parametrize("sha", ["", "not-a-sha"])
def test_reject_invalid_snapshot_sha(sha: str) -> None:
    with pytest.raises(ValueError, match="hexadecimal"):
        Version(1, 0, 0).snapshot(sha)
