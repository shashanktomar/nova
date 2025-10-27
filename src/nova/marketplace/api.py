"""Public API class for Nova marketplace management."""

from __future__ import annotations

import json
import tempfile
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import NamedTuple

from nova.common import AppDirectories, create_logger, get_data_directory_from_dirs
from nova.utils.functools.models import Err, Ok, Result, is_err

from .config import MarketplaceConfig
from .models import (
    MarketplaceAddError,
    MarketplaceAlreadyExistsError,
    MarketplaceError,
    MarketplaceInfo,
    MarketplaceManifest,
    MarketplaceNotFoundError,
    MarketplaceScope,
    MarketplaceSource,
    MarketplaceState,
    MarketplaceStateError,
)
from .protocol import MarketplaceConfigProvider
from .sources import create_source_provider, parse_source
from .store import MarketplaceStore
from .validator import load_and_validate_marketplace

logger = create_logger("marketplace")


@dataclass(frozen=True)
class _RemovalContext:
    """Internal data passed between marketplace removal steps."""

    name: str
    config: MarketplaceConfig
    state: MarketplaceState | None = None
    info: MarketplaceInfo | None = None


class _ValidatedMarketplace(NamedTuple):
    path: Path
    source: MarketplaceSource
    manifest: MarketplaceManifest


