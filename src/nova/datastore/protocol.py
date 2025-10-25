"""DataStore protocol."""

from __future__ import annotations

from typing import Protocol

from nova.common import JsonValue
from nova.utils.functools.models import Result

from .models import DataStoreError


class DataStore(Protocol):
    """Protocol for data storage operations."""

    def save(self, key: str, data: JsonValue) -> Result[None, DataStoreError]: ...

    def load(self, key: str) -> Result[JsonValue, DataStoreError]: ...

    def delete(self, key: str) -> Result[None, DataStoreError]: ...
