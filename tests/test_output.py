from pathlib import Path

from changelog_fragments.models import Bump, Version
from changelog_fragments.output import emit, preview_comment, release_outputs
from changelog_fragments.release import Release


def test_outputs_and_comment(tmp_path: Path, capsys: object) -> None:
    release = Release(
        current=Version(1, 2, 3),
        next=Version(2, 0, 0),
        bump=Bump.MAJOR,
        snapshot="2.0.0+abc",
        fragments=(),
    )
    outputs = release_outputs(release, "# preview\n")
    comment = preview_comment(outputs)
    destination = tmp_path / "output"

    emit({**outputs, "comment": comment}, destination)

    assert "MAJOR" not in comment
    assert "breaking release" in comment
    assert "2.0.0+abc" in comment
    written = destination.read_text()
    assert "current_version<<" in written
    assert "changelog_preview<<" in written
    assert "# preview" in written
