"""Configuration merging utilities."""

from __future__ import annotations

from typing import Any

from .models import (
    GlobalConfig,
    NovaConfig,
    ProjectConfig,
    UserConfig,
)


def merge_configs(
    global_cfg: GlobalConfig | None,
    project_cfg: ProjectConfig | None,
    user_cfg: UserConfig | None,
) -> NovaConfig:
    """Merge configs with precedence: user > project > global."""
    merged_data: dict[str, Any] = {}

    for scope in (global_cfg, project_cfg, user_cfg):
        if scope is None:
            continue
        scope_data = _strip_none_dict(scope.model_dump())
        merged_data = _deep_merge(merged_data, scope_data)

    return NovaConfig.model_validate(merged_data)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = base.copy()
    for key, value in override.items():
        if value is None:
            continue
        if key in result:
            base_value = result[key]
            if isinstance(base_value, dict) and isinstance(value, dict):
                result[key] = _deep_merge(base_value, value)
            else:
                result[key] = value
        else:
            result[key] = value
    return result


def _strip_none_dict(data: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, dict):
            cleaned[key] = _strip_none_dict(dict(value))
        else:
            cleaned[key] = value
    return cleaned
