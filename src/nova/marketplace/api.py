"""Public API class for Nova marketplace management."""

from __future__ import annotations

from pathlib import Path

from nova.utils.functools.models import Result

from .models import MarketplaceError, MarketplaceInfo, MarketplaceScope
from .protocol import MarketplaceConfigProvider


class Marketplace:
    """Marketplace management API."""

    def __init__(self, config_provider: MarketplaceConfigProvider) -> None:
        """Initialize with a marketplace configuration provider."""
        self._config_provider = config_provider

    def add(
        self,
        source: str,
        *,
        scope: MarketplaceScope,
        working_dir: Path | None = None,
    ) -> Result[MarketplaceInfo, MarketplaceError]:
        """Add a marketplace source.

        Flow:
        1. Parse the source string into a typed MarketplaceSource (github/git/local/url)
        2. Fetch or clone the marketplace repository to local data directory
        3. Read and validate marketplace.json from the cloned location
        4. Extract marketplace name from marketplace.json
        5. Get current marketplace config from all scopes via config provider
        6. Check if marketplace with same name already exists (error if duplicate)
        7. Write marketplace metadata to data.json (install location, last updated)
        8. Add marketplace entry to appropriate config file (global or project config.yaml)
        9. Return MarketplaceInfo with marketplace details
        """
        raise NotImplementedError

    def remove(
        self,
        name_or_source: str,
        *,
        scope: MarketplaceScope | None = None,
        working_dir: Path | None = None,
    ) -> Result[MarketplaceInfo, MarketplaceError]:
        """Remove a marketplace by name or source."""
        raise NotImplementedError

    def list(
        self,
        *,
        working_dir: Path | None = None,
    ) -> Result[list[MarketplaceInfo], MarketplaceError]:
        """List all configured marketplaces."""
        raise NotImplementedError

    def get(
        self,
        name: str,
        *,
        working_dir: Path | None = None,
    ) -> Result[MarketplaceInfo, MarketplaceError]:
        """Get details for a specific marketplace."""
        raise NotImplementedError
