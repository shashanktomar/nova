"""Configuration storage protocol."""

from typing import Protocol

from nova.marketplace.protocol import MarketplaceConfigProvider
from nova.utils.functools.models import Result

from .models import ConfigError, ConfigScope, NovaConfig


class ConfigStore(MarketplaceConfigProvider, Protocol):
    """Protocol for configuration storage and retrieval."""

    def load(self) -> Result[NovaConfig, ConfigError]:
        """Load and merge configuration from all scopes."""
        ...

    def load_scope(self, scope: ConfigScope) -> Result[NovaConfig | None, ConfigError]:
        """Load configuration from a specific scope.

        Returns:
            Ok(NovaConfig) when config file exists for the scope.
            Ok(None) when config file doesn't exist for the scope.
            Err(ConfigError) on any loading or validation errors.
        """
        ...
