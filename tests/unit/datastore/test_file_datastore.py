from __future__ import annotations

import json
from pathlib import Path

import pytest

from nova.common import AppDirectories
from nova.datastore.file import FileDataStore
from nova.datastore.models import (
    DataStoreKeyNotFoundError,
    DataStoreReadError,
    DataStoreWriteError,
)
from nova.utils.functools.models import is_err, is_ok


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[FileDataStore, Path]:
    data_home = tmp_path / "xdg-data"
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))

    namespace = "test-namespace"
    directories = AppDirectories(app_name="nova", project_marker=".nova")
    datastore = FileDataStore(namespace=namespace, directories=directories)
    data_file = data_home / "nova" / namespace / "data.json"
    return datastore, data_file


def test_save_persists_json_payload(store: tuple[FileDataStore, Path]) -> None:
    datastore, data_file = store

    result = datastore.save("api-token", {"value": "secret"})

    assert is_ok(result)
    assert json.loads(data_file.read_text()) == {"api-token": {"value": "secret"}}


def test_save_merges_with_existing_payload(store: tuple[FileDataStore, Path]) -> None:
    datastore, data_file = store
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps({"existing": {"flag": True}}))

    result = datastore.save("new", {"value": 42})

    assert is_ok(result)
    assert json.loads(data_file.read_text()) == {
        "existing": {"flag": True},
        "new": {"value": 42},
    }


def test_load_returns_saved_value(store: tuple[FileDataStore, Path]) -> None:
    datastore, _ = store
    datastore.save("bundle", {"enabled": True})

    result = datastore.load("bundle")

    assert is_ok(result)
    assert result.unwrap() == {"enabled": True}


def test_load_returns_error_when_key_missing(store: tuple[FileDataStore, Path]) -> None:
    datastore, _ = store

    result = datastore.load("missing-key")

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, DataStoreKeyNotFoundError)
    assert error.key == "missing-key"


def test_load_returns_error_when_key_absent_in_existing_file(store: tuple[FileDataStore, Path]) -> None:
    datastore, data_file = store
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps({"other": {"value": 1}}))

    result = datastore.load("missing-key")

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, DataStoreKeyNotFoundError)
    assert error.key == "missing-key"


def test_save_rejects_existing_payload_that_is_not_mapping(store: tuple[FileDataStore, Path]) -> None:
    datastore, data_file = store
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps(["unexpected"]))

    result = datastore.save("key", {"value": 1})

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, DataStoreWriteError)


def test_save_rejects_unserializable_payload(store: tuple[FileDataStore, Path]) -> None:
    datastore, _ = store
    unserializable = object()

    result = datastore.save("key", {"value": unserializable})

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, DataStoreWriteError)


def test_load_rejects_existing_payload_that_is_not_mapping(store: tuple[FileDataStore, Path]) -> None:
    datastore, data_file = store
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps(["unexpected"]))

    result = datastore.load("key")

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, DataStoreReadError)


def test_load_rejects_invalid_json(store: tuple[FileDataStore, Path]) -> None:
    datastore, data_file = store
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text("{invalid json")

    result = datastore.load("key")

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, DataStoreReadError)


def test_delete_is_idempotent_when_file_missing(store: tuple[FileDataStore, Path]) -> None:
    datastore, _ = store

    result = datastore.delete("key")

    assert is_ok(result)


def test_delete_rejects_existing_payload_that_is_not_mapping(store: tuple[FileDataStore, Path]) -> None:
    datastore, data_file = store
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps(["unexpected"]))

    result = datastore.delete("key")

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, DataStoreWriteError)


def test_delete_removes_key_and_preserves_other_entries(store: tuple[FileDataStore, Path]) -> None:
    datastore, data_file = store
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps({"remove-me": {"value": 1}, "keep-me": {"value": 2}}))

    result = datastore.delete("remove-me")

    assert is_ok(result)
    assert json.loads(data_file.read_text()) == {"keep-me": {"value": 2}}
