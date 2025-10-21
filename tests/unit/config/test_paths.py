from __future__ import annotations

from pathlib import Path

import pytest

from nova.config.paths import ConfigPaths, discover_config_paths


@pytest.fixture(autouse=True)
def _reset_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure environment-related settings are reset between tests."""
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)


# Tests rely on pytest's built-in tmp_path fixture to build isolated configs per case.
def _given_global_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a global configuration file under a fake XDG config home."""
    xdg_home = tmp_path / "xdg"
    config_dir = xdg_home / "nova"
    config_dir.mkdir(parents=True, exist_ok=True)
    global_file = config_dir / "config.yaml"
    global_file.write_text("global")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_home))
    return global_file


def _create_workspace(
    base_dir: Path,
    *,
    create_project: bool,
    nested_depth: int,
) -> tuple[Path, Path | None, Path | None]:
    """Build a fake project tree returning the deepest directory and config files."""
    project_root = base_dir / "project"
    project_root.mkdir(parents=True, exist_ok=True)

    current_dir = project_root
    for depth in range(nested_depth):
        current_dir = current_dir / f"level_{depth}"
        current_dir.mkdir()

    project_file = None
    user_file = None
    if create_project:
        config_dir = project_root / ".nova"
        config_dir.mkdir()
        project_file = config_dir / "config.yaml"
        project_file.write_text("project")
        user_file = config_dir / "config.local.yaml"
        user_file.write_text("user")

    return current_dir, project_file, user_file


@pytest.mark.parametrize(
    ("description", "create_project", "nested_depth", "use_file", "create_global"),
    [
        ("project_root", True, 0, False, True),
        ("nested_file", True, 3, True, True),
        ("outside_project", False, 2, False, True),
        ("no_global", True, 1, False, False),
    ],
    ids=["project-root", "nested-file", "outside-project", "no-global"],
)
def test_discover_paths_variants(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    description: str,
    create_project: bool,
    nested_depth: int,
    use_file: bool,
    create_global: bool,
) -> None:
    home_dir = tmp_path / f"{description}_home"
    home_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home_dir, raising=False)

    global_file: Path | None = None
    if create_global:
        global_file = _given_global_config(tmp_path, monkeypatch)

    base_dir = tmp_path / f"{description}_workspace"
    base_dir.mkdir()
    working_base, project_file, user_file = _create_workspace(
        base_dir,
        create_project=create_project,
        nested_depth=nested_depth,
    )

    working_path = working_base
    if use_file:
        file_path = working_base / "settings.py"
        file_path.write_text("#")
        working_path = file_path

    paths = discover_config_paths(working_path)

    assert paths == ConfigPaths(
        global_path=global_file,
        project_path=project_file,
        user_path=user_file,
    )


def test_discover_paths_defaults_to_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home_dir = tmp_path / "default_home"
    home_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home_dir, raising=False)

    global_file = _given_global_config(tmp_path, monkeypatch)

    base_dir = tmp_path / "default_workspace"
    base_dir.mkdir()
    working_dir, project_file, user_file = _create_workspace(
        base_dir,
        create_project=True,
        nested_depth=2,
    )

    monkeypatch.setattr(Path, "cwd", lambda: working_dir, raising=False)

    paths = discover_config_paths()

    assert paths == ConfigPaths(
        global_path=global_file,
        project_path=project_file,
        user_path=user_file,
    )

