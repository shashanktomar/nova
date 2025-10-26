"""Marketplace fetcher."""

from __future__ import annotations

from pathlib import Path

from nova.common import create_logger
from nova.marketplace.models import (
    GitHubMarketplaceSource,
    GitMarketplaceSource,
    LocalMarketplaceSource,
    MarketplaceFetchError,
    MarketplaceSource,
)
from nova.utils.functools.models import Ok, Result
from nova.utils.git import clone_repository

logger = create_logger("marketplace.fetcher")

type FetchResult = Result[Path, MarketplaceFetchError]


def fetch_marketplace(source: MarketplaceSource, destination: Path) -> FetchResult:
    match source:
        case GitHubMarketplaceSource():
            logger.debug("Fetching GitHub marketplace", repo=source.repo, destination=str(destination))
            return _fetch_github(source, destination)
        case GitMarketplaceSource():
            logger.debug("Fetching Git marketplace", url=source.url, destination=str(destination))
            return _fetch_git(source, destination)
        case LocalMarketplaceSource():
            logger.debug("Using local marketplace", path=str(source.path))
            return _fetch_local(source)


def _fetch_github(source: GitHubMarketplaceSource, destination: Path) -> FetchResult:
    github_url = f"https://github.com/{source.repo}.git"

    def log_success(path: Path) -> None:
        logger.debug("GitHub marketplace fetched successfully", repo=source.repo, path=str(path))

    def log_error(err: object) -> None:
        logger.error("Failed to fetch GitHub marketplace", repo=source.repo, error=str(err))

    return (
        clone_repository(github_url, destination)
        .inspect(log_success)
        .inspect_err(log_error)
        .map_err(lambda err: MarketplaceFetchError(source=source.repo, message=str(err)))
    )


def _fetch_git(source: GitMarketplaceSource, destination: Path) -> FetchResult:
    def log_success(path: Path) -> None:
        logger.debug("Git marketplace fetched successfully", url=source.url, path=str(path))

    def log_error(err: object) -> None:
        logger.error("Failed to fetch Git marketplace", url=source.url, error=str(err))

    return (
        clone_repository(source.url, destination)
        .inspect(log_success)
        .inspect_err(log_error)
        .map_err(lambda err: MarketplaceFetchError(source=source.url, message=str(err)))
    )


def _fetch_local(source: LocalMarketplaceSource) -> FetchResult:
    return Ok(source.path)
