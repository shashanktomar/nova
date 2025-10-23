"""Marketplace fetcher."""

from __future__ import annotations

from pathlib import Path

from nova.marketplace.models import (
    GitHubMarketplaceSource,
    GitMarketplaceSource,
    LocalMarketplaceSource,
    MarketplaceFetchError,
    MarketplaceSource,
)
from nova.utils.functools.models import Ok, Result
from nova.utils.git import clone_repository

type FetchResult = Result[Path, MarketplaceFetchError]


def fetch_marketplace(source: MarketplaceSource, destination: Path) -> FetchResult:
    match source:
        case GitHubMarketplaceSource():
            return _fetch_github(source, destination)
        case GitMarketplaceSource():
            return _fetch_git(source, destination)
        case LocalMarketplaceSource():
            return _fetch_local(source)


def _fetch_github(source: GitHubMarketplaceSource, destination: Path) -> FetchResult:
    github_url = f"https://github.com/{source.repo}.git"
    result = clone_repository(github_url, destination)

    return result.map_err(
        lambda err: MarketplaceFetchError(source=source.repo, message=err.message)
    )


def _fetch_git(source: GitMarketplaceSource, destination: Path) -> FetchResult:
    result = clone_repository(source.url, destination)

    return result.map_err(
        lambda err: MarketplaceFetchError(source=source.url, message=err.message)
    )


def _fetch_local(source: LocalMarketplaceSource) -> FetchResult:
    return Ok(source.path)
