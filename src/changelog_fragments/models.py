"""Core release domain models."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import ClassVar


class Bump(IntEnum):
    """Semantic-version bump ordered by precedence."""

    NONE = 0
    PATCH = 1
    MINOR = 2
    MAJOR = 3

    def __str__(self) -> str:
        return self.name.lower()


@dataclass(frozen=True)
class FileChange:
    """A changed path and its Git status."""

    status: str
    path: Path


@dataclass(frozen=True)
class Fragment:
    """A parsed changelog fragment."""

    kind: str
    description: str
    bump: Bump
    source: Path
    scope: str | None = None
    body: str = ""
    pr_number: int | None = None
    pr_url: str | None = None


@dataclass(frozen=True, order=True)
class Version:
    """A stable semantic version."""

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$"
    )

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> Version:
        """Parse ``X.Y.Z`` or a version tag named ``vX.Y.Z``."""
        raw = value.removeprefix("v")
        if cls._PATTERN.fullmatch(raw) is None:
            raise ValueError(f"invalid stable semantic version: {value!r}")
        return cls(*(int(part) for part in raw.split(".")))

    def bump(self, bump: Bump) -> Version:
        """Return a version with the requested bump applied."""
        if bump is Bump.MAJOR:
            return Version(self.major + 1, 0, 0)
        if bump is Bump.MINOR:
            return Version(self.major, self.minor + 1, 0)
        if bump is Bump.PATCH:
            return Version(self.major, self.minor, self.patch + 1)
        return self

    @property
    def tag(self) -> str:
        return f"v{self}"

    def snapshot(self, sha: str) -> str:
        """Return a PEP 440/SemVer-compatible build version for a Git SHA."""
        normalized = sha.strip().lower()
        if not normalized or any(character not in "0123456789abcdef" for character in normalized):
            raise ValueError("snapshot SHA must contain hexadecimal characters only")
        return f"{self}+{normalized}"

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
