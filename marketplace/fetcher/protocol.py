"""Fetcher protocol for marketplace sources."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from nova.marketplace.models import MarketplaceSource
from nova.utils.functools.models import Result


class FetchError(Exception):
    """Base error for fetch operations."""

    pass


type FetchResult = Result[Path, FetchError]


type MarketplaceFetcher = Callable[[MarketplaceSource, Path], FetchResult]
