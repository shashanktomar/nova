from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from nova.common import AppDirectories
from nova.datastore.models import DataStoreKeyNotFoundError
from nova.marketplace import Marketplace, MarketplaceScope
from nova.marketplace.config import MarketplaceConfig
from nova.marketplace.models import (
    GitHubMarketplaceSource,
    LocalMarketplaceSource,
    MarketplaceAddError,
    MarketplaceAlreadyExistsError,
    MarketplaceNotFoundError,
)
from nova.utils.functools.models import Err, Ok, Result, is_err, is_ok

try:
    from pytest_mock import MockerFixture
except ImportError:  # pragma: no cover - pytest imports the plugin automatically
    MockerFixture = Any


class FakeConfigProvider:
    def __init__(self) -> None:
        self._has_marketplace_result: Result[bool, Any] = Ok(False)
        self._add_marketplace_result: Result[None, Any] = Ok(None)
        self._remove_marketplace_result: Result[Any, Any] = Ok(None)
        self._get_marketplace_config_result: Result[list[Any], Any] = Ok([])
        self.calls: dict[str, list[tuple[Any, ...]]] = {"has": [], "add": [], "remove": [], "get": []}

    def set_has_marketplace_result(self, result: Result[bool, Any]) -> None:
        self._has_marketplace_result = result

    def set_add_marketplace_result(self, result: Result[None, Any]) -> None:
        self._add_marketplace_result = result

    def set_remove_marketplace_result(self, result: Result[Any, Any]) -> None:
        self._remove_marketplace_result = result

    def set_get_marketplace_config_result(self, result: Result[list[Any], Any]) -> None:
        self._get_marketplace_config_result = result

    def has_marketplace(self, name: str, source: Any) -> Result[bool, Any]:
        self.calls["has"].append((name, source))
        return self._has_marketplace_result

    def add_marketplace(self, config: Any, scope: MarketplaceScope) -> Result[None, Any]:
        self.calls["add"].append((config, scope))
        return self._add_marketplace_result

    def remove_marketplace(self, name: str, scope: MarketplaceScope | None) -> Result[Any, Any]:
        self.calls["remove"].append((name, scope))
        return self._remove_marketplace_result

    def get_marketplace_config(self) -> Result[list[Any], Any]:
        self.calls["get"].append(())
        return self._get_marketplace_config_result


class FakeDatastore:
    def __init__(self) -> None:
        self.save_result: Result[None, Any] = Ok(None)
        self.load_result: Result[Any, Any] = Ok({})
        self.delete_result: Result[None, Any] = Ok(None)
        self.saved: list[tuple[str, Any]] = []
        self.loaded: list[str] = []
        self.deleted: list[str] = []

    def set_save_result(self, result: Result[None, Any]) -> None:
        self.save_result = result

    def set_load_result(self, result: Result[Any, Any]) -> None:
        self.load_result = result

    def set_delete_result(self, result: Result[None, Any]) -> None:
        self.delete_result = result

    def save(self, key: str, data: Any) -> Result[None, Any]:
        self.saved.append((key, data))
        return self.save_result

    def load(self, key: str) -> Result[Any, Any]:
        self.loaded.append(key)
        return self.load_result

    def delete(self, key: str) -> Result[None, Any]:
        self.deleted.append(key)
        return self.delete_result


@pytest.fixture
def config_provider() -> FakeConfigProvider:
    return FakeConfigProvider()


@pytest.fixture
def datastore() -> FakeDatastore:
    return FakeDatastore()


@pytest.fixture
def marketplace(config_provider: FakeConfigProvider, datastore: FakeDatastore) -> Marketplace:
    directories = AppDirectories(app_name="nova", project_marker=".nova")
    return Marketplace(config_provider=config_provider, datastore=datastore, directories=directories)


class DummyManifest:
    def __init__(self, name: str) -> None:
        self.name = name
        self.bundles = []


