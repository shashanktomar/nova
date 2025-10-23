"""Public API for Nova marketplace management."""

from __future__ import annotations

from pathlib import Path

from nova.utils.functools.models import Result

from .models import (
    BundleEntry,
    Contact,
    GitHubMarketplaceSource,
    GitMarketplaceSource,
    LocalMarketplaceSource,
    MarketplaceAddError,
    MarketplaceAlreadyExistsError,
    MarketplaceErrorType,
    MarketplaceInfo,
    MarketplaceInvalidManifestError,
    MarketplaceNotFoundError,
    MarketplaceScope,
    MarketplaceSource,
    MarketplaceSourceType,
    URLMarketplaceSource,
)

__all__ = [
    "BundleEntry",
    "Contact",
    "GitHubMarketplaceSource",
    "GitMarketplaceSource",
    "LocalMarketplaceSource",
    "MarketplaceAddError",
    "MarketplaceAlreadyExistsError",
    "MarketplaceErrorType",
    "MarketplaceInfo",
    "MarketplaceInvalidManifestError",
    "MarketplaceNotFoundError",
    "MarketplaceScope",
    "MarketplaceSource",
    "MarketplaceSourceType",
    "URLMarketplaceSource",
    "add_marketplace",
    "get_marketplace",
    "list_marketplaces",
    "remove_marketplace",
]


def add_marketplace(
    source: str,
    *,
    scope: MarketplaceScope,
    working_dir: Path | None = None,
) -> Result[MarketplaceInfo, MarketplaceErrorType]:
    """Add a marketplace source."""
    raise NotImplementedError


def remove_marketplace(
    name_or_source: str,
    *,
    scope: MarketplaceScope | None = None,
    working_dir: Path | None = None,
) -> Result[MarketplaceInfo, MarketplaceErrorType]:
    """Remove a marketplace by name or source."""
    raise NotImplementedError


def list_marketplaces(
    *,
    working_dir: Path | None = None,
) -> Result[list[MarketplaceInfo], MarketplaceErrorType]:
    """List configured marketplaces."""
    raise NotImplementedError


def get_marketplace(
    name: str,
    *,
    working_dir: Path | None = None,
) -> Result[MarketplaceInfo, MarketplaceErrorType]:
    """Get details for a specific marketplace."""
    raise NotImplementedError

