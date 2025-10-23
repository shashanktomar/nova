"""File-based configuration store implementation."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from nova.marketplace import MarketplaceConfig
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
from ..resolver import apply_env_overrides
from .config import FileConfigPaths
from .paths import discover_config_paths

ScopeModel = GlobalConfig | ProjectConfig | UserConfig
ScopeModelType = type[GlobalConfig] | type[ProjectConfig] | type[UserConfig]


class FileConfigStore:
    def __init__(self, working_dir: Path, config: FileConfigPaths) -> None:
        self.working_dir = working_dir
        self.config = config

    def load(self) -> Result[NovaConfig, ConfigError]:
        paths = discover_config_paths(self.working_dir, self.config)

        scope_specs: tuple[tuple[Path | None, ScopeModelType, ConfigScope], ...] = (
            (paths.global_path, GlobalConfig, ConfigScope.GLOBAL),
            (paths.project_path, ProjectConfig, ConfigScope.PROJECT),
            (paths.user_path, UserConfig, ConfigScope.USER),
        )

        global_cfg: GlobalConfig | None = None
        project_cfg: ProjectConfig | None = None
        user_cfg: UserConfig | None = None

        for path, model_cls, scope in scope_specs:
            result = self._load_optional(path, model_cls, scope)
            if is_err(result):
                return Err(result.err())
            value = result.unwrap()
            match scope:
                case ConfigScope.GLOBAL:
                    assert value is None or isinstance(value, GlobalConfig)
                    global_cfg = value
                case ConfigScope.PROJECT:
                    assert value is None or isinstance(value, ProjectConfig)
                    project_cfg = value
                case ConfigScope.USER:
                    assert value is None or isinstance(value, UserConfig)
                    user_cfg = value

        merged = merge_configs(
            global_cfg,
            project_cfg,
            user_cfg,
        )
        effective = apply_env_overrides(merged)
        return Ok(effective)

    def get_marketplace_config(self) -> Result[list[MarketplaceConfig], ConfigError]:
        """Get marketplace configuration from all scopes."""
        result = self.load()
        if is_err(result):
            return Err(result.err())
        config = result.unwrap()
        return Ok(config.marketplaces)

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
        if not path.exists() or not path.is_file():
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
        except ValidationError as exc:
            error_details = exc.errors()
            field = None
            message = str(exc)
            if error_details:
                first = error_details[0]
                loc = first.get("loc") or ()
                field = ".".join(str(part) for part in loc) or None
                message = first.get("msg", message)
            return Err(
                ConfigValidationError(
                    scope=scope,
                    path=path,
                    field=field,
                    message=message,
                ),
            )

        return Ok(model)
