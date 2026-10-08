import json
import subprocess

import pytest

from changelog_fragments import github


def completed(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(("gh",), returncode, stdout, "failure")


def test_create_preview_comment(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[tuple[str, ...], str | None]] = []
    responses = iter((completed("[]"), completed("{}")))

    def fake_run(
        *arguments: str, input_text: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        calls.append((arguments, input_text))
        return next(responses)

    monkeypatch.setattr(github, "_run_gh", fake_run)
    github.upsert_preview_comment("acme/example", 42, "<!-- changelog-fragments-preview -->\nHi")

    assert calls[1][0] == (
        "api",
        "repos/acme/example/issues/42/comments",
        "--method",
        "POST",
        "--input",
        "-",
    )
    assert json.loads(calls[1][1] or "") == {"body": "<!-- changelog-fragments-preview -->\nHi"}


def test_update_preview_comment(monkeypatch: pytest.MonkeyPatch) -> None:
    comments = json.dumps([{"id": 99, "body": "<!-- changelog-fragments-preview -->\nOld"}])
    responses = iter((completed(comments), completed("{}")))
    calls: list[tuple[str, ...]] = []

    def fake_run(
        *arguments: str, input_text: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        calls.append(arguments)
        return next(responses)

    monkeypatch.setattr(github, "_run_gh", fake_run)
    github.upsert_preview_comment("acme/example", 42, "new")

    assert calls[1][1] == "repos/acme/example/issues/comments/99"
    assert "PATCH" in calls[1]
