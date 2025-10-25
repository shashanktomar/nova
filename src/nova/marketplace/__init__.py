"""Public API for Nova marketplace management."""

from __future__ import annotations

from .api import Marketplace
from .config import MarketplaceConfig
from .models import (
    BundleEntry,
    Contact,
    GitHubMarketplaceSource,
    GitMarketplaceSource,
    LocalMarketplaceSource,
    MarketplaceAddError,
    MarketplaceAlreadyExistsError,
    MarketplaceError,
    MarketplaceInfo,
    MarketplaceInvalidManifestError,
    MarketplaceNotFoundError,
    MarketplaceScope,
    MarketplaceSource,
    MarketplaceSourceType,
)
from .protocol import MarketplaceConfigProvider

__all__ = [
    "BundleEntry",
    "Contact",
    "GitHubMarketplaceSource",
    "GitMarketplaceSource",
    "LocalMarketplaceSource",
    "Marketplace",
    "MarketplaceAddError",
    "MarketplaceAlreadyExistsError",
    "MarketplaceConfig",
    "MarketplaceConfigProvider",
    "MarketplaceError",
    "MarketplaceInfo",
    "MarketplaceInvalidManifestError",
    "MarketplaceNotFoundError",
    "MarketplaceScope",
    "MarketplaceSource",
    "MarketplaceSourceType",
]
