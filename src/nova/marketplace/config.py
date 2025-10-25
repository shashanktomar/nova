"""Marketplace configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from nova.common import NonEmptyString

from .models import MarketplaceSource


class MarketplaceConfig(BaseModel):
    """Marketplace configuration entry stored in config.yaml."""

    model_config = ConfigDict(extra="ignore")

    name: NonEmptyString
    source: MarketplaceSource
