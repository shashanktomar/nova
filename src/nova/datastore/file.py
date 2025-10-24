"""File-based DataStore implementation."""

from __future__ import annotations

import json
from pathlib import Path

from nova.utils.directories import AppDirectories
from nova.utils.functools.models import Err, Ok, Result
from nova.utils.paths import get_data_directory_from_dirs
from nova.utils.types import JsonValue

from .models import DataStoreError, DataStoreKeyNotFoundError, DataStoreReadError, DataStoreWriteError


class FileDataStore:
    """File-based implementation of DataStore protocol."""

    def __init__(self, namespace: str, directories: AppDirectories) -> None:
        self._namespace = namespace
        self._directories = directories

    def save(self, key: str, data: JsonValue) -> Result[None, DataStoreError]:
        data_file = self._get_data_file_path()

        try:
            data_file.parent.mkdir(parents=True, exist_ok=True)

            existing_data: dict[str, JsonValue]
            existing_data = {}
            if data_file.exists():
                existing_data_raw = json.loads(data_file.read_text())
                if not isinstance(existing_data_raw, dict):
                    raise TypeError("Existing data must be a JSON object")
                existing_data = existing_data_raw

            existing_data[key] = data

            data_file.write_text(json.dumps(existing_data, indent=2))

            return Ok(None)

        except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
            return Err(
                DataStoreWriteError(
                    namespace=self._namespace,
                    message=f"Failed to save data: {e}",
                )
            )

    def load(self, key: str) -> Result[JsonValue, DataStoreError]:
        data_file = self._get_data_file_path()

        if not data_file.exists():
            return Err(
                DataStoreKeyNotFoundError(
                    namespace=self._namespace,
                    key=key,
                    message=f"Key '{key}' not found in namespace '{self._namespace}'",
                )
            )

        try:
            all_data = json.loads(data_file.read_text())
            if not isinstance(all_data, dict):
                raise TypeError("Stored data must be a JSON object")

            if key not in all_data:
                return Err(
                    DataStoreKeyNotFoundError(
                        namespace=self._namespace,
                        key=key,
                        message=f"Key '{key}' not found in namespace '{self._namespace}'",
                    )
                )

            return Ok(all_data[key])

        except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
            return Err(
                DataStoreReadError(
                    namespace=self._namespace,
                    message=f"Failed to read data: {e}",
                )
            )

    def delete(self, key: str) -> Result[None, DataStoreError]:
        data_file = self._get_data_file_path()

        if not data_file.exists():
            return Ok(None)

        try:
            all_data = json.loads(data_file.read_text())
            if not isinstance(all_data, dict):
                raise TypeError("Stored data must be a JSON object")

            if key in all_data:
                del all_data[key]
                data_file.write_text(json.dumps(all_data, indent=2))

            return Ok(None)

        except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
            return Err(
                DataStoreWriteError(
                    namespace=self._namespace,
                    message=f"Failed to delete data: {e}",
                )
            )

    def _get_data_file_path(self) -> Path:
        data_dir = get_data_directory_from_dirs(self._directories)
        return data_dir / self._namespace / "data.json"
