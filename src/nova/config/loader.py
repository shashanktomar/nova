"""Configuration file loading and validation helpers."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from nova.utils.functools.models import Err, Ok, Result

from .models import (
    ConfigError,
    ConfigIOError,
    ConfigNotFoundError,
    ConfigScope,
    ConfigValidationError,
    ConfigYamlError,
    GlobalConfig,
    ProjectConfig,
    UserConfig,
)


def load_global_config(path: Path) -> Result[GlobalConfig, ConfigError]:
    """Load and validate global config from YAML file."""
    return _load_scope_config(path, GlobalConfig, ConfigScope.GLOBAL)


def load_project_config(path: Path) -> Result[ProjectConfig, ConfigError]:
    """Load and validate project config from YAML file."""
    return _load_scope_config(path, ProjectConfig, ConfigScope.PROJECT)


def load_user_config(path: Path) -> Result[UserConfig, ConfigError]:
    """Load and validate user config from YAML file."""
    return _load_scope_config(path, UserConfig, ConfigScope.USER)


def _load_scope_config[
    T: (GlobalConfig, ProjectConfig, UserConfig),
](
    path: Path,
    model_cls: type[T],
    scope: ConfigScope,
) -> Result[T, ConfigError]:
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
        data = yaml.safe_load(raw_text) or {}
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
    except ValidationError as exc:  # pragma: no cover - exercised via structured error
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
