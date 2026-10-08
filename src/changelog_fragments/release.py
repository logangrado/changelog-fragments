"""Release calculation helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .fragments import highest_bump
from .models import Bump, Fragment, Version


@dataclass(frozen=True)
class Release:
    """Versions and fragments associated with a release calculation."""

    current: Version
    next: Version
    bump: Bump
    snapshot: str
    fragments: tuple[Fragment, ...]


def calculate_release(current: Version, fragments: Iterable[Fragment], sha: str) -> Release:
    """Calculate version outputs from all pending fragments."""
    materialized = tuple(fragments)
    bump = highest_bump(materialized)
    next_version = current.bump(bump)
    return Release(
        current=current,
        next=next_version,
        bump=bump,
        snapshot=next_version.snapshot(sha),
        fragments=materialized,
    )
