"""Public configuration API for Nova.

This module exposes the minimal public interface for loading Nova configuration,
as defined in docs/specs/feature-1-config-management-spec.md.
"""

from __future__ import annotations

from pathlib import Path

from nova.utils.functools.models import Result

from .file import FileConfigStore
from .models import (
    ConfigError,
    ConfigIOError,
    ConfigNotFoundError,
    ConfigScope,
    ConfigValidationError,
    ConfigYamlError,
    NovaConfig,
)
from .protocol import ConfigStore

__all__ = [
    "ConfigError",
    "ConfigIOError",
    "ConfigNotFoundError",
    "ConfigScope",
    "ConfigStore",
    "ConfigValidationError",
    "ConfigYamlError",
    "FileConfigStore",
    "NovaConfig",
]
