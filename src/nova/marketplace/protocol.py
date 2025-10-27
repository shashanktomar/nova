"""Marketplace configuration provider protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from nova.utils.functools.models import Result

from .config import MarketplaceConfig
from .models import MarketplaceConfigError, MarketplaceFetchError, MarketplaceScope, MarketplaceSource


class MarketplaceConfigProvider(Protocol):
    """Protocol for providing marketplace configuration."""

    def get_marketplace_configs(self) -> Result[list[MarketplaceConfig], MarketplaceConfigError]:
        """Get marketplace configuration from all scopes."""
        ...

    def has_marketplace(self, name: str, source: MarketplaceSource) -> Result[bool, MarketplaceConfigError]:
        """Check if a marketplace exists with the given name or source.

        Returns True if a marketplace is found with either the same name or the same source.
        """
        ...

    def add_marketplace(
        self,
        config: MarketplaceConfig,
        scope: MarketplaceScope,
    ) -> Result[None, MarketplaceConfigError]:
        """Add marketplace configuration to specified scope."""
        ...

    def remove_marketplace(
        self,
        name: str,
        scope: MarketplaceScope | None = None,
    ) -> Result[MarketplaceConfig, MarketplaceConfigError]:
        """Remove marketplace configuration by name.

        If scope is provided, only remove from that scope.
        If scope is None, remove from all scopes where found.

        Returns the removed MarketplaceConfig.
        """
        ...


class MarketplaceSourceProvider(Protocol):
    """Protocol for marketplace source operations."""

    def fetch(self, destination: Path) -> Result[Path, MarketplaceFetchError]:
        """Fetch marketplace content to destination."""
        ...

    def move_to_storage(self, temp_path: Path, final_path: Path) -> Path:
        """Move fetched content to final storage location."""
        ...

    def cleanup_on_removal(self, install_location: Path) -> None:
        """Clean up marketplace content when removed."""
        ...

    def display_name(self) -> str:
        """Human-readable identifier for this source."""
        ...
