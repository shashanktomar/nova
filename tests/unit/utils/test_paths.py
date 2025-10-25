from __future__ import annotations

from pathlib import Path

import pytest

from nova.utils.paths import (
    PathsConfig,
    get_data_directory,
    get_global_config_root,
    get_project_root,
    resolve_project_dir,
    resolve_working_directory,
)


@pytest.fixture
def paths_config() -> PathsConfig:
    return PathsConfig(config_dir_name="nova", project_subdir_name=".nova")


def test_get_project_root_defaults_to_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, paths_config: PathsConfig
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".nova").mkdir()
    nested = project_root / "src" / "nova"
    nested.mkdir(parents=True)

    monkeypatch.chdir(nested)

    root = get_project_root(start_dir=None, config=paths_config)

    assert root == project_root


def test_get_project_root_handles_starting_from_file(tmp_path: Path, paths_config: PathsConfig) -> None:
    project_root = tmp_path / "repo"
    project_root.mkdir()
    (project_root / ".nova").mkdir()
    nested = project_root / "src" / "package"
    nested.mkdir(parents=True)
    file_path = nested / "module.py"
    file_path.write_text("# test")

    root = get_project_root(start_dir=file_path, config=paths_config)

    assert root == project_root


def test_get_project_root_returns_none_when_marker_missing(tmp_path: Path, paths_config: PathsConfig) -> None:
    start = tmp_path / "workspace"
    start.mkdir()

    root = get_project_root(start_dir=start, config=paths_config)

    assert root is None


def test_resolve_project_dir_returns_directory_when_present(tmp_path: Path, paths_config: PathsConfig) -> None:
    project_root = tmp_path / "repo"
    project_root.mkdir()
    config_dir = project_root / ".nova"
    config_dir.mkdir()

    resolved = resolve_project_dir(project_root, paths_config)

    assert resolved == config_dir


def test_resolve_project_dir_returns_none_when_directory_missing(tmp_path: Path, paths_config: PathsConfig) -> None:
    project_root = tmp_path / "repo"
    project_root.mkdir()

    resolved = resolve_project_dir(project_root, paths_config)

    assert resolved is None


def test_resolve_project_dir_returns_none_when_project_root_missing(paths_config: PathsConfig) -> None:
    assert resolve_project_dir(None, paths_config) is None


def test_resolve_working_directory_returns_parent_for_file(tmp_path: Path) -> None:
    file_path = tmp_path / "repo" / "README.md"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("content")

    resolved = resolve_working_directory(file_path)

    assert resolved == file_path.parent.resolve()


def test_resolve_working_directory_defaults_to_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    resolved = resolve_working_directory(None)

    assert resolved == tmp_path.resolve()


def test_resolve_working_directory_returns_path_when_resolve_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "broken"

    original_resolve = Path.resolve

    def fake_resolve(self: Path, strict: bool = False) -> Path:
        if self == target:
            raise OSError("cannot resolve")
        return original_resolve(self, strict=strict)

    monkeypatch.setattr(Path, "resolve", fake_resolve, raising=False)

    resolved = resolve_working_directory(target)

    assert resolved == target


def test_get_data_directory_prefers_xdg_data_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, paths_config: PathsConfig
) -> None:
    xdg_data = tmp_path / "xdg-data"
    monkeypatch.setenv("XDG_DATA_HOME", str(xdg_data))

    data_dir = get_data_directory(paths_config)

    assert data_dir == xdg_data / paths_config.config_dir_name


def test_get_global_config_root_prefers_xdg_config_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, paths_config: PathsConfig
) -> None:
    xdg_config = tmp_path / "xdg-config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_config))

    config_root = get_global_config_root(paths_config)

    assert config_root == xdg_config / paths_config.config_dir_name