class Marketplace:
    """Marketplace management API."""

    def __init__(
        self,
        config_provider: MarketplaceConfigProvider,
        store: MarketplaceStore,
        directories: AppDirectories,
    ) -> None:
        self._config_provider = config_provider
        self._store = store
        self._directories = directories

    def add(
        self,
        source: str,
        *,
        scope: MarketplaceScope,
        working_dir: Path | None = None,
    ) -> Result[MarketplaceInfo, MarketplaceError]:
        logger.info("Adding marketplace", source=source, scope=scope.value)

        save_to_config = partial(self._save_to_config, scope)
        log_add_error = partial(self._log_add_error, source)

        return (
            parse_source(source, working_dir=working_dir)
            .and_then(self._fetch_marketplace_to_temp)
            .and_then(self._validate_and_extract_manifest)
            .and_then(self._check_for_duplicate)
            .and_then(self._move_to_final_location)
            .and_then(self._save_marketplace_state)
            .and_then(save_to_config)
            .map(lambda data: data.manifest.to_info(data.source))
            .inspect(self._log_add_success)
            .inspect_err(log_add_error)
        )

    def remove(
        self,
        name_or_source: str,
        *,
        scope: MarketplaceScope | None = None,
        working_dir: Path | None = None,
    ) -> Result[str, MarketplaceError]:
        """Remove a marketplace by name or source."""
        logger.info("Removing marketplace", name_or_source=name_or_source, scope=scope.value if scope else "any")
        remove_from_config = partial(self._config_provider.remove_marketplace, scope=scope)

        cleanup_result = (
            self._resolve_marketplace_name(name_or_source, working_dir)
            .and_then(remove_from_config)
            .map(lambda config: config.name)
            .and_then(self._delete_state)
            .and_then(self._cleanup_directory)
        )

        match cleanup_result:
            case Ok(state):
                logger.success("Marketplace removed", name=state.name)
                return Ok(state.name)
            case Err(err):
                if isinstance(err, MarketplaceStateError):
                    logger.warning(
                        "Marketplace state not found but marketplace is removed from config",
                        name=err.name,
                        error=err.message,
                    )
                    return Ok(err.name)
                logger.error("Failed to remove marketplace", name_or_source=name_or_source, error=err.message)
                return Err(err)

    def list(self) -> Result[list[MarketplaceInfo], MarketplaceError]:
        """List all configured marketplaces."""
        return self._config_provider.get_marketplace_configs().map(self._build_marketplace_infos_from_configs)

    def get(
        self,
        name: str,
    ) -> Result[MarketplaceInfo, MarketplaceError]:
        """Get details for a specific marketplace."""
        state_result = self._get_state(name)

        if is_err(state_result):
            return state_result

        state = state_result.unwrap()
        return load_and_validate_marketplace(state.install_location).map(
            lambda manifest: manifest.to_info(state.source)
        )

    def _fetch_marketplace_to_temp(
        self,
        source: MarketplaceSource,
    ) -> Result[tuple[Path, MarketplaceSource], MarketplaceError]:
        temp_base = Path(tempfile.gettempdir()) / f"nova-marketplace-{uuid.uuid4().hex}"
        return create_source_provider(source).fetch(temp_base).map(lambda path: (path, source))

    def _validate_and_extract_manifest(
        self,
        data: tuple[Path, MarketplaceSource],
    ) -> Result[_ValidatedMarketplace, MarketplaceError]:
        path, source = data
        return load_and_validate_marketplace(path).map(lambda manifest: _ValidatedMarketplace(path, source, manifest))

    def _check_for_duplicate(
        self,
        data: _ValidatedMarketplace,
    ) -> Result[_ValidatedMarketplace, MarketplaceError]:
        name = data.manifest.name
        source = data.source

        has_marketplace_result = self._config_provider.has_marketplace(name, source)
        if is_err(has_marketplace_result):
            return has_marketplace_result

        if has_marketplace_result.unwrap():
            logger.warning("Marketplace already exists", name=name, source=str(source))
            return Err(
                MarketplaceAlreadyExistsError(
                    name=name,
                    existing_source=str(source),
                    message=f"Marketplace with name '{name}' or source '{source}' already exists",
                )
            )

        return Ok(data)

    def _move_to_final_location(
        self,
        data: _ValidatedMarketplace,
    ) -> Result[_ValidatedMarketplace, MarketplaceError]:
        path, source, manifest = data
        final_location = self._move_to_data_directory(source, path, manifest.name)
        return Ok(_ValidatedMarketplace(final_location, source, manifest))

    def _save_marketplace_state(
        self,
        data: _ValidatedMarketplace,
    ) -> Result[_ValidatedMarketplace, MarketplaceError]:
        path, source, manifest = data

        state = MarketplaceState(
            name=manifest.name,
            source=source,
            install_location=path,
            last_updated=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        )

        return self._store.save(state).map(lambda _: data)

    def _save_to_config(
        self,
        scope: MarketplaceScope,
        data: _ValidatedMarketplace,
    ) -> Result[_ValidatedMarketplace, MarketplaceError]:
        _, source, manifest = data

        config = MarketplaceConfig(name=manifest.name, source=source)

        return (
            self._config_provider.add_marketplace(config, scope)
            .map_err(
                lambda error: MarketplaceAddError(
                    source=str(source),
                    message=f"Failed to save marketplace config: {error.message}",
                )
            )
            .map(lambda _: data)
        )

    def _move_to_data_directory(
        self,
        marketplace_source: MarketplaceSource,
        temp_dir: Path,
        marketplace_name: str,
    ) -> Path:
        data_dir = get_data_directory_from_dirs(self._directories)
        marketplaces_dir = data_dir / "marketplaces"
        final_location = marketplaces_dir / marketplace_name

        provider = create_source_provider(marketplace_source)
        return provider.move_to_storage(temp_dir, final_location)

    def _cleanup_directory(self, state: MarketplaceState) -> Result[MarketplaceState, MarketplaceError]:
        provider = create_source_provider(state.source)
        provider.cleanup_on_removal(state.install_location)
        return Ok(state)

    def _build_info_from_config(self, config: MarketplaceConfig) -> MarketplaceInfo:
        return MarketplaceInfo(
            name=config.name,
            description="",
            source=config.source,
            bundle_count=0,
        )

    def _resolve_marketplace_name(
        self,
        name_or_source: str,
        working_dir: Path | None,
    ) -> Result[str, MarketplaceError]:
        source_result = parse_source(name_or_source, working_dir=working_dir)
        if is_err(source_result):
            # if no source found, treat it as name
            return Ok(name_or_source)

        source = source_result.unwrap()
        config_result = self._config_provider.get_marketplace_configs()
        if is_err(config_result):
            return config_result

        match = next((cfg.name for cfg in config_result.unwrap() if cfg.source == source), None)
        if match is None:
            return Err(
                MarketplaceNotFoundError(
                    name_or_source=name_or_source,
                    message=f"Marketplace with source '{name_or_source}' not found",
                )
            )

        return Ok(match)

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

    def _build_marketplace_infos_from_configs(
        self,
        configs: list[MarketplaceConfig],
    ) -> list[MarketplaceInfo]:
        infos: list[MarketplaceInfo] = []
        for config in configs:
            state_result = self._get_state(config.name)
            if is_err(state_result):
                error = state_result.unwrap_err()
                logger.warning("Skipping marketplace due to state error", name=config.name, error=error.message)
                continue

            marketplace_dir = state_result.unwrap().install_location
            manifest_result = load_and_validate_marketplace(marketplace_dir)

            if is_err(manifest_result):
                error = manifest_result.unwrap_err()
                logger.warning("Skipping marketplace due to manifest error", name=config.name, error=error.message)
                continue

            manifest = manifest_result.unwrap()
            infos.append(manifest.to_info(config.source))

        return infos

    def _get_state(self, name: str) -> Result[MarketplaceState, MarketplaceStateError]:
        return self._store.load(name)

    def _delete_state(
        self,
        name: str,
    ) -> Result[MarketplaceState, MarketplaceStateError]:
        state_result = self._store.load(name)
        if is_err(state_result):
            return state_result

        state = state_result.unwrap()
        return self._store.delete(name).map(lambda _: state)

    def _handle_state_not_found(self, name: str, error: MarketplaceError) -> Result[str, MarketplaceError]:
        if isinstance(error, MarketplaceStateError):
            logger.warning("Marketplace state not found, skipping cleanup", name=name)
            return Ok(name)
        return Err(error)

    def _log_add_success(self, info: MarketplaceInfo) -> None:
        logger.success("Marketplace added", name=info.name, bundles=info.bundle_count)

    def _log_add_error(self, source: str, error: MarketplaceError) -> None:
        logger.error("Failed to add marketplace", source=source, error=error.message)
