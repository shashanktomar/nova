"""Local filesystem marketplace fetcher."""

from __future__ import annotations

from pathlib import Path

from nova.marketplace.models import LocalMarketplaceSource
from nova.utils.functools.models import Ok

from .protocol import FetchResult


def fetch_local(source: LocalMarketplaceSource, destination: Path) -> FetchResult:
    """Fetch marketplace from local filesystem.

    For local sources, no actual fetching occurs. The path is already validated
    by Pydantic (DirectoryPath), so we just return it.
    """
    return Ok(source.path)
