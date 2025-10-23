"""DataStore error models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DataStoreError(BaseModel):
    """Base datastore error."""

    model_config = ConfigDict(extra="forbid")

    message: str


class DataStoreReadError(DataStoreError):
    """Error reading from datastore."""

    namespace: str


class DataStoreWriteError(DataStoreError):
    """Error writing to datastore."""

    namespace: str


class DataStoreKeyNotFoundError(DataStoreError):
    """Key not found in datastore."""

    namespace: str
    key: str
