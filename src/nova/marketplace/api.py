"""Public API class for Nova marketplace management."""

from __future__ import annotations

import json
import shutil
import tempfile
import uuid
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

from nova.datastore import DataStore
from nova.utils.directories import AppDirectories
from nova.utils.functools.models import Err, Ok, Result, is_err
from nova.utils.paths import get_data_directory_from_dirs

from .config import MarketplaceConfig
from .fetcher import fetch_marketplace
from .models import (
    LocalMarketplaceSource,
    MarketplaceAddError,
    MarketplaceAlreadyExistsError,
    MarketplaceError,
    MarketplaceInfo,
    MarketplaceNotFoundError,
    MarketplaceScope,
    MarketplaceSource,
    MarketplaceState,
)
from .protocol import MarketplaceConfigProvider
from .sources import parse_source
from .validator import validate_marketplace


class Marketplace:
    """Marketplace management API."""

    def __init__(
        self,
        config_provider: MarketplaceConfigProvider,
        datastore: DataStore,
        directories: AppDirectories,
    ) -> None:
        self._config_provider = config_provider
        self._datastore = datastore
        self._directories = directories

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
        return (
            self._resolve_marketplace_name(name_or_source, working_dir)
            .and_then(self._load_marketplace_state)
            .and_then(self._attach_marketplace_info)
            .and_then(lambda data: self._remove_from_config_with_info(data, scope))
            .and_then(self._delete_marketplace_state_with_info)
            .and_then(self._cleanup_directory_with_info)
            .map(lambda data: data[1])
        )

    def list(
        self,
        *,
        working_dir: Path | None = None,
    ) -> Result[list[MarketplaceInfo], MarketplaceError]:
        """List all configured marketplaces."""
        return (
            self._get_all_marketplace_configs()
            .map(self._build_marketplace_infos_from_configs)
        )

    def get(
        self,
        name: str,
        *,
        working_dir: Path | None = None,
    ) -> Result[MarketplaceInfo, MarketplaceError]:
        """Get details for a specific marketplace."""
        return (
            self._load_marketplace_state(name)
            .and_then(self._attach_marketplace_info)
            .map(lambda data: data[1])
        )

    def _fetch_marketplace_to_temp(
        self,
        source: MarketplaceSource,
    ) -> Result[tuple[MarketplaceSource, Path], MarketplaceError]:
        if isinstance(source, LocalMarketplaceSource):
            return Ok((source, source.path))

        # Create a unique temp directory path (git clone will create it)
        temp_base = Path(tempfile.gettempdir()) / f"nova-marketplace-{uuid.uuid4().hex}"
        return fetch_marketplace(source, temp_base).map(lambda path: (source, path))

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

        data_dir = get_data_directory_from_dirs(self._directories)
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
            last_updated=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
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

    def _resolve_marketplace_name(
        self,
        name_or_source: str,
        working_dir: Path | None,
    ) -> Result[str, MarketplaceError]:
        # Try parsing as source
        source_result = parse_source(name_or_source, working_dir=working_dir)
        if not is_err(source_result):
            # It's a valid source, find marketplace by source
            source = source_result.unwrap()
            config_result = self._config_provider.get_marketplace_config()
            if is_err(config_result):
                return config_result

            marketplaces = config_result.unwrap()
            for marketplace in marketplaces:
                if marketplace.source == source:
                    return Ok(marketplace.name)

            return Err(
                MarketplaceNotFoundError(
                    name_or_source=name_or_source,
                    message=f"Marketplace with source '{name_or_source}' not found",
                )
            )

        # Not a valid source, treat as name
        return Ok(name_or_source)

    def _load_marketplace_state(
        self,
        name: str,
    ) -> Result[MarketplaceState, MarketplaceError]:
        load_result = self._datastore.load(name)
        if is_err(load_result):
            return Err(
                MarketplaceNotFoundError(
                    name_or_source=name,
                    message=f"Marketplace '{name}' state not found",
                )
            )

        state_data = load_result.unwrap()
        state = MarketplaceState.model_validate(state_data)
        return Ok(state)

    def _attach_marketplace_info(
        self,
        state: MarketplaceState,
    ) -> Result[tuple[MarketplaceState, MarketplaceInfo], MarketplaceError]:
        manifest_path = state.install_location / "marketplace.json"
        bundle_count = 0
        description = ""

        if manifest_path.exists():
            manifest_data = json.loads(manifest_path.read_text())
            bundle_count = len(manifest_data.get("bundles", []))
            description = manifest_data.get("description", "")

        info = MarketplaceInfo(
            name=state.name,
            description=description,
            source=state.source,
            bundle_count=bundle_count,
        )

        return Ok((state, info))

    def _remove_from_config_with_info(
        self,
        data: tuple[MarketplaceState, MarketplaceInfo],
        scope: MarketplaceScope | None,
    ) -> Result[tuple[MarketplaceState, MarketplaceInfo], MarketplaceError]:
        state, info = data
        remove_result = self._config_provider.remove_marketplace(state.name, scope)
        if is_err(remove_result):
            return remove_result

        return Ok((state, info))

    def _delete_marketplace_state_with_info(
        self,
        data: tuple[MarketplaceState, MarketplaceInfo],
    ) -> Result[tuple[MarketplaceState, MarketplaceInfo], MarketplaceError]:
        state, info = data
        delete_result = self._datastore.delete(state.name)
        if is_err(delete_result):
            return Err(
                MarketplaceAddError(
                    source=str(state.source),
                    message=f"Failed to delete marketplace state: {delete_result.unwrap_err().message}",
                )
            )

        return Ok((state, info))

    def _cleanup_directory_with_info(
        self,
        data: tuple[MarketplaceState, MarketplaceInfo],
    ) -> Result[tuple[MarketplaceState, MarketplaceInfo], MarketplaceError]:
        state, info = data

        if isinstance(state.source, LocalMarketplaceSource):
            # Don't delete local source directories
            return Ok((state, info))

        if state.install_location.exists():
            shutil.rmtree(state.install_location)

        return Ok((state, info))

    def _get_all_marketplace_configs(self) -> Result[list[MarketplaceConfig], MarketplaceError]:
        return self._config_provider.get_marketplace_config()

    def _build_marketplace_infos_from_configs(
        self,
        configs: list[MarketplaceConfig],
    ) -> list[MarketplaceInfo]:
        infos: list[MarketplaceInfo] = []
        for config in configs:
            state_result = self._datastore.load(config.name)
            if is_err(state_result):
                continue

            state_data = state_result.unwrap()
            state = MarketplaceState.model_validate(state_data)

            manifest_path = state.install_location / "marketplace.json"
            bundle_count = 0
            description = ""

            if manifest_path.exists():
                manifest_data = json.loads(manifest_path.read_text())
                bundle_count = len(manifest_data.get("bundles", []))
                description = manifest_data.get("description", "")

            info = MarketplaceInfo(
                name=state.name,
                description=description,
                source=state.source,
                bundle_count=bundle_count,
            )
            infos.append(info)

        return infos