def test_add_succeeds_for_remote_source(
    marketplace: Marketplace,
    config_provider: FakeConfigProvider,
    datastore: FakeDatastore,
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    source = GitHubMarketplaceSource(type="github", repo="owner/repo")
    fake_temp = tmp_path / "temp"
    fake_temp.mkdir()
    manifest = fake_temp / "marketplace.json"
    manifest.write_text('{"name": "remote", "description": "Remote marketplace", "bundles": [{"name": "bundle"}]}')

    data_root = tmp_path / "data"
    mocker.patch("nova.marketplace.api.fetch_marketplace", return_value=Ok(fake_temp))
    mocker.patch("nova.marketplace.api.load_and_validate_marketplace", return_value=Ok(DummyManifest("remote")))
    mocker.patch("nova.marketplace.api.parse_source", return_value=Ok(source))
    mocker.patch("nova.marketplace.api.get_data_directory_from_dirs", return_value=data_root)

    result = marketplace.add("ignored", scope=MarketplaceScope.GLOBAL)

    assert is_ok(result)
    info = result.unwrap()
    assert info.name == "remote"
    assert info.description == "Remote marketplace"
    assert info.bundle_count == 1
    assert info.source == source

    assert config_provider.calls["has"] == [("remote", source)]
    assert config_provider.calls["add"]
    assert datastore.saved
    final_location = data_root / "marketplaces" / "remote"
    assert final_location.exists()
    assert (final_location / "marketplace.json").exists()
    saved_state = datastore.saved[0][1]
    assert saved_state["name"] == "remote"
    assert Path(saved_state["install_location"]) == final_location


def test_add_returns_existing_error_when_duplicate_found(
    marketplace: Marketplace,
    config_provider: FakeConfigProvider,
    mocker: MockerFixture,
) -> None:
    source = GitHubMarketplaceSource(type="github", repo="owner/repo")
    config_provider.set_has_marketplace_result(Ok(True))
    mocker.patch("nova.marketplace.api.parse_source", return_value=Ok(source))
    mocker.patch("nova.marketplace.api.fetch_marketplace", return_value=Ok(Path("/tmp")))
    mocker.patch("nova.marketplace.api.load_and_validate_marketplace", return_value=Ok(DummyManifest("remote")))

    result = marketplace.add("ignored", scope=MarketplaceScope.GLOBAL)

    assert isinstance(result, Err)
    error = result.err_value
    assert isinstance(error, MarketplaceAlreadyExistsError)
    assert "already exists" in error.message


def test_add_propagates_fetch_error(
    marketplace: Marketplace,
    mocker: MockerFixture,
) -> None:
    source = GitHubMarketplaceSource(type="github", repo="owner/repo")
    mocker.patch("nova.marketplace.api.parse_source", return_value=Ok(source))
    mocker.patch(
        "nova.marketplace.api.fetch_marketplace", return_value=Err(MarketplaceAddError(source="src", message="fail"))
    )

    result = marketplace.add("ignored", scope=MarketplaceScope.GLOBAL)

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, MarketplaceAddError)
    assert "fail" in error.message


def test_add_skips_fetch_for_local_source(
    marketplace: Marketplace,
    mocker: MockerFixture,
    config_provider: FakeConfigProvider,
    datastore: FakeDatastore,
    tmp_path: Path,
) -> None:
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    manifest = local_dir / "marketplace.json"
    manifest.write_text('{"name": "local", "description": "local marketplace", "bundles": []}')
    source = LocalMarketplaceSource(type="local", path=local_dir)

    parse_mock = mocker.patch("nova.marketplace.api.parse_source", return_value=Ok(source))
    fetch_mock = mocker.patch("nova.marketplace.api.fetch_marketplace")
    mocker.patch("nova.marketplace.api.load_and_validate_marketplace", return_value=Ok(DummyManifest("local")))
    move_mock = mocker.patch.object(
        marketplace,
        "_move_to_data_directory",
        wraps=marketplace._move_to_data_directory,
    )

    result = marketplace.add("ignored", scope=MarketplaceScope.GLOBAL)

    assert is_ok(result)
    info = result.unwrap()
    assert info.name == "local"
    assert info.source == source
    fetch_mock.assert_not_called()
    parse_mock.assert_called_once()
    move_mock.assert_called_once()
    assert config_provider.calls["has"]
    assert datastore.saved


def test_add_returns_error_when_datastore_save_fails(
    marketplace: Marketplace,
    datastore: FakeDatastore,
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    datastore.set_save_result(Err(type("Error", (), {"message": "cannot save"})()))
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    source = LocalMarketplaceSource(type="local", path=temp_dir)

    mocker.patch("nova.marketplace.api.parse_source", return_value=Ok(source))
    mocker.patch("nova.marketplace.api.load_and_validate_marketplace", return_value=Ok(DummyManifest("fail")))

    result = marketplace.add("ignored", scope=MarketplaceScope.GLOBAL)

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, MarketplaceAddError)
    assert "Failed to save marketplace state" in error.message


