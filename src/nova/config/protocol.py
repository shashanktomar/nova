"""Configuration storage protocol."""

from typing import Protocol

from nova.config.models import ConfigError, NovaConfig
from nova.marketplace.protocol import MarketplaceConfigProvider
from nova.utils.functools.models import Result


class ConfigStore(MarketplaceConfigProvider, Protocol):
    """Protocol for configuration storage and retrieval."""

    def load(self) -> Result[NovaConfig, ConfigError]:
        """Load merged configuration."""
        ...
