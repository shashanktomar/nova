"""Environment variable resolution helpers for configuration."""

from __future__ import annotations

import os

import yaml

from nova.common import JsonDict
from nova.constants import ENV_PREFIX
from nova.utils.dicts import deep_merge

from .models import NovaConfig


def apply_env_overrides(config: NovaConfig) -> NovaConfig:
    """Apply environment variable overrides to config."""
    override_data: JsonDict = {}

    for key, value in os.environ.items():
        if not key.startswith(ENV_PREFIX):
            continue
        path = key[len(ENV_PREFIX) :].strip("_")
        if not path:
            continue
        segments = [segment.lower() for segment in path.split("__") if segment]
        _insert_override(override_data, segments, _parse_env_value(value))

    if not override_data:
        return config

    merged = deep_merge(dict(config.model_dump()), override_data)
    return NovaConfig.model_validate(merged)


def _insert_override(data: JsonDict, path: list[str], value: object) -> None:
    cursor = data
    *parents, leaf = path
    for segment in parents:
        child = cursor.get(segment)
        if not isinstance(child, dict):
            child = {}
            cursor[segment] = child
        cursor = child
    cursor[leaf] = value


def _parse_env_value(raw: str) -> object:
    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError:
        return raw
    return parsed