def test_add_returns_error_when_config_save_fails(
    marketplace: Marketplace,
    config_provider: FakeConfigProvider,
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    config_provider.set_add_marketplace_result(Err(type("Error", (), {"message": "cannot add"})()))
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    source = LocalMarketplaceSource(type="local", path=temp_dir)

    mocker.patch("nova.marketplace.api.parse_source", return_value=Ok(source))
    mocker.patch("nova.marketplace.api.load_and_validate_marketplace", return_value=Ok(DummyManifest("fail-config")))

    result = marketplace.add("ignored", scope=MarketplaceScope.GLOBAL)

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, MarketplaceAddError)
    assert "Failed to save marketplace config" in error.message


def test_add_propagates_config_provider_error(
    marketplace: Marketplace,
    config_provider: FakeConfigProvider,
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    config_provider.set_has_marketplace_result(Err(MarketplaceAddError(source="src", message="cannot load")))
    local_dir = tmp_path / "local"
    local_dir.mkdir()
    source = LocalMarketplaceSource(type="local", path=local_dir)

    mocker.patch("nova.marketplace.api.parse_source", return_value=Ok(source))
    mocker.patch("nova.marketplace.api.load_and_validate_marketplace", return_value=Ok(DummyManifest("local")))

    result = marketplace.add("ignored", scope=MarketplaceScope.GLOBAL)

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, MarketplaceAddError)
    assert "cannot load" in error.message


def test_move_to_data_directory_replaces_existing_directory(
    marketplace: Marketplace,
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    data_root = tmp_path / "data"
    mocker.patch("nova.marketplace.api.get_data_directory_from_dirs", return_value=data_root)

    existing = data_root / "marketplaces" / "remote"
    existing.mkdir(parents=True)
    (existing / "old.txt").write_text("old")

    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    (temp_dir / "marketplace.json").write_text("{}")

    source = GitHubMarketplaceSource(type="github", repo="owner/repo")
    final_location = marketplace._move_to_data_directory(source, temp_dir, "remote")

    assert final_location == data_root / "marketplaces" / "remote"
    assert (final_location / "marketplace.json").exists()
    assert not (final_location / "old.txt").exists()
    assert not temp_dir.exists()


def test_list_returns_all_marketplaces(
    marketplace: Marketplace,
    config_provider: FakeConfigProvider,
    datastore: FakeDatastore,
    tmp_path: Path,
) -> None:
    mp1_dir = tmp_path / "mp1"
    mp1_dir.mkdir()
    (mp1_dir / "marketplace.json").write_text('{"name": "mp1", "description": "First", "bundles": [{"name": "b1"}]}')

    mp2_dir = tmp_path / "mp2"
    mp2_dir.mkdir()
    (mp2_dir / "marketplace.json").write_text('{"name": "mp2", "description": "Second", "bundles": []}')

    source1 = GitHubMarketplaceSource(type="github", repo="owner/repo1")
    source2 = GitHubMarketplaceSource(type="github", repo="owner/repo2")

    config1 = MarketplaceConfig(name="mp1", source=source1)
    config2 = MarketplaceConfig(name="mp2", source=source2)

    state1_data = {
        "name": "mp1",
        "source": {"type": "github", "repo": "owner/repo1"},
        "install_location": str(mp1_dir),
        "last_updated": "2025-01-01T00:00:00Z",
    }
    state2_data = {
        "name": "mp2",
        "source": {"type": "github", "repo": "owner/repo2"},
        "install_location": str(mp2_dir),
        "last_updated": "2025-01-01T00:00:00Z",
    }

    config_provider.set_get_marketplace_config_result(Ok([config1, config2]))

    def load_side_effect(key: str):
        if key == "mp1":
            return Ok(state1_data)
        elif key == "mp2":
            return Ok(state2_data)
        return Err({})

    datastore.load_result = Ok({})
    datastore.load = load_side_effect

    result = marketplace.list()

    assert is_ok(result)
    infos = result.unwrap()
    assert len(infos) == 2
    assert infos[0].name == "mp1"
    assert infos[0].bundle_count == 1
    assert infos[1].name == "mp2"
    assert infos[1].bundle_count == 0


def test_list_returns_empty_when_no_marketplaces(
    marketplace: Marketplace,
    config_provider: FakeConfigProvider,
) -> None:
    config_provider.set_get_marketplace_config_result(Ok([]))

    result = marketplace.list()

    assert is_ok(result)
    infos = result.unwrap()
    assert len(infos) == 0


def test_list_skips_marketplaces_with_missing_state(
    marketplace: Marketplace,
    config_provider: FakeConfigProvider,
    datastore: FakeDatastore,
    tmp_path: Path,
) -> None:
    mp1_dir = tmp_path / "mp1"
    mp1_dir.mkdir()
    (mp1_dir / "marketplace.json").write_text('{"name": "mp1", "description": "First", "bundles": []}')

    source1 = GitHubMarketplaceSource(type="github", repo="owner/repo1")
    source2 = GitHubMarketplaceSource(type="github", repo="owner/repo2")

    config1 = MarketplaceConfig(name="mp1", source=source1)
    config2 = MarketplaceConfig(name="mp2", source=source2)

    state1_data = {
        "name": "mp1",
        "source": {"type": "github", "repo": "owner/repo1"},
        "install_location": str(mp1_dir),
        "last_updated": "2025-01-01T00:00:00Z",
    }

    config_provider.set_get_marketplace_config_result(Ok([config1, config2]))

    def load_side_effect(key: str):
        if key == "mp1":
            return Ok(state1_data)
        return Err(DataStoreKeyNotFoundError(namespace="marketplaces", key=key, message="Not found"))

    datastore.load = load_side_effect

    result = marketplace.list()

    assert is_ok(result)
    infos = result.unwrap()
    assert len(infos) == 1
    assert infos[0].name == "mp1"


def test_get_returns_marketplace_info(
    marketplace: Marketplace,
    datastore: FakeDatastore,
    tmp_path: Path,
) -> None:
    mp_dir = tmp_path / "test-mp"
    mp_dir.mkdir()
    (mp_dir / "marketplace.json").write_text(
        '{"name": "test-mp", "description": "Test", "bundles": [{"name": "b1"}, {"name": "b2"}]}'
    )

    source = GitHubMarketplaceSource(type="github", repo="owner/repo")
    state_data = {
        "name": "test-mp",
        "source": {"type": "github", "repo": "owner/repo"},
        "install_location": str(mp_dir),
        "last_updated": "2025-01-01T00:00:00Z",
    }

    datastore.set_load_result(Ok(state_data))

    result = marketplace.get("test-mp")

    assert is_ok(result)
    info = result.unwrap()
    assert info.name == "test-mp"
    assert info.description == "Test"
    assert info.bundle_count == 2
    assert info.source == source


def test_get_fails_when_not_found(
    marketplace: Marketplace,
    datastore: FakeDatastore,
) -> None:
    datastore.set_load_result(
        Err(DataStoreKeyNotFoundError(namespace="marketplaces", key="unknown", message="Not found"))
    )

    result = marketplace.get("unknown")

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, MarketplaceNotFoundError)
    assert error.name_or_source == "unknown"


