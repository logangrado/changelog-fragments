"""GitHub metadata helpers backed by the GitHub CLI."""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace

from .git import introducing_commit, pr_number_from_subject
from .models import Fragment

_PREVIEW_MARKER = "<!-- changelog-fragments-preview -->"


def _run_gh(*arguments: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("gh", *arguments),
        check=False,
        capture_output=True,
        text=True,
        input=input_text,
    )


def _pull_request_for_commit(repository: str, sha: str) -> tuple[int, str] | None:
    result = _run_gh("api", f"repos/{repository}/commits/{sha}/pulls")
    if result.returncode != 0:
        return None
    pulls = json.loads(result.stdout)
    if not pulls:
        return None
    return int(pulls[0]["number"]), str(pulls[0]["html_url"])


def attach_pull_request(fragment: Fragment, repository: str | None) -> Fragment:
    """Attach the PR that introduced a fragment, with an offline Git fallback."""
    introduced = introducing_commit(fragment.source)
    if introduced is None:
        return fragment
    sha, subject = introduced
    pull_request = _pull_request_for_commit(repository, sha) if repository else None
    if pull_request:
        number, url = pull_request
        return replace(fragment, pr_number=number, pr_url=url)
    if number := pr_number_from_subject(subject):
        url = f"https://github.com/{repository}/pull/{number}" if repository else None
        return replace(fragment, pr_number=number, pr_url=url)
    return fragment


def upsert_preview_comment(repository: str, pr_number: int, body: str) -> None:
    """Create or update this tool's sticky pull-request comment."""
    comments = _run_gh("api", f"repos/{repository}/issues/{pr_number}/comments")
    if comments.returncode != 0:
        raise RuntimeError(comments.stderr.strip() or "could not list pull-request comments")
    comment_id = next(
        (
            comment["id"]
            for comment in json.loads(comments.stdout)
            if str(comment.get("body", "")).startswith(_PREVIEW_MARKER)
        ),
        None,
    )
    endpoint = (
        f"repos/{repository}/issues/comments/{comment_id}"
        if comment_id is not None
        else f"repos/{repository}/issues/{pr_number}/comments"
    )
    method = "PATCH" if comment_id is not None else "POST"
    result = _run_gh(
        "api",
        endpoint,
        "--method",
        method,
        "--input",
        "-",
        input_text=json.dumps({"body": body}),
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "could not write pull-request comment")
