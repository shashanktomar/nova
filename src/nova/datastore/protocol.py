"""DataStore protocol."""

from __future__ import annotations

from typing import Protocol

from nova.utils.functools.models import Result

from .models import DataStoreError


class DataStore(Protocol):
    """Protocol for data storage operations."""

    def save(self, namespace: str, key: str, data: dict) -> Result[None, DataStoreError]:
        ...

    def load(self, namespace: str, key: str) -> Result[dict, DataStoreError]:
        ...

    def delete(self, namespace: str, key: str) -> Result[None, DataStoreError]:
        ...
