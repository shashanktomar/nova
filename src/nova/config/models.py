"""Pydantic models for Nova configuration scopes and errors."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nova.common import LoggingConfig
from nova.marketplace.config import MarketplaceConfig


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


type ConfigError = ConfigNotFoundError | ConfigYamlError | ConfigValidationError | ConfigIOError


class GlobalConfig(BaseModel):
    """Global configuration (~/.config/nova/config.yaml)."""

    model_config = ConfigDict(extra="allow")

    marketplaces: list[MarketplaceConfig] = []
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


class ProjectConfig(BaseModel):
    """Project configuration (.nova/config.yaml)."""

    model_config = ConfigDict(extra="allow")

    marketplaces: list[MarketplaceConfig] = []

    @model_validator(mode="before")
    @classmethod
    def _validate_no_logging(cls, data: dict) -> dict:
        if isinstance(data, dict) and "logging" in data:
            raise ValueError(
                "Logging configuration can only be set in global config (~/.config/nova/config.yaml). "
                "Remove 'logging' from project config (.nova/config.yaml)."
            )
        return data


class UserConfig(BaseModel):
    """User configuration (.nova/config.local.yaml)."""

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def _validate_no_logging(cls, data: dict) -> dict:
        if isinstance(data, dict) and "logging" in data:
            raise ValueError(
                "Logging configuration can only be set in global config (~/.config/nova/config.yaml). "
                "Remove 'logging' from user config (.nova/config.local.yaml)."
            )
        return data


class NovaConfig(BaseModel):
    """Effective configuration (merged result)."""

    model_config = ConfigDict(extra="allow")

    marketplaces: list[MarketplaceConfig] = []
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
