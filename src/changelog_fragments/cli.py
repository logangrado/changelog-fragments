"""Command-line interface for changelog-fragments."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

from .changelog import prepend_release, render_release
from .fragments import FragmentError, discover_fragments, parse_fragment, validate_pr_changes
from .git import changed_files, file_at, latest_version, resolve_sha
from .github import attach_pull_request, upsert_preview_comment
from .output import emit, preview_comment, release_outputs
from .release import calculate_release


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--fragment-dir", type=Path, default=Path("CHANGELOG.d"))
    parser.add_argument("--sha", help="snapshot SHA; defaults to the selected Git ref")
    parser.add_argument("--github-output", type=Path)


def _preview(arguments: argparse.Namespace) -> int:
    changes = changed_files(arguments.base_ref, arguments.head_ref)
    path = validate_pr_changes(changes, arguments.fragment_dir)
    fragment = parse_fragment(file_at(arguments.head_ref, path), path)
    if arguments.pr_number:
        repository_url = arguments.repository_url.rstrip("/") if arguments.repository_url else None
        fragment = replace(
            fragment,
            pr_number=arguments.pr_number,
            pr_url=f"{repository_url}/pull/{arguments.pr_number}" if repository_url else None,
        )
    sha = arguments.sha or resolve_sha(arguments.head_ref)
    release = calculate_release(latest_version(), [fragment], sha)
    rendered = render_release(release.next, release.fragments, date.today())
    outputs = release_outputs(release, rendered)
    outputs["fragment"] = path.as_posix()
    outputs["comment"] = preview_comment(outputs)
    emit(outputs, arguments.github_output)
    if arguments.post_comment:
        repository = arguments.repository or os.environ.get("GITHUB_REPOSITORY")
        if not repository or not arguments.pr_number:
            raise ValueError("--post-comment requires --repository and --pr-number")
        upsert_preview_comment(repository, arguments.pr_number, outputs["comment"])
    return 0


def _consolidate(arguments: argparse.Namespace) -> int:
    fragments = discover_fragments(arguments.fragment_dir)
    repository = arguments.repository or os.environ.get("GITHUB_REPOSITORY")
    fragments = [attach_pull_request(fragment, repository) for fragment in fragments]
    sha = arguments.sha or resolve_sha()
    release = calculate_release(latest_version(), fragments, sha)
    rendered = (
        render_release(release.next, release.fragments, arguments.date) if release.fragments else ""
    )
    outputs = release_outputs(release, rendered)

    if release.fragments:
        existing = arguments.changelog.read_text() if arguments.changelog.exists() else ""
        arguments.changelog.write_text(prepend_release(existing, rendered))
        for fragment in release.fragments:
            fragment.source.unlink()

    emit(outputs, arguments.github_output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the public command-line parser."""
    parser = argparse.ArgumentParser(prog="changelog-fragments")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preview = subparsers.add_parser("preview", help="validate and preview a pull request")
    _add_common(preview)
    preview.add_argument("--base-ref", required=True)
    preview.add_argument("--head-ref", default="HEAD")
    preview.add_argument("--pr-number", type=int)
    preview.add_argument("--repository", help="GitHub owner/repository")
    preview.add_argument("--repository-url")
    preview.add_argument("--post-comment", action="store_true")
    preview.set_defaults(handler=_preview)

    consolidate = subparsers.add_parser(
        "consolidate", help="consolidate all pending fragments into CHANGELOG.md"
    )
    _add_common(consolidate)
    consolidate.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    consolidate.add_argument("--repository", help="GitHub owner/repository")
    consolidate.add_argument("--date", type=date.fromisoformat, default=date.today())
    consolidate.set_defaults(handler=_consolidate)
    return parser


def main() -> None:
    """Run the command-line interface."""
    try:
        arguments = build_parser().parse_args()
        raise SystemExit(arguments.handler(arguments))
    except (FragmentError, ValueError, OSError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
