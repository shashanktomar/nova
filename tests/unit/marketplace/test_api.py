from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from nova.marketplace import Marketplace, MarketplaceScope
from nova.marketplace.models import (
    GitHubMarketplaceSource,
    LocalMarketplaceSource,
    MarketplaceAddError,
    MarketplaceAlreadyExistsError,
)
from nova.utils.directories import AppDirectories
from nova.utils.functools.models import Err, Ok, Result, is_err, is_ok

try:
    from pytest_mock import MockerFixture
except ImportError:  # pragma: no cover - pytest imports the plugin automatically
    MockerFixture = Any


class FakeConfigProvider:
    def __init__(self) -> None:
        self._has_marketplace_result: Result[bool, Any] = Ok(False)
        self._add_marketplace_result: Result[None, Any] = Ok(None)
        self.calls: dict[str, list[tuple[Any, ...]]] = {"has": [], "add": []}

    def set_has_marketplace_result(self, result: Result[bool, Any]) -> None:
        self._has_marketplace_result = result

    def set_add_marketplace_result(self, result: Result[None, Any]) -> None:
        self._add_marketplace_result = result

    def has_marketplace(self, name: str, source: Any) -> Result[bool, Any]:
        self.calls["has"].append((name, source))
        return self._has_marketplace_result

    def add_marketplace(self, config: Any, scope: MarketplaceScope) -> Result[None, Any]:
        self.calls["add"].append((config, scope))
        return self._add_marketplace_result


class FakeDatastore:
    def __init__(self) -> None:
        self.save_result: Result[None, Any] = Ok(None)
        self.saved: list[tuple[str, Any]] = []

    def set_save_result(self, result: Result[None, Any]) -> None:
        self.save_result = result

    def save(self, key: str, data: Any) -> Result[None, Any]:
        self.saved.append((key, data))
        return self.save_result


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
    mocker.patch("nova.marketplace.api.validate_marketplace", return_value=Ok(DummyManifest("remote")))
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
    mocker.patch("nova.marketplace.api.validate_marketplace", return_value=Ok(DummyManifest("remote")))

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
    mocker.patch("nova.marketplace.api.validate_marketplace", return_value=Ok(DummyManifest("local")))
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
    mocker.patch("nova.marketplace.api.validate_marketplace", return_value=Ok(DummyManifest("fail")))

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
    mocker.patch("nova.marketplace.api.validate_marketplace", return_value=Ok(DummyManifest("fail-config")))

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
    mocker.patch("nova.marketplace.api.validate_marketplace", return_value=Ok(DummyManifest("local")))

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


def test_list_not_implemented(marketplace: Marketplace) -> None:
    with pytest.raises(NotImplementedError):
        marketplace.list()


def test_get_not_implemented(marketplace: Marketplace) -> None:
    with pytest.raises(NotImplementedError):
        marketplace.get("name")
