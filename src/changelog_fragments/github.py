"""GitHub metadata helpers backed by the GitHub CLI."""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace

from .git import introducing_commit, pr_number_from_subject
from .models import Fragment


def _pull_request_for_commit(repository: str, sha: str) -> tuple[int, str] | None:
    result = subprocess.run(
        ("gh", "api", f"repos/{repository}/commits/{sha}/pulls"),
        check=False,
        capture_output=True,
        text=True,
    )
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
