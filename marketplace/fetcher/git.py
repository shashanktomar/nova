"""Git repository marketplace fetcher."""

from __future__ import annotations

from pathlib import Path

from nova.marketplace.models import GitHubMarketplaceSource, GitMarketplaceSource
from nova.utils.git import clone_repository

from .protocol import FetchError, FetchResult


def fetch_github(source: GitHubMarketplaceSource, destination: Path) -> FetchResult:
    """Fetch marketplace from GitHub repository."""
    github_url = f"https://github.com/{source.repo}.git"
    result = clone_repository(github_url, destination)

    return result.map_err(lambda err: FetchError(err))


def fetch_git(source: GitMarketplaceSource, destination: Path) -> FetchResult:
    """Fetch marketplace from generic git repository."""
    result = clone_repository(source.url, destination)

    return result.map_err(lambda err: FetchError(err))