def test_remove_succeeds_by_name(
    marketplace: Marketplace,
    config_provider: FakeConfigProvider,
    datastore: FakeDatastore,
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    fake_location = tmp_path / "marketplace-dir"
    fake_location.mkdir()
    manifest = fake_location / "marketplace.json"
    manifest.write_text('{"name": "test-mp", "description": "Test", "bundles": []}')

    source = GitHubMarketplaceSource(type="github", repo="owner/repo")
    state_data = {
        "name": "test-mp",
        "source": {"type": "github", "repo": "owner/repo"},
        "install_location": str(fake_location),
        "last_updated": "2025-01-01T00:00:00Z",
    }
    removed_config = MarketplaceConfig(name="test-mp", source=source)

    datastore.set_load_result(Ok(state_data))
    config_provider.set_remove_marketplace_result(Ok(removed_config))

    result = marketplace.remove("test-mp", scope=MarketplaceScope.GLOBAL)

    assert is_ok(result)
    info = result.unwrap()
    assert info.name == "test-mp"
    assert info.source == source
    assert len(datastore.loaded) == 1
    assert datastore.loaded[0] == "test-mp"
    assert len(datastore.deleted) == 1
    assert datastore.deleted[0] == "test-mp"
    assert len(config_provider.calls["remove"]) == 1
    assert config_provider.calls["remove"][0] == ("test-mp", MarketplaceScope.GLOBAL)


def test_remove_succeeds_by_source(
    marketplace: Marketplace,
    config_provider: FakeConfigProvider,
    datastore: FakeDatastore,
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    fake_location = tmp_path / "marketplace-dir"
    fake_location.mkdir()
    manifest = fake_location / "marketplace.json"
    manifest.write_text('{"name": "test-mp", "description": "Test", "bundles": []}')

    source = GitHubMarketplaceSource(type="github", repo="owner/repo")
    state_data = {
        "name": "test-mp",
        "source": {"type": "github", "repo": "owner/repo"},
        "install_location": str(fake_location),
        "last_updated": "2025-01-01T00:00:00Z",
    }
    marketplace_config = MarketplaceConfig(name="test-mp", source=source)
    removed_config = MarketplaceConfig(name="test-mp", source=source)

    mocker.patch("nova.marketplace.api.parse_source", return_value=Ok(source))
    config_provider.set_get_marketplace_config_result(Ok([marketplace_config]))
    datastore.set_load_result(Ok(state_data))
    config_provider.set_remove_marketplace_result(Ok(removed_config))

    result = marketplace.remove("owner/repo", scope=None)

    assert is_ok(result)
    info = result.unwrap()
    assert info.name == "test-mp"
    assert len(config_provider.calls["get"]) == 1


def test_remove_cleans_up_non_local_directory(
    marketplace: Marketplace,
    config_provider: FakeConfigProvider,
    datastore: FakeDatastore,
    tmp_path: Path,
) -> None:
    fake_location = tmp_path / "marketplace-dir"
    fake_location.mkdir()
    manifest = fake_location / "marketplace.json"
    manifest.write_text('{"name": "test-mp", "description": "Test", "bundles": []}')

    source = GitHubMarketplaceSource(type="github", repo="owner/repo")
    state_data = {
        "name": "test-mp",
        "source": {"type": "github", "repo": "owner/repo"},
        "install_location": str(fake_location),
        "last_updated": "2025-01-01T00:00:00Z",
    }
    removed_config = MarketplaceConfig(name="test-mp", source=source)

    datastore.set_load_result(Ok(state_data))
    config_provider.set_remove_marketplace_result(Ok(removed_config))

    result = marketplace.remove("test-mp", scope=MarketplaceScope.GLOBAL)

    assert is_ok(result)
    assert not fake_location.exists()


def test_remove_preserves_local_directory(
    marketplace: Marketplace,
    config_provider: FakeConfigProvider,
    datastore: FakeDatastore,
    tmp_path: Path,
) -> None:
    fake_location = tmp_path / "marketplace-dir"
    fake_location.mkdir()
    manifest = fake_location / "marketplace.json"
    manifest.write_text('{"name": "test-mp", "description": "Test", "bundles": []}')

    source = LocalMarketplaceSource(type="local", path=fake_location)
    state_data = {
        "name": "test-mp",
        "source": {"type": "local", "path": str(fake_location)},
        "install_location": str(fake_location),
        "last_updated": "2025-01-01T00:00:00Z",
    }
    removed_config = MarketplaceConfig(name="test-mp", source=source)

    datastore.set_load_result(Ok(state_data))
    config_provider.set_remove_marketplace_result(Ok(removed_config))

    result = marketplace.remove("test-mp", scope=MarketplaceScope.GLOBAL)

    assert is_ok(result)
    assert fake_location.exists()


def test_remove_succeeds_when_state_missing(
    marketplace: Marketplace,
    config_provider: FakeConfigProvider,
    datastore: FakeDatastore,
) -> None:
    source = GitHubMarketplaceSource(type="github", repo="owner/repo")
    removed_config = MarketplaceConfig(name="test-mp", source=source)

    datastore.set_load_result(
        Err(
            DataStoreKeyNotFoundError(
                namespace="marketplaces",
                key="test-mp",
                message="Key not found",
            )
        )
    )
    config_provider.set_remove_marketplace_result(Ok(removed_config))

    result = marketplace.remove("test-mp", scope=MarketplaceScope.GLOBAL)

    assert is_ok(result)
    info = result.unwrap()
    assert info.name == "test-mp"
    assert info.bundle_count == 0
    assert len(config_provider.calls["remove"]) == 1
    assert datastore.deleted == []


def test_remove_fails_when_not_found(
    marketplace: Marketplace,
    config_provider: FakeConfigProvider,
) -> None:
    config_provider.set_remove_marketplace_result(
        Err(
            MarketplaceNotFoundError(
                name_or_source="unknown",
                message="Marketplace 'unknown' not found",
            )
        )
    )

    result = marketplace.remove("unknown", scope=MarketplaceScope.GLOBAL)

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, MarketplaceNotFoundError)
    assert error.name_or_source == "unknown"
