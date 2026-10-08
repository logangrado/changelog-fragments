import json
import subprocess
import sys
from pathlib import Path

import pytest

from changelog_fragments.cli import main


@pytest.fixture(autouse=True)
def isolate_github_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep local CLI expectations independent of the CI runner environment."""
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)


def git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", *args), cwd=repository, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def invoke(monkeypatch: pytest.MonkeyPatch, arguments: list[str]) -> int:
    monkeypatch.setattr(sys, "argv", ["changelog-fragments", *arguments])
    with pytest.raises(SystemExit) as stopped:
        main()
    return int(stopped.value.code)


def repository(tmp_path: Path) -> tuple[Path, str]:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "user.email", "test@example.com")
    (tmp_path / "README.md").write_text("test")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "initial")
    git(tmp_path, "tag", "v1.2.3")
    return tmp_path, git(tmp_path, "rev-parse", "HEAD")


def test_preview_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: object) -> None:
    repo, base = repository(tmp_path)
    directory = repo / "CHANGELOG.d"
    directory.mkdir()
    (directory / "42.md").write_text("feat(api): add search")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "feat: add search (#42)")
    monkeypatch.chdir(repo)

    code = invoke(
        monkeypatch,
        [
            "preview",
            "--base-ref",
            base,
            "--pr-number",
            "42",
            "--repository-url",
            "https://github.com/acme/example",
        ],
    )

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["current_version"] == "1.2.3"
    assert payload["next_version"] == "1.3.0"
    assert payload["bump_type"] == "minor"
    assert payload["fragment"] == "CHANGELOG.d/42.md"
    assert "https://github.com/acme/example/pull/42" in payload["comment"]


def test_consolidate_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: object
) -> None:
    repo, _ = repository(tmp_path)
    directory = repo / "CHANGELOG.d"
    directory.mkdir()
    fragment = directory / "42.md"
    fragment.write_text("fix: repair parser")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "fix: repair parser (#42)")
    monkeypatch.chdir(repo)

    code = invoke(monkeypatch, ["consolidate", "--date", "2026-10-08"])

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["next_version"] == "1.2.4"
    assert not fragment.exists()
    assert (repo / "CHANGELOG.md").read_text() == (
        "# v1.2.4 - 2026-10-08\n\n## Fixes\n\n- repair parser (#42)\n"
    )


def test_preview_rejects_missing_fragment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: object
) -> None:
    repo, base = repository(tmp_path)
    (repo / "README.md").write_text("changed")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "docs: update")
    monkeypatch.chdir(repo)

    assert invoke(monkeypatch, ["preview", "--base-ref", base]) == 2
    assert "must add exactly one" in capsys.readouterr().err
