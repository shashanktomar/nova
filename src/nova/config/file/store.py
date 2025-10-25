"""File-based configuration store implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from nova.common import create_logger, get_global_config_root
from nova.marketplace import MarketplaceConfig, MarketplaceScope
from nova.marketplace.models import (
    MarketplaceConfigLoadError,
    MarketplaceConfigSaveError,
    MarketplaceError,
    MarketplaceNotFoundError,
    MarketplaceSource,
)
from nova.utils.functools.models import Err, Ok, Result, is_err

from ..merger import merge_configs
from ..models import (
    ConfigError,
    ConfigIOError,
    ConfigNotFoundError,
    ConfigScope,
    ConfigValidationError,
    ConfigYamlError,
    GlobalConfig,
    NovaConfig,
    ProjectConfig,
    UserConfig,
)
from ..protocol import ConfigStore
from ..resolver import apply_env_overrides
from .paths import ResolvedConfigPaths, discover_config_paths
from .settings import ConfigStoreSettings

logger = create_logger("config")

ScopeModel = GlobalConfig | ProjectConfig | UserConfig
ScopeModelType = type[GlobalConfig] | type[ProjectConfig] | type[UserConfig]


class FileConfigStore(ConfigStore):
    def __init__(self, settings: ConfigStoreSettings, working_dir: Path | None = None) -> None:
        self.working_dir = working_dir or Path.cwd()
        self.settings = settings

    def load(self) -> Result[NovaConfig, ConfigError]:
        logger.debug("Loading config", working_dir=str(self.working_dir))
        paths = discover_config_paths(self.working_dir, self.settings)

        logger.debug(
            "Config paths discovered",
            global_path=str(paths.global_path) if paths.global_path else None,
            project_path=str(paths.project_path) if paths.project_path else None,
            user_path=str(paths.user_path) if paths.user_path else None,
        )

        return (
            self._load_all_scopes(paths)
            .map(lambda configs: merge_configs(configs[0], configs[1], configs[2]))
            .map(apply_env_overrides)
            .inspect_err(lambda error: logger.error("Config load failed", scope=error.scope.value, error=error.message))
        )

    def load_scope(self, scope: ConfigScope) -> Result[NovaConfig | None, ConfigError]:
        paths = discover_config_paths(self.working_dir, self.settings)

        match scope:
            case ConfigScope.GLOBAL:
                path, model_cls = paths.global_path, GlobalConfig
            case ConfigScope.PROJECT:
                path, model_cls = paths.project_path, ProjectConfig
            case ConfigScope.USER:
                path, model_cls = paths.user_path, UserConfig
            case _:
                raise ValueError(f"Unexpected scope: {scope}")

        result = self._load_optional(path, model_cls, scope)
        if is_err(result):
            return result

        config = result.unwrap()
        if config is None:
            return Ok(None)

        return Ok(NovaConfig.model_validate(config.model_dump()))

    def get_marketplace_config(self) -> Result[list[MarketplaceConfig], MarketplaceError]:
        """Get marketplace configuration from all scopes."""
        result = self.load()
        if is_err(result):
            config_error = result.unwrap_err()
            return Err(
                MarketplaceConfigLoadError(
                    scope=config_error.scope.value,
                    message=f"Failed to load marketplace config: {config_error.message}",
                )
            )
        config = result.unwrap()
        return Ok(config.marketplaces)

    def has_marketplace(
        self,
        name: str,
        source: MarketplaceSource,
    ) -> Result[bool, MarketplaceError]:
        config_result = self.get_marketplace_config()
        if is_err(config_result):
            return config_result

        marketplaces = config_result.unwrap()
        has_match = any(m.name == name or m.source == source for m in marketplaces)
        return Ok(has_match)

    def add_marketplace(
        self,
        config: MarketplaceConfig,
        scope: MarketplaceScope,
    ) -> Result[None, MarketplaceError]:
        """Add marketplace configuration to specified scope."""
        config_scope = ConfigScope.GLOBAL if scope == MarketplaceScope.GLOBAL else ConfigScope.PROJECT

        result = self.load_scope(config_scope)
        if is_err(result):
            config_error = result.unwrap_err()
            return Err(
                MarketplaceConfigLoadError(
                    scope=scope.value,
                    message=f"Failed to load existing config: {config_error.message}",
                )
            )

        existing_config = result.unwrap()

        if existing_config is None:
            marketplaces = [config.model_dump(mode="json")]
        else:
            marketplaces = [m.model_dump(mode="json") for m in existing_config.marketplaces]
            marketplaces.append(config.model_dump(mode="json"))

        data = {"marketplaces": marketplaces}

        write_result = self._write_scope_data(config_scope, data)
        if is_err(write_result):
            config_error = write_result.unwrap_err()
            return Err(
                MarketplaceConfigSaveError(
                    scope=scope.value,
                    message=f"Failed to write config: {config_error.message}",
                )
            )

        return Ok(None)

    def remove_marketplace(
        self,
        name: str,
        scope: MarketplaceScope | None = None,
    ) -> Result[MarketplaceConfig, MarketplaceError]:
        """Remove marketplace configuration by name.

        If scope is provided, only remove from that scope.
        If scope is None, remove from all scopes where found.
        """
        if scope is not None:
            return self._remove_from_scope(name, scope)

        # Try removing from both scopes, return first success
        for marketplace_scope in [MarketplaceScope.PROJECT, MarketplaceScope.GLOBAL]:
            result = self._remove_from_scope(name, marketplace_scope)
            if not is_err(result):
                return result

        return Err(
            MarketplaceNotFoundError(
                name_or_source=name,
                message=f"Marketplace '{name}' not found in any scope",
            )
        )

    def _remove_from_scope(
        self,
        name: str,
        scope: MarketplaceScope,
    ) -> Result[MarketplaceConfig, MarketplaceError]:
        config_scope = (
            ConfigScope.GLOBAL
            if scope == MarketplaceScope.GLOBAL
            else ConfigScope.PROJECT
        )

        result = self.load_scope(config_scope)
        if is_err(result):
            err = result.unwrap_err()
            return Err(MarketplaceConfigLoadError(
                scope=scope.value,
                message=f"Failed to load existing config: {err.message}",
            ))

        config = result.unwrap()
        if not (config and config.marketplaces):
            return Err(MarketplaceNotFoundError(
                name_or_source=name,
                message=f"Marketplace '{name}' not found in {scope.value} scope",
            ))

        index = next(
            (i for i, m in enumerate(config.marketplaces) if m.name == name),
            None,
        )
        if index is None:
            return Err(MarketplaceNotFoundError(
                name_or_source=name,
                message=f"Marketplace '{name}' not found in {scope.value} scope",
            ))

        removed = config.marketplaces[index]
        data = {
            "marketplaces": [
                m.model_dump(mode="json")
                for i, m in enumerate(config.marketplaces)
                if i != index
            ]
        }

        write = self._write_scope_data(config_scope, data)
        if is_err(write):
            err = write.unwrap_err()
            return Err(MarketplaceConfigSaveError(
                scope=scope.value,
                message=f"Failed to write config: {err.message}",
            ))

        return Ok(removed)

    def _get_config_path_for_scope(self, scope: ConfigScope) -> Path:
        paths = discover_config_paths(self.working_dir, self.settings)

        match scope:
            case ConfigScope.GLOBAL:
                return paths.global_path or self._get_default_global_path()
            case ConfigScope.PROJECT:
                return paths.project_path or self._get_default_project_path()
            case ConfigScope.USER:
                return paths.user_path or self._get_default_user_path()
            case _:
                raise ValueError(f"Unexpected scope: {scope}")

    def _get_default_global_path(self) -> Path:
        return get_global_config_root(self.settings.directories) / self.settings.global_file

    def _get_default_project_path(self) -> Path:
        return self.working_dir / self.settings.project_marker / self.settings.project_file

    def _get_default_user_path(self) -> Path:
        return self.working_dir / self.settings.project_marker / self.settings.user_file

    def _write_scope_data(
        self,
        scope: ConfigScope,
        data: dict[str, Any],
    ) -> Result[None, ConfigError]:
        config_path = self._get_config_path_for_scope(scope)

        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            return Ok(None)
        except OSError as exc:
            return Err(
                ConfigIOError(
                    scope=scope,
                    path=config_path,
                    message=str(exc),
                )
            )

    def _load_all_scopes(
        self,
        paths: ResolvedConfigPaths,
    ) -> Result[tuple[GlobalConfig | None, ProjectConfig | None, UserConfig | None], ConfigError]:
        global_result = self._load_optional(paths.global_path, GlobalConfig, ConfigScope.GLOBAL)
        if is_err(global_result):
            return global_result

        project_result = self._load_optional(paths.project_path, ProjectConfig, ConfigScope.PROJECT)
        if is_err(project_result):
            return project_result

        user_result = self._load_optional(paths.user_path, UserConfig, ConfigScope.USER)
        if is_err(user_result):
            return user_result

        global_cfg = global_result.unwrap()
        project_cfg = project_result.unwrap()
        user_cfg = user_result.unwrap()

        assert global_cfg is None or isinstance(global_cfg, GlobalConfig)
        assert project_cfg is None or isinstance(project_cfg, ProjectConfig)
        assert user_cfg is None or isinstance(user_cfg, UserConfig)

        return Ok((global_cfg, project_cfg, user_cfg))

    def _load_optional(
        self,
        path: Path | None,
        model_cls: ScopeModelType,
        scope: ConfigScope,
    ) -> Result[ScopeModel | None, ConfigError]:
        """Load a scoped configuration when the associated path exists."""
        if path is None:
            return Ok(None)

        return self._load_scope_config(path, model_cls, scope)

    def _load_scope_config(
        self,
        path: Path,
        model_cls: ScopeModelType,
        scope: ConfigScope,
    ) -> Result[ScopeModel, ConfigError]:
        """Load and validate config from YAML file."""
        logger.debug("Loading config file", scope=scope.value, path=str(path))

        if not path.exists() or not path.is_file():
            logger.warning("Config file not found", scope=scope.value, path=str(path))
            return Err(
                ConfigNotFoundError(
                    scope=scope,
                    expected_path=path,
                    message=f"Configuration file not found for scope '{scope.value}'.",
                ),
            )

        try:
            raw_text = path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error("Config file read error", scope=scope.value, path=str(path), error=str(exc))
            return Err(
                ConfigIOError(
                    scope=scope,
                    path=path,
                    message=str(exc),
                ),
            )

        try:
            data = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            line = getattr(mark, "line", None)
            column = getattr(mark, "column", None)
            logger.error(
                "Config YAML parse error",
                scope=scope.value,
                path=str(path),
                line=line,
                column=column,
                error=str(exc),
            )
            return Err(
                ConfigYamlError(
                    scope=scope,
                    path=path,
                    line=(line + 1) if line is not None else None,
                    column=(column + 1) if column is not None else None,
                    message=str(exc),
                ),
            )

        if data is None:
            data = {}

        if not isinstance(data, dict):
            logger.error("Config must be a mapping", scope=scope.value, path=str(path))
            return Err(
                ConfigValidationError(
                    scope=scope,
                    path=path,
                    field=None,
                    message="Configuration root must be a mapping of keys to values.",
                ),
            )

        try:
            model = model_cls.model_validate(data)
            logger.debug("Config validated", scope=scope.value, path=str(path))
        except ValidationError as exc:
            error_details = exc.errors()
            field = None
            message = str(exc)
            if error_details:
                first = error_details[0]
                loc = first.get("loc") or ()
                field = ".".join(str(part) for part in loc) or None
                message = first.get("msg", message)
            logger.error("Config validation error", scope=scope.value, path=str(path), field=field, error=message)
            return Err(
                ConfigValidationError(
                    scope=scope,
                    path=path,
                    field=field,
                    message=message,
                ),
            )

        return Ok(model)
