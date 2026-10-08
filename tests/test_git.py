import subprocess
from pathlib import Path

from changelog_fragments.git import latest_version, pr_number_from_subject
from changelog_fragments.models import Version


def git(repository: Path, *args: str) -> None:
    subprocess.run(("git", *args), cwd=repository, check=True, capture_output=True)


def test_latest_stable_version(tmp_path: Path, monkeypatch: object) -> None:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "user.email", "test@example.com")
    (tmp_path / "README.md").write_text("test")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "initial")
    for tag in ("v1.9.0", "v1.10.0", "v2.0.0-rc1", "other"):
        git(tmp_path, "tag", tag)
    monkeypatch.chdir(tmp_path)

    assert latest_version() == Version(1, 10, 0)


def test_extract_pr_number() -> None:
    assert pr_number_from_subject("feat: add it (#123)") == 123
    assert pr_number_from_subject("Merge pull request #9 from acme/topic") == 9
    assert pr_number_from_subject("direct commit") is None
