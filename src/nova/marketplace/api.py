"""Public API class for Nova marketplace management."""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

from nova.datastore import DataStore
from nova.utils.functools.models import Err, Ok, Result, is_err
from nova.utils.paths import PathsConfig, get_data_directory

from .config import MarketplaceConfig
from .fetcher import fetch_marketplace
from .models import (
    LocalMarketplaceSource,
    MarketplaceAddError,
    MarketplaceAlreadyExistsError,
    MarketplaceError,
    MarketplaceInfo,
    MarketplaceScope,
    MarketplaceSource,
    MarketplaceState,
)
from .protocol import MarketplaceConfigProvider
from .sources import parse_source
from .validator import validate_marketplace


class Marketplace:
    """Marketplace management API."""

    def __init__(self, config_provider: MarketplaceConfigProvider, datastore: DataStore) -> None:
        """Initialize with a marketplace configuration provider and datastore."""
        self._config_provider = config_provider
        self._datastore = datastore

    def add(
        self,
        source: str,
        *,
        scope: MarketplaceScope,
        working_dir: Path | None = None,
    ) -> Result[MarketplaceInfo, MarketplaceError]:
        save_to_config = partial(self._save_to_config, scope=scope)

        return (
            parse_source(source, working_dir=working_dir)
            .and_then(self._fetch_marketplace_to_temp)
            .and_then(self._validate_and_extract_manifest)
            .and_then(self._check_for_duplicate)
            .and_then(self._move_to_final_location)
            .and_then(self._save_marketplace_state)
            .and_then(save_to_config)
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

    def _check_for_duplicate(
        self,
        data: tuple[MarketplaceSource, Path, str],
    ) -> Result[tuple[MarketplaceSource, Path, str], MarketplaceError]:
        source, marketplace_dir, marketplace_name = data

        has_marketplace_result = self._config_provider.has_marketplace(marketplace_name, source)
        if is_err(has_marketplace_result):
            return has_marketplace_result

        if has_marketplace_result.unwrap():
            return Err(
                MarketplaceAlreadyExistsError(
                    name=marketplace_name,
                    existing_source=str(source),
                    message=f"Marketplace with name '{marketplace_name}' or source '{source}' already exists",
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

    def _save_marketplace_state(
        self,
        data: tuple[MarketplaceSource, Path, str],
    ) -> Result[tuple[MarketplaceSource, Path, str], MarketplaceError]:
        source, final_location, marketplace_name = data

        state = MarketplaceState(
            name=marketplace_name,
            source=source,
            install_location=final_location,
            last_updated=datetime.now(UTC).isoformat(),
        )

        save_result = self._datastore.save(marketplace_name, state.model_dump(mode="json"))
        if is_err(save_result):
            return Err(
                MarketplaceAddError(
                    source=str(source),
                    message=f"Failed to save marketplace state: {save_result.unwrap_err().message}",
                )
            )

        return Ok((source, final_location, marketplace_name))

    def _save_to_config(
        self,
        data: tuple[MarketplaceSource, Path, str],
        scope: MarketplaceScope,
    ) -> Result[tuple[MarketplaceSource, Path, str], MarketplaceError]:
        source, final_location, marketplace_name = data

        config = MarketplaceConfig(name=marketplace_name, source=source)
        save_result = self._config_provider.add_marketplace(config, scope)

        if is_err(save_result):
            return Err(
                MarketplaceAddError(
                    source=str(source),
                    message=f"Failed to save marketplace config: {save_result.unwrap_err().message}",
                )
            )

        return Ok((source, final_location, marketplace_name))

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
