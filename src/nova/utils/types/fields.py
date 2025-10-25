"""Reusable Pydantic field annotations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, TypeVar

from pydantic import Field, HttpUrl, StrictStr

type JsonValue = dict[str, object] | list[object] | str | int | float | bool | None
type JsonDict = dict[str, object]

NonEmptyString = Annotated[StrictStr, Field(min_length=1, frozen=True)]

T = TypeVar("T")
NonEmptySequence = Annotated[Sequence[T], Field(min_length=1)]

# GitHub repository identifier (e.g., "owner/repo")
GitHubRepo = Annotated[
    StrictStr,
    Field(
        pattern=r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$",
        frozen=True,
        description="GitHub repository in 'owner/repo' format",
    ),
]

# Git URL (https or git protocol)
GitUrl = Annotated[
    StrictStr,
    Field(
        pattern=r"^(https?://|git@|git://)",
        frozen=True,
        description="Git repository URL",
    ),
]

# HTTP/HTTPS URL for direct file access
DirectUrl = Annotated[
    HttpUrl,
    Field(
        frozen=True,
        description="Direct HTTP/HTTPS URL",
    ),
]

__all__ = [
    "DirectUrl",
    "GitHubRepo",
    "GitUrl",
    "JsonDict",
    "JsonValue",
    "NonEmptySequence",
    "NonEmptyString",
]
