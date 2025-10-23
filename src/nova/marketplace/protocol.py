"""Marketplace configuration provider protocol."""

from __future__ import annotations

from typing import Protocol

from nova.utils.functools.models import Result

from .config import MarketplaceConfig
from .models import MarketplaceError, MarketplaceScope


class MarketplaceConfigProvider(Protocol):
    """Protocol for providing marketplace configuration."""

    def get_marketplace_config(self) -> Result[list[MarketplaceConfig], MarketplaceError]:
        """Get marketplace configuration from all scopes."""
        ...

    def add_marketplace_config(
        self,
        config: MarketplaceConfig,
        scope: MarketplaceScope,
    ) -> Result[None, MarketplaceError]:
        """Add marketplace configuration to specified scope."""
        ...
