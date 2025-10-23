"""Configuration merging utilities."""

from __future__ import annotations

from typing import Any

from nova.utils.dicts import deep_merge

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
        merged_data = deep_merge(
            merged_data,
            scope_data,
            list_merge_strategy=_config_list_merge,
        )

    return NovaConfig.model_validate(merged_data)


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


def _config_list_merge(key: str, base_list: list[object], override_list: list[object]) -> list[object]:
    if key != "marketplaces":
        return list(override_list)
    return _merge_marketplaces(base_list, override_list)


def _merge_marketplaces(
    base_marketplaces: list[object],
    override_marketplaces: list[object],
) -> list[object]:
    merged: list[object] = []
    index_by_name: dict[str, int] = {}

    def _append(entry: object) -> None:
        merged.append(entry)
        name = _extract_marketplace_name(entry)
        if name is not None:
            index_by_name[name] = len(merged) - 1

    for entry in base_marketplaces:
        _append(entry)

    for entry in override_marketplaces:
        name = _extract_marketplace_name(entry)
        if name is not None and name in index_by_name:
            merged[index_by_name[name]] = entry
        else:
            _append(entry)

    return merged


def _extract_marketplace_name(entry: object) -> str | None:
    if isinstance(entry, dict):
        name = entry.get("name")
        return name if isinstance(name, str) else None
    return getattr(entry, "name", None)
