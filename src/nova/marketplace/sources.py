"""Marketplace source parsing utilities."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from pydantic import ValidationError

from nova.utils.functools.models import Err, Ok, Result
from nova.utils.paths import resolve_working_directory
from nova.utils.validation import format_validation_error

from .models import (
    GitHubMarketplaceSource,
    GitMarketplaceSource,
    LocalMarketplaceSource,
    MarketplaceSource,
    MarketplaceSourceParseError,
)


def parse_source(
    source: str,
    *,
    working_dir: Path | None = None,
) -> Result[MarketplaceSource, MarketplaceSourceParseError]:
    """Parse raw source input into a typed MarketplaceSource."""
    normalized = source.strip()
    if not normalized:
        return Err(
            MarketplaceSourceParseError(
                message="Marketplace source cannot be empty.",
                source=source,
            )
        )

    base_dir = resolve_working_directory(working_dir)

    if result := _try_github_source(normalized, source):
        return result

    if result := _try_git_source(normalized, source):
        return result

    return _try_local_source(normalized, source, base_dir)


def _try_github_source(
    value: str,
    original: str,
) -> Result[MarketplaceSource, MarketplaceSourceParseError] | None:
    if not re.fullmatch(r"[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+", value):
        return None

    try:
        return Ok(GitHubMarketplaceSource(repo=value))
    except ValidationError as exc:
        return Err(
            MarketplaceSourceParseError(
                message=format_validation_error("GitHub repository", exc),
                source=original,
            )
        )


def _try_git_source(
    value: str,
    original: str,
) -> Result[MarketplaceSource, MarketplaceSourceParseError] | None:
    is_git = value.startswith(("git@", "git://")) or value.endswith(".git")
    if not is_git:
        parsed = urlparse(value)
        is_git = parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    if not is_git:
        return None

    try:
        return Ok(GitMarketplaceSource(url=value))
    except ValidationError as exc:
        return Err(
            MarketplaceSourceParseError(
                message=format_validation_error("git repository URL", exc),
                source=original,
            )
        )


def _try_local_source(
    value: str,
    original: str,
    base_dir: Path,
) -> Result[MarketplaceSource, MarketplaceSourceParseError]:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    else:
        path = path.resolve()

    try:
        return Ok(LocalMarketplaceSource(path=path))
    except ValidationError as exc:
        return Err(
            MarketplaceSourceParseError(
                message=format_validation_error("local marketplace path", exc),
                source=original,
            )
        )
