"""Public API class for Nova marketplace management."""

from __future__ import annotations

import tempfile
from pathlib import Path

from nova.utils.functools.models import Result, is_err

from .fetcher import fetch_marketplace
from .models import (
    LocalMarketplaceSource,
    MarketplaceError,
    MarketplaceInfo,
    MarketplaceScope,
)
from .protocol import MarketplaceConfigProvider
from .sources import parse_source
from .validator import validate_marketplace


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
        parsed_source = parse_source(source, working_dir=working_dir)
        if is_err(parsed_source):
            return parsed_source

        marketplace_source = parsed_source.unwrap()

        if isinstance(marketplace_source, LocalMarketplaceSource):
            marketplace_dir = marketplace_source.path
        else:
            temp_dir = Path(tempfile.mkdtemp(prefix="nova-marketplace-"))
            fetch_result = fetch_marketplace(marketplace_source, temp_dir)
            if is_err(fetch_result):
                return fetch_result
            marketplace_dir = fetch_result.unwrap()

        manifest_result = validate_marketplace(marketplace_dir)
        if is_err(manifest_result):
            return manifest_result

        _manifest = manifest_result.unwrap()

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
