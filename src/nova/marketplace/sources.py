"""Marketplace source parsing utilities."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

from pydantic import ValidationError

from nova.common import create_logger, resolve_working_directory
from nova.utils.format import format_validation_error
from nova.utils.functools.models import Err, Ok, Result
from nova.utils.git import clone_repository

from .models import (
    GitHubMarketplaceSource,
    GitMarketplaceSource,
    LocalMarketplaceSource,
    MarketplaceFetchError,
    MarketplaceSource,
    MarketplaceSourceParseError,
)
from .protocol import MarketplaceSourceProvider

logger = create_logger("marketplace.sources")


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


def create_source_provider(source: MarketplaceSource) -> MarketplaceSourceProvider:
    """Create appropriate source provider for the given source."""
    match source:
        case GitHubMarketplaceSource():
            return GitHubSourceProvider(source)
        case GitMarketplaceSource():
            return GitSourceProvider(source)
        case LocalMarketplaceSource():
            return LocalSourceProvider(source)


class GitHubSourceProvider:
    """GitHub marketplace source provider."""

    def __init__(self, source: GitHubMarketplaceSource) -> None:
        self._source = source

    def fetch(self, destination: Path) -> Result[Path, MarketplaceFetchError]:
        github_url = f"https://github.com/{self._source.repo}.git"
        logger.debug("Fetching GitHub marketplace", repo=self._source.repo, destination=str(destination))

        return clone_repository(github_url, destination).map_err(
            lambda err: MarketplaceFetchError(source=self._source.repo, message=str(err))
        )

    def move_to_storage(self, temp_path: Path, final_path: Path) -> Path:
        final_path.parent.mkdir(parents=True, exist_ok=True)

        if final_path.exists():
            shutil.rmtree(final_path)

        shutil.move(str(temp_path), str(final_path))
        return final_path

    def cleanup_on_removal(self, install_location: Path) -> None:
        if install_location.exists():
            shutil.rmtree(install_location)

    def display_name(self) -> str:
        return self._source.repo


class GitSourceProvider:
    """Git repository marketplace source provider."""

    def __init__(self, source: GitMarketplaceSource) -> None:
        self._source = source

    def fetch(self, destination: Path) -> Result[Path, MarketplaceFetchError]:
        logger.debug("Fetching Git marketplace", url=self._source.url, destination=str(destination))

        return clone_repository(self._source.url, destination).map_err(
            lambda err: MarketplaceFetchError(source=self._source.url, message=str(err))
        )

    def move_to_storage(self, temp_path: Path, final_path: Path) -> Path:
        final_path.parent.mkdir(parents=True, exist_ok=True)

        if final_path.exists():
            shutil.rmtree(final_path)

        shutil.move(str(temp_path), str(final_path))
        return final_path

    def cleanup_on_removal(self, install_location: Path) -> None:
        if install_location.exists():
            shutil.rmtree(install_location)

    def display_name(self) -> str:
        return self._source.url


class LocalSourceProvider:
    """Local filesystem marketplace source provider."""

    def __init__(self, source: LocalMarketplaceSource) -> None:
        self._source = source

    def fetch(self, destination: Path) -> Result[Path, MarketplaceFetchError]:
        logger.debug("Using local marketplace", path=str(self._source.path))
        return Ok(self._source.path)

    def move_to_storage(self, temp_path: Path, final_path: Path) -> Path:
        return temp_path

    def cleanup_on_removal(self, install_location: Path) -> None:
        pass

    def display_name(self) -> str:
        return str(self._source.path)


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
