"""Marketplace configuration provider protocol."""

from __future__ import annotations

from typing import Protocol

from nova.utils.functools.models import Result

from .config import MarketplaceConfig
from .models import MarketplaceError, MarketplaceScope, MarketplaceSource


class MarketplaceConfigProvider(Protocol):
    """Protocol for providing marketplace configuration."""

    def get_marketplace_config(self) -> Result[list[MarketplaceConfig], MarketplaceError]:
        """Get marketplace configuration from all scopes."""
        ...

    def has_marketplace(self, name: str, source: MarketplaceSource) -> Result[bool, MarketplaceError]:
        """Check if a marketplace exists with the given name or source.

        Returns True if a marketplace is found with either the same name or the same source.
        """
        ...

    def add_marketplace(
        self,
        config: MarketplaceConfig,
        scope: MarketplaceScope,
    ) -> Result[None, MarketplaceError]:
        """Add marketplace configuration to specified scope."""
        ...
