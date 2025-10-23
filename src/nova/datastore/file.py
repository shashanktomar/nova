"""File-based DataStore implementation."""

from __future__ import annotations

import json
from pathlib import Path

from nova.utils.functools.models import Err, Ok, Result
from nova.utils.paths import PathsConfig, get_data_directory

from .models import DataStoreError, DataStoreKeyNotFoundError, DataStoreReadError, DataStoreWriteError


class FileDataStore:
    """File-based implementation of DataStore protocol."""

    def __init__(self) -> None:
        self._config = PathsConfig(config_dir_name="nova", project_subdir_name=".nova")

    def save(self, namespace: str, key: str, data: dict) -> Result[None, DataStoreError]:
        data_file = self._get_data_file_path(namespace)

        try:
            data_file.parent.mkdir(parents=True, exist_ok=True)

            existing_data = {}
            if data_file.exists():
                existing_data = json.loads(data_file.read_text())

            existing_data[key] = data

            data_file.write_text(json.dumps(existing_data, indent=2))

            return Ok(None)

        except (OSError, json.JSONDecodeError) as e:
            return Err(
                DataStoreWriteError(
                    namespace=namespace,
                    message=f"Failed to save data: {e}",
                )
            )

    def load(self, namespace: str, key: str) -> Result[dict, DataStoreError]:
        data_file = self._get_data_file_path(namespace)

        if not data_file.exists():
            return Err(
                DataStoreKeyNotFoundError(
                    namespace=namespace,
                    key=key,
                    message=f"Key '{key}' not found in namespace '{namespace}'",
                )
            )

        try:
            all_data = json.loads(data_file.read_text())

            if key not in all_data:
                return Err(
                    DataStoreKeyNotFoundError(
                        namespace=namespace,
                        key=key,
                        message=f"Key '{key}' not found in namespace '{namespace}'",
                    )
                )

            return Ok(all_data[key])

        except (OSError, json.JSONDecodeError) as e:
            return Err(
                DataStoreReadError(
                    namespace=namespace,
                    message=f"Failed to read data: {e}",
                )
            )

    def delete(self, namespace: str, key: str) -> Result[None, DataStoreError]:
        data_file = self._get_data_file_path(namespace)

        if not data_file.exists():
            return Ok(None)

        try:
            all_data = json.loads(data_file.read_text())

            if key in all_data:
                del all_data[key]
                data_file.write_text(json.dumps(all_data, indent=2))

            return Ok(None)

        except (OSError, json.JSONDecodeError) as e:
            return Err(
                DataStoreWriteError(
                    namespace=namespace,
                    message=f"Failed to delete data: {e}",
                )
            )

    def _get_data_file_path(self, namespace: str) -> Path:
        data_dir = get_data_directory(self._config)
        return data_dir / namespace / "data.json"
