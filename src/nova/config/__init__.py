"""Public configuration API for Nova.

This module exposes the minimal public interface for loading Nova configuration,
as defined in docs/specs/feature-1-config-management-spec.md.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from nova.utils.functools.models import Err, Ok, Result, is_err

from .loader import load_global_config, load_project_config, load_user_config
from .merger import merge_configs
from .models import (
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
from .paths import discover_config_paths
from .resolver import apply_env_overrides

__all__ = [
    "ConfigError",
    "ConfigIOError",
    "ConfigNotFoundError",
    "ConfigScope",
    "ConfigValidationError",
    "ConfigYamlError",
    "NovaConfig",
    "parse_config",
]


def parse_config(*, working_dir: Path | None = None) -> Result[NovaConfig, ConfigError]:
    """Parse and validate effective configuration from all scopes."""
    base_dir = working_dir or Path.cwd()

    paths = discover_config_paths(base_dir)

    global_result = _load_optional(paths.global_path, load_global_config)
    if is_err(global_result):
        return Err(global_result.err())

    project_result = _load_optional(paths.project_path, load_project_config)
    if is_err(project_result):
        return Err(project_result.err())

    user_result = _load_optional(paths.user_path, load_user_config)
    if is_err(user_result):
        return Err(user_result.err())

    global_cfg = global_result.unwrap()
    project_cfg = project_result.unwrap()
    user_cfg = user_result.unwrap()

    merged = merge_configs(
        global_cfg,
        project_cfg,
        user_cfg,
    )
    effective = apply_env_overrides(merged)
    return Ok(effective)


def _load_optional[T: (GlobalConfig, ProjectConfig, UserConfig)](
    path: Path | None,
    loader: Callable[[Path], Result[T, ConfigError]],
) -> Result[T | None, ConfigError]:
    """Load a scoped configuration when the associated path exists."""
    if path is None:
        return Ok(None)

    return loader(path)
