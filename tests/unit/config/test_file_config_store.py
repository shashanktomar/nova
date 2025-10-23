from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from nova.config import FileConfigStore
from nova.config.file.config import FileConfigPaths
from nova.config.models import (
    ConfigIOError,
    ConfigScope,
    ConfigValidationError,
    ConfigYamlError,
)
from nova.utils.functools.models import is_err, is_ok

TEST_CONFIG = FileConfigPaths(
    global_config_filename="config.yaml",
    project_config_filename="config.yaml",
    user_config_filename="config.local.yaml",
    project_subdir_name=".nova",
    config_dir_name="nova",
)


def write_yaml(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_yaml_dict(path: Path, data: object) -> None:
    path.write_text(yaml.dump(data))


def test_file_config_store_loads_and_merges_all_scopes(tmp_path: Path, monkeypatch) -> None:
    # Arrange global config
    global_dir = tmp_path / "xdg" / "nova"
    global_dir.mkdir(parents=True)
    write_yaml(
        global_dir / "config.yaml",
        """
log:
  level: INFO
feature:
  retries: 1
  enabled: false
""",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    # Arrange project config
    project_root = tmp_path / "project"
    project_config_dir = project_root / ".nova"
    project_config_dir.mkdir(parents=True)
    write_yaml(
        project_config_dir / "config.yaml",
        """
feature:
  retries: 3
  metadata:
    source: project
list_value:
  items:
    - a
    - b
""",
    )
    write_yaml(
        project_config_dir / "config.local.yaml",
        """
feature:
  enabled: true
""",
    )

    working_dir = project_root / "src"
    working_dir.mkdir(parents=True)

    # Environment overrides
    monkeypatch.setenv("NOVA_CONFIG__FEATURE__RETRIES", "5")
    monkeypatch.setenv("NOVA_CONFIG__LIST_VALUE__ITEMS", '["x", "y"]')

    store = FileConfigStore(working_dir=working_dir, config=TEST_CONFIG)
    result = store.load()

    assert is_ok(result)
    config = result.unwrap()
    data = config.model_dump()
    assert data["feature"]["enabled"] is True
    assert data["feature"]["retries"] == 5
    assert data["feature"]["metadata"] == {"source": "project"}
    assert data["log"]["level"] == "INFO"
    assert data["list_value"]["items"] == ["x", "y"]


def test_file_config_store_merges_marketplaces_from_multiple_scopes(tmp_path: Path, monkeypatch) -> None:
    global_dir = tmp_path / "xdg" / "nova"
    global_dir.mkdir(parents=True)
    write_yaml(
        global_dir / "config.yaml",
        """
marketplaces:
  - name: official
    source:
      type: github
      repo: owner/official
""",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    project_root = tmp_path / "project"
    project_config_dir = project_root / ".nova"
    project_config_dir.mkdir(parents=True)
    local_marketplace_dir = project_root / "marketplaces" / "internal"
    local_marketplace_dir.mkdir(parents=True)
    override_marketplace_dir = project_root / "marketplaces" / "internal-override"
    override_marketplace_dir.mkdir(parents=True)
    write_yaml(
        project_config_dir / "config.yaml",
        f"""
marketplaces:
  - name: internal
    source:
      type: local
      path: "{local_marketplace_dir}"
  - name: official
    source:
      type: github
      repo: owner/official-fork
""",
    )
    write_yaml(
        project_config_dir / "config.local.yaml",
        f"""
marketplaces:
  - name: internal
    source:
      type: local
      path: "{override_marketplace_dir}"
  - name: user-only
    source:
      type: github
      repo: owner/user-only
""",
    )

    working_dir = project_root / "src"
    working_dir.mkdir(parents=True)

    store = FileConfigStore(working_dir=working_dir, config=TEST_CONFIG)
    result = store.load()

    assert is_ok(result)
    config = result.unwrap()
    names = [entry.name for entry in config.marketplaces]
    assert names == ["official", "internal", "user-only"]
    assert config.marketplaces[0].source.repo == "owner/official-fork"
    assert str(config.marketplaces[1].source.path) == str(override_marketplace_dir)
    assert config.marketplaces[2].source.repo == "owner/user-only"


def test_file_config_store_returns_defaults_when_no_files_exist(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path, raising=False)

    store = FileConfigStore(working_dir=Path.cwd(), config=TEST_CONFIG)
    result = store.load()

    assert is_ok(result)
    assert result.unwrap().model_dump() == {"marketplaces": []}


def test_file_config_store_returns_error_on_invalid_yaml(tmp_path: Path, monkeypatch) -> None:
    """Test that invalid YAML in global config returns ConfigYamlError."""
    global_dir = tmp_path / "xdg" / "nova"
    global_dir.mkdir(parents=True)
    global_config = global_dir / "config.yaml"
    global_config.write_text("foo: [")  # Invalid YAML
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    store = FileConfigStore(working_dir=tmp_path, config=TEST_CONFIG)
    result = store.load()

    assert is_err(result)
    error = result.err_value
    assert isinstance(error, ConfigYamlError)
    assert error.path == global_config
    assert error.message


def test_file_config_store_returns_error_on_non_mapping_root(tmp_path: Path, monkeypatch) -> None:
    """Test that non-mapping root in project config returns ConfigValidationError."""
    global_dir = tmp_path / "xdg" / "nova"
    global_dir.mkdir(parents=True)
    write_yaml_dict(global_dir / "config.yaml", {})
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    project_root = tmp_path / "project"
    project_config_dir = project_root / ".nova"
    project_config_dir.mkdir(parents=True)
    project_config = project_config_dir / "config.yaml"
    write_yaml_dict(project_config, ["not", "a", "mapping"])  # List instead of dict

    store = FileConfigStore(working_dir=project_root, config=TEST_CONFIG)
    result = store.load()

    assert is_err(result)
    error = result.err_value
    assert isinstance(error, ConfigValidationError)
    assert error.path == project_config
    assert error.message == "Configuration root must be a mapping of keys to values."


def test_file_config_store_returns_error_on_falsy_non_mapping_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that falsy non-mapping YAML roots (e.g. 'false') are rejected."""
    global_dir = tmp_path / "xdg" / "nova"
    global_dir.mkdir(parents=True)
    write_yaml_dict(global_dir / "config.yaml", {})
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    project_root = tmp_path / "project"
    project_config_dir = project_root / ".nova"
    project_config_dir.mkdir(parents=True)
    project_config = project_config_dir / "config.yaml"
    write_yaml(project_config, "false\n")

    store = FileConfigStore(working_dir=project_root, config=TEST_CONFIG)
    result = store.load()

    assert is_err(result)
    error = result.err_value
    assert isinstance(error, ConfigValidationError)
    assert error.path == project_config
    assert error.message == "Configuration root must be a mapping of keys to values."


def test_file_config_store_short_circuits_after_scope_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure later scopes are not processed once an error occurs."""
    global_dir = tmp_path / "xdg" / "nova"
    global_dir.mkdir(parents=True)
    write_yaml_dict(global_dir / "config.yaml", {"global": True})
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    project_root = tmp_path / "project"
    project_config_dir = project_root / ".nova"
    project_config_dir.mkdir(parents=True)
    project_config = project_config_dir / "config.yaml"
    write_yaml_dict(project_config, ["invalid", "root"])
    user_config = project_config_dir / "config.local.yaml"
    write_yaml(
        user_config,
        """
user_scope: true
""",
    )

    store = FileConfigStore(working_dir=project_root, config=TEST_CONFIG)

    original = FileConfigStore._load_scope_config
    called_scopes: list[ConfigScope] = []

    def tracking(
        self: FileConfigStore,
        path: Path,
        model_cls: type[object],
        scope: ConfigScope,
    ):
        called_scopes.append(scope)
        return original(self, path, model_cls, scope)

    monkeypatch.setattr(FileConfigStore, "_load_scope_config", tracking, raising=False)

    result = store.load()

    assert is_err(result)
    error = result.err_value
    assert isinstance(error, ConfigValidationError)
    assert error.scope == ConfigScope.PROJECT
    assert called_scopes == [ConfigScope.GLOBAL, ConfigScope.PROJECT]


def test_file_config_store_returns_error_on_io_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that IO errors when reading config return ConfigIOError."""
    global_dir = tmp_path / "xdg" / "nova"
    global_dir.mkdir(parents=True)
    global_config = global_dir / "config.yaml"
    write_yaml_dict(global_config, {})
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    original_read_text = Path.read_text

    def fake_read_text(self: Path, *args, **kwargs):
        if self == global_config:
            raise OSError("Permission denied")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read_text, raising=False)

    store = FileConfigStore(working_dir=tmp_path, config=TEST_CONFIG)
    result = store.load()

    assert is_err(result)
    error = result.err_value
    assert isinstance(error, ConfigIOError)
    assert error.path == global_config
    assert error.message == "Permission denied"


def test_file_config_store_finds_configs_in_nested_directories(tmp_path: Path, monkeypatch) -> None:
    """Test that FileConfigStore finds configs when working_dir is nested deep in project."""
    global_dir = tmp_path / "xdg" / "nova"
    global_dir.mkdir(parents=True)
    write_yaml(
        global_dir / "config.yaml",
        """
log:
  level: DEBUG
""",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    project_root = tmp_path / "project"
    project_config_dir = project_root / ".nova"
    project_config_dir.mkdir(parents=True)
    write_yaml(
        project_config_dir / "config.yaml",
        """
feature:
  enabled: true
""",
    )

    # Working directory is nested 3 levels deep
    nested_dir = project_root / "src" / "nova" / "cli"
    nested_dir.mkdir(parents=True)

    store = FileConfigStore(working_dir=nested_dir, config=TEST_CONFIG)
    result = store.load()

    assert is_ok(result)
    config = result.unwrap()
    data = config.model_dump()
    assert data["log"]["level"] == "DEBUG"
    assert data["feature"]["enabled"] is True


def test_file_config_store_defaults_to_cwd_when_no_working_dir_provided(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that FileConfigStore defaults to cwd when working_dir is None."""
    global_dir = tmp_path / "xdg" / "nova"
    global_dir.mkdir(parents=True)
    write_yaml(
        global_dir / "config.yaml",
        """
from_global: true
""",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    project_root = tmp_path / "project"
    project_config_dir = project_root / ".nova"
    project_config_dir.mkdir(parents=True)
    write_yaml(
        project_config_dir / "config.yaml",
        """
from_project: true
""",
    )

    working_dir = project_root / "src" / "deep"
    working_dir.mkdir(parents=True)
    monkeypatch.setattr(Path, "cwd", lambda: working_dir, raising=False)

    # Don't provide working_dir, should default to cwd
    store = FileConfigStore(working_dir=Path.cwd(), config=TEST_CONFIG)
    result = store.load()

    assert is_ok(result)
    config = result.unwrap()
    data = config.model_dump()
    assert data["from_global"] is True
    assert data["from_project"] is True


def test_file_config_store_handles_missing_project_config_gracefully(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that FileConfigStore handles missing project/user config files gracefully (not an error)."""
    # Only global config exists
    global_dir = tmp_path / "xdg" / "nova"
    global_dir.mkdir(parents=True)
    write_yaml(
        global_dir / "config.yaml",
        """
only_global: true
""",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    # Working directory has no .nova folder
    working_dir = tmp_path / "no_project"
    working_dir.mkdir()

    store = FileConfigStore(working_dir=working_dir, config=TEST_CONFIG)
    result = store.load()

    # Should succeed with just global config
    assert is_ok(result)
    config = result.unwrap()
    data = config.model_dump()
    assert data["only_global"] is True
    assert data["marketplaces"] == []


def test_get_marketplace_config_returns_merged_marketplaces(tmp_path: Path, monkeypatch) -> None:
    """Test that get_marketplace_config returns merged marketplace list from all scopes."""
    global_dir = tmp_path / "xdg" / "nova"
    global_dir.mkdir(parents=True)
    write_yaml(
        global_dir / "config.yaml",
        """
marketplaces:
  - name: official
    source:
      type: github
      repo: owner/official
""",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    project_root = tmp_path / "project"
    project_config_dir = project_root / ".nova"
    project_config_dir.mkdir(parents=True)
    local_marketplace_dir = project_root / "marketplaces" / "internal"
    local_marketplace_dir.mkdir(parents=True)
    write_yaml(
        project_config_dir / "config.yaml",
        f"""
marketplaces:
  - name: internal
    source:
      type: local
      path: "{local_marketplace_dir}"
""",
    )

    store = FileConfigStore(working_dir=project_root, config=TEST_CONFIG)
    result = store.get_marketplace_config()

    assert is_ok(result)
    marketplaces = result.unwrap()
    assert len(marketplaces) == 2
    assert marketplaces[0].name == "official"
    assert marketplaces[0].source.repo == "owner/official"
    assert marketplaces[1].name == "internal"
    assert str(marketplaces[1].source.path) == str(local_marketplace_dir)


def test_get_marketplace_config_returns_empty_list_when_no_marketplaces(tmp_path: Path, monkeypatch) -> None:
    """Test that get_marketplace_config returns empty list when no marketplaces configured."""
    global_dir = tmp_path / "xdg" / "nova"
    global_dir.mkdir(parents=True)
    write_yaml(global_dir / "config.yaml", "")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    store = FileConfigStore(working_dir=tmp_path, config=TEST_CONFIG)
    result = store.get_marketplace_config()

    assert is_ok(result)
    marketplaces = result.unwrap()
    assert marketplaces == []


def test_get_marketplace_config_propagates_config_errors(tmp_path: Path, monkeypatch) -> None:
    """Test that get_marketplace_config propagates errors from load()."""
    global_dir = tmp_path / "xdg" / "nova"
    global_dir.mkdir(parents=True)
    global_config = global_dir / "config.yaml"
    write_yaml(global_config, "invalid: [")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    store = FileConfigStore(working_dir=tmp_path, config=TEST_CONFIG)
    result = store.get_marketplace_config()

    assert is_err(result)
    error = result.err_value
    assert isinstance(error, ConfigYamlError)
