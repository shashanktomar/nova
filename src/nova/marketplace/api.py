"""Public API class for Nova marketplace management."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from nova.utils.functools.models import Err, Ok, Result, is_err
from nova.utils.paths import PathsConfig, get_data_directory

from .fetcher import fetch_marketplace
from .models import (
    LocalMarketplaceSource,
    MarketplaceAlreadyExistsError,
    MarketplaceError,
    MarketplaceInfo,
    MarketplaceScope,
    MarketplaceSource,
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
        1. ~~Parse the source string into a typed MarketplaceSource (github/git/local/url)~~ ✅
        2. ~~Fetch or clone the marketplace repository to temp directory~~ ✅
        3. ~~Read and validate marketplace.json from the cloned location~~ ✅
        4. ~~Extract marketplace name from marketplace.json~~ ✅
        5. ~~Get current marketplace config from all scopes via config provider~~ ✅
        6. ~~Check if marketplace with same name already exists (error if duplicate)~~ ✅
        7. ~~Move cloned marketplace from temp to final data directory location~~ ✅
        8. Write marketplace metadata to data.json (install location, last updated)
        9. Add marketplace entry to appropriate config file (global or project config.yaml)
        10. Return MarketplaceInfo with marketplace details
        """
        return (
            parse_source(source, working_dir=working_dir)
            .and_then(self._fetch_marketplace_to_temp)
            .and_then(self._validate_and_extract_manifest)
            .and_then(self._check_for_duplicate_name)
            .and_then(self._move_to_final_location)
            .map(self._build_marketplace_info)
        )

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

    def _fetch_marketplace_to_temp(
        self,
        source: MarketplaceSource,
    ) -> Result[tuple[MarketplaceSource, Path], MarketplaceError]:
        if isinstance(source, LocalMarketplaceSource):
            return Ok((source, source.path))

        temp_dir = Path(tempfile.mkdtemp(prefix="nova-marketplace-"))
        return fetch_marketplace(source, temp_dir).map(lambda path: (source, path))

    def _validate_and_extract_manifest(
        self,
        data: tuple[MarketplaceSource, Path],
    ) -> Result[tuple[MarketplaceSource, Path, str], MarketplaceError]:
        source, marketplace_dir = data
        return validate_marketplace(marketplace_dir).map(lambda manifest: (source, marketplace_dir, manifest.name))

    def _check_for_duplicate_name(
        self,
        data: tuple[MarketplaceSource, Path, str],
    ) -> Result[tuple[MarketplaceSource, Path, str], MarketplaceError]:
        source, marketplace_dir, marketplace_name = data

        config_result = self._config_provider.get_marketplace_config()
        if is_err(config_result):
            return config_result

        existing_marketplaces = config_result.unwrap()

        if any(m.name == marketplace_name for m in existing_marketplaces):
            return Err(
                MarketplaceAlreadyExistsError(
                    name=marketplace_name,
                    existing_source="",
                    message=f"Marketplace '{marketplace_name}' already exists",
                )
            )

        return Ok((source, marketplace_dir, marketplace_name))

    def _move_to_final_location(
        self,
        data: tuple[MarketplaceSource, Path, str],
    ) -> Result[tuple[MarketplaceSource, Path, str], MarketplaceError]:
        source, marketplace_dir, marketplace_name = data
        final_location = self._move_to_data_directory(source, marketplace_dir, marketplace_name)
        return Ok((source, final_location, marketplace_name))

    def _move_to_data_directory(
        self,
        marketplace_source: MarketplaceSource,
        temp_dir: Path,
        marketplace_name: str,
    ) -> Path:
        if isinstance(marketplace_source, LocalMarketplaceSource):
            return temp_dir

        config = PathsConfig(config_dir_name="nova", project_subdir_name=".nova")
        data_dir = get_data_directory(config)
        marketplaces_dir = data_dir / "marketplaces"
        final_location = marketplaces_dir / marketplace_name

        marketplaces_dir.mkdir(parents=True, exist_ok=True)

        if final_location.exists():
            shutil.rmtree(final_location)

        shutil.move(str(temp_dir), str(final_location))

        return final_location

    def _build_marketplace_info(
        self,
        data: tuple[MarketplaceSource, Path, str],
    ) -> MarketplaceInfo:
        source, final_location, marketplace_name = data
        manifest_path = final_location / "marketplace.json"
        manifest_data = json.loads(manifest_path.read_text())
        bundle_count = len(manifest_data.get("bundles", []))

        return MarketplaceInfo(
            name=marketplace_name,
            description=manifest_data.get("description", ""),
            source=source,
            bundle_count=bundle_count,
        )
