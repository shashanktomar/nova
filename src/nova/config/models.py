"""Pydantic models for Nova configuration scopes and errors."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class ConfigScope(str, Enum):
    """Configuration scope levels."""

    GLOBAL = "global"
    PROJECT = "project"
    USER = "user"
    EFFECTIVE = "effective"


class ConfigNotFoundError(BaseModel):
    """Configuration file not found at expected location."""

    model_config = ConfigDict(extra="forbid")

    scope: ConfigScope
    expected_path: Path
    message: str


class ConfigYamlError(BaseModel):
    """YAML parsing error in configuration file."""

    model_config = ConfigDict(extra="forbid")

    scope: ConfigScope
    path: Path
    line: int | None = None
    column: int | None = None
    message: str


class ConfigValidationError(BaseModel):
    """Schema validation error in configuration."""

    model_config = ConfigDict(extra="forbid")

    scope: ConfigScope
    path: Path
    field: str | None = None
    message: str


class ConfigIOError(BaseModel):
    """File I/O error reading configuration."""

    model_config = ConfigDict(extra="forbid")

    scope: ConfigScope
    path: Path
    message: str


type ConfigError = (
    ConfigNotFoundError
    | ConfigYamlError
    | ConfigValidationError
    | ConfigIOError
)


class GlobalConfig(BaseModel):
    """Global configuration (~/.config/nova/config.yaml)."""

    model_config = ConfigDict(extra="allow")


class ProjectConfig(BaseModel):
    """Project configuration (.nova/config.yaml)."""

    model_config = ConfigDict(extra="allow")


class UserConfig(BaseModel):
    """User configuration (.nova/config.local.yaml)."""

    model_config = ConfigDict(extra="allow")


class NovaConfig(BaseModel):
    """Effective configuration (merged result)."""

    model_config = ConfigDict(extra="allow")
