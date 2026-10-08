"""Human and GitHub Actions output formatting."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .release import Release


def release_outputs(release: Release, preview: str = "") -> dict[str, str]:
    """Create the stable output contract shared by all commands/actions."""
    return {
        "bump_type": str(release.bump),
        "current_version": str(release.current),
        "next_version": str(release.next),
        "snapshot_version": release.snapshot,
        "skip_release": str(not release.fragments).lower(),
        "changelog_preview": preview,
    }


def preview_comment(outputs: dict[str, str]) -> str:
    """Render the sticky PR release preview comment."""
    bump = outputs["bump_type"]
    warning = (
        "\n\n> ⚠️ Confirm that this breaking release is intentional." if bump == "major" else ""
    )
    preview = outputs["changelog_preview"].strip()
    changelog = f"\n\n**Changelog preview**\n\n{preview}" if preview else ""
    return (
        "<!-- changelog-fragments-preview -->\n"
        "### 📦 Release preview\n\n"
        "| | |\n"
        "|---|---|\n"
        f"| **Bump type** | {bump} |\n"
        f"| **Current version** | `{outputs['current_version']}` |\n"
        f"| **Next version** | `{outputs['next_version']}` |\n"
        f"| **Snapshot version** | `{outputs['snapshot_version']}` |"
        f"{warning}{changelog}\n"
    )


def emit(outputs: dict[str, Any], github_output: Path | None = None) -> None:
    """Print JSON and optionally append values to ``GITHUB_OUTPUT``."""
    print(json.dumps(outputs, indent=2, sort_keys=True))
    destination = github_output
    if destination is None and os.environ.get("GITHUB_OUTPUT"):
        destination = Path(os.environ["GITHUB_OUTPUT"])
    if destination is None:
        return
    with destination.open("a") as stream:
        for key, value in outputs.items():
            text = str(value)
            delimiter = f"changelog_fragments_{key}"
            while delimiter in text:
                delimiter += "_end"
            stream.write(f"{key}<<{delimiter}\n{text}\n{delimiter}\n")
