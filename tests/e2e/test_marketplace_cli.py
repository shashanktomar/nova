from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner, Result

from nova.cli.main import app

RUNNER = CliRunner()
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "marketplaces"
pytestmark = pytest.mark.e2e


def _create_env(base: Path) -> dict[str, str]:
    home = base / "home"
    xdg_config = base / "xdg-config"
    xdg_data = base / "xdg-data"
    for path in (home, xdg_config, xdg_data):
        path.mkdir(parents=True, exist_ok=True)
    return {
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(xdg_config),
        "XDG_DATA_HOME": str(xdg_data),
        # Prevent git from prompting during tests
        "GIT_TERMINAL_PROMPT": "0",
    }


def _copy_marketplace_fixture(name: str, destination: Path) -> Path:
    src = FIXTURES_DIR / name
    if not src.exists():
        raise RuntimeError(f"Fixture '{name}' not found at {src}")
    shutil.copytree(src, destination)
    return destination


def _run_git(args: list[str], *, cwd: Path | None = None) -> None:
    env = os.environ | {
        "GIT_AUTHOR_NAME": "Nova Tests",
        "GIT_AUTHOR_EMAIL": "nova-tests@example.com",
        "GIT_COMMITTER_NAME": "Nova Tests",
        "GIT_COMMITTER_EMAIL": "nova-tests@example.com",
    }
    subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True)


def _create_github_mirror(
    fixture_name: str,
    *,
    owner: str,
    repo: str,
    mirror_root: Path,
) -> None:
    working_repo = mirror_root / "working" / owner / repo
    _copy_marketplace_fixture(fixture_name, working_repo)
    _run_git(["init"], cwd=working_repo)
    _run_git(["add", "-A"], cwd=working_repo)
    _run_git(["commit", "-m", "Initial commit"], cwd=working_repo)

    bare_repo = mirror_root / "github.com" / owner / f"{repo}.git"
    bare_repo.parent.mkdir(parents=True, exist_ok=True)
    _run_git(["clone", "--bare", str(working_repo), str(bare_repo)])
    _run_git(["update-server-info"], cwd=bare_repo)


def _configure_git_redirect(home: Path, mirror_root: Path) -> None:
    prefix = (mirror_root / "github.com").resolve().as_uri()
    if not prefix.endswith("/"):
        prefix = f"{prefix}/"
    gitconfig = home / ".gitconfig"
    gitconfig.write_text(f'[url "{prefix}"]\n\tinsteadOf = https://github.com/\n')


def _read_config(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data


def _read_datastore(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _invoke(args: list[str], env: dict[str, str]) -> Result:
    return RUNNER.invoke(app, args, env=env)


def test_add_marketplace_from_git_repo() -> None:
    """Journey 1: add marketplace from simulated GitHub source (global scope)."""
    with RUNNER.isolated_filesystem():
        base = Path.cwd()
        env = _create_env(base)
        mirror_root = base / "git-mirrors"
        _create_github_mirror("valid-basic", owner="owner", repo="repo", mirror_root=mirror_root)
        _configure_git_redirect(Path(env["HOME"]), mirror_root)

        result = _invoke(["marketplace", "add", "owner/repo"], env=env)
        assert result.exit_code == 0, result.stdout + result.stderr
        assert "✓ Added 'test-marketplace' with 0 bundles (global)" in result.stdout

        config_path = Path(env["XDG_CONFIG_HOME"]) / "nova" / "config.yaml"
        config = _read_config(config_path)
        assert config["marketplaces"][0]["name"] == "test-marketplace"
        assert config["marketplaces"][0]["source"]["type"] == "github"
        assert config["marketplaces"][0]["source"]["repo"] == "owner/repo"

        data_dir = Path(env["XDG_DATA_HOME"]) / "nova" / "marketplaces"
        manifest_path = data_dir / "test-marketplace" / "marketplace.json"
        assert manifest_path.exists()
        datastore_content = _read_datastore(data_dir / "data.json")
        assert "test-marketplace" in datastore_content
        assert datastore_content["test-marketplace"]["source"]["repo"] == "owner/repo"


def test_add_marketplace_to_project_scope() -> None:
    """Journey 2: add marketplace to project scope and ensure isolation."""
    with RUNNER.isolated_filesystem():
        base = Path.cwd()
        env = _create_env(base)

        project_root = base / "project"
        local_fixture = project_root / "marketplaces" / "internal"
        _copy_marketplace_fixture("valid-basic", local_fixture)
        (project_root / ".nova").mkdir(parents=True, exist_ok=True)

        result = _invoke(
            ["marketplace", "add", str(local_fixture), "--scope", "project", "--working-dir", str(project_root)],
            env=env,
        )

        assert result.exit_code == 0, result.stdout + result.stderr
        assert "✓ Added 'test-marketplace' with 0 bundles (project)" in result.stdout

        global_config = Path(env["XDG_CONFIG_HOME"]) / "nova" / "config.yaml"
        assert not global_config.exists()

        project_config = project_root / ".nova" / "config.yaml"
        config = _read_config(project_config)
        assert config["marketplaces"][0]["source"]["type"] == "local"
        assert config["marketplaces"][0]["source"]["path"] == str(local_fixture.resolve())

        data_dir = Path(env["XDG_DATA_HOME"]) / "nova" / "marketplaces"
        datastore_content = _read_datastore(data_dir / "data.json")
        assert "test-marketplace" in datastore_content


def test_add_marketplace_duplicate_error() -> None:
    """Journey 3: adding a duplicate marketplace surfaces helpful error."""
    with RUNNER.isolated_filesystem():
        base = Path.cwd()
        env = _create_env(base)
        local_dir = base / "local-marketplace"
        _copy_marketplace_fixture("valid-basic", local_dir)

        first = _invoke(["marketplace", "add", str(local_dir)], env=env)
        assert first.exit_code == 0

        duplicate = _invoke(["marketplace", "add", str(local_dir)], env=env)
        assert duplicate.exit_code == 1
        assert "error: marketplace 'test-marketplace' already exists" in duplicate.stderr
        assert "hint: use 'nova marketplace remove test-marketplace' to replace it" in duplicate.stderr

        config_path = Path(env["XDG_CONFIG_HOME"]) / "nova" / "config.yaml"
        config = _read_config(config_path)
        assert len(config["marketplaces"]) == 1


def test_add_marketplace_invalid_source() -> None:
    """Journey 4: invalid source provides guidance."""
    with RUNNER.isolated_filesystem():
        base = Path.cwd()
        env = _create_env(base)

        result = _invoke(["marketplace", "add", "./missing-path"], env=env)

        assert result.exit_code == 1
        assert "error: invalid marketplace source" in result.stderr
        assert "valid formats are" in result.stderr
        assert "owner/repo (GitHub)" in result.stderr


def test_remove_marketplace_by_name() -> None:
    """Journey 5: remove marketplace by name."""
    with RUNNER.isolated_filesystem():
        base = Path.cwd()
        env = _create_env(base)
        local_dir = base / "local-marketplace"
        _copy_marketplace_fixture("valid-basic", local_dir)

        add_result = _invoke(["marketplace", "add", str(local_dir)], env=env)
        assert add_result.exit_code == 0

        remove_result = _invoke(["marketplace", "remove", "test-marketplace"], env=env)
        assert remove_result.exit_code == 0
        assert "✓ Removed 'test-marketplace'" in remove_result.stdout

        config_path = Path(env["XDG_CONFIG_HOME"]) / "nova" / "config.yaml"
        config = _read_config(config_path)
        assert len(config.get("marketplaces", [])) == 0

        data_dir = Path(env["XDG_DATA_HOME"]) / "nova" / "marketplaces"
        datastore_content = _read_datastore(data_dir / "data.json")
        assert "test-marketplace" not in datastore_content


def test_remove_marketplace_by_source() -> None:
    """Journey 6: remove marketplace by source."""
    with RUNNER.isolated_filesystem():
        base = Path.cwd()
        env = _create_env(base)
        mirror_root = base / "git-mirrors"
        _create_github_mirror("valid-basic", owner="owner", repo="repo", mirror_root=mirror_root)
        _configure_git_redirect(Path(env["HOME"]), mirror_root)

        add_result = _invoke(["marketplace", "add", "owner/repo"], env=env)
        assert add_result.exit_code == 0

        remove_result = _invoke(["marketplace", "remove", "owner/repo"], env=env)
        assert remove_result.exit_code == 0
        assert "✓ Removed 'test-marketplace'" in remove_result.stdout

        config_path = Path(env["XDG_CONFIG_HOME"]) / "nova" / "config.yaml"
        config = _read_config(config_path)
        assert len(config.get("marketplaces", [])) == 0


def test_remove_marketplace_with_scope() -> None:
    """Journey 7: remove marketplace from specific scope."""
    with RUNNER.isolated_filesystem():
        base = Path.cwd()
        env = _create_env(base)
        project_root = base / "project"
        local_fixture = project_root / "marketplaces" / "internal"
        _copy_marketplace_fixture("valid-basic", local_fixture)
        (project_root / ".nova").mkdir(parents=True, exist_ok=True)

        add_result = _invoke(
            ["marketplace", "add", str(local_fixture), "--scope", "project", "--working-dir", str(project_root)],
            env=env,
        )
        assert add_result.exit_code == 0

        remove_result = _invoke(
            ["marketplace", "remove", "test-marketplace", "--scope", "project", "--working-dir", str(project_root)],
            env=env,
        )
        assert remove_result.exit_code == 0
        assert "✓ Removed 'test-marketplace'" in remove_result.stdout

        project_config = project_root / ".nova" / "config.yaml"
        config = _read_config(project_config)
        assert len(config.get("marketplaces", [])) == 0


def test_remove_marketplace_missing_state() -> None:
    """Journey 8: removal succeeds even if marketplace state is missing."""
    with RUNNER.isolated_filesystem():
        base = Path.cwd()
        env = _create_env(base)
        local_dir = base / "local-marketplace"
        _copy_marketplace_fixture("valid-basic", local_dir)

        add_result = _invoke(["marketplace", "add", str(local_dir)], env=env)
        assert add_result.exit_code == 0

        data_file = Path(env["XDG_DATA_HOME"]) / "nova" / "marketplaces" / "data.json"
        if data_file.exists():
            data_file.unlink()

        remove_result = _invoke(["marketplace", "remove", "test-marketplace"], env=env)
        assert remove_result.exit_code == 0, remove_result.stderr
        assert "✓ Removed 'test-marketplace'" in remove_result.stdout

        config_path = Path(env["XDG_CONFIG_HOME"]) / "nova" / "config.yaml"
        config = _read_config(config_path)
        assert len(config.get("marketplaces", [])) == 0


def test_remove_marketplace_not_found() -> None:
    """Journey 9: removing non-existent marketplace shows helpful error."""
    with RUNNER.isolated_filesystem():
        base = Path.cwd()
        env = _create_env(base)

        result = _invoke(["marketplace", "remove", "non-existent"], env=env)

        assert result.exit_code == 1
        assert "error: marketplace 'non-existent' not found" in result.stderr
        assert "hint: use 'nova marketplace list' to see available marketplaces" in result.stderr


def test_list_marketplaces() -> None:
    """Journey 10: list all configured marketplaces."""
    with RUNNER.isolated_filesystem():
        base = Path.cwd()
        env = _create_env(base)
        local_dir1 = base / "marketplace1"
        local_dir2 = base / "marketplace2"
        _copy_marketplace_fixture("valid-basic", local_dir1)
        _copy_marketplace_fixture("valid-one-bundle", local_dir2)

        add1_result = _invoke(["marketplace", "add", str(local_dir1)], env=env)
        assert add1_result.exit_code == 0

        add2_result = _invoke(["marketplace", "add", str(local_dir2)], env=env)
        assert add2_result.exit_code == 0

        list_result = _invoke(["marketplace", "list"], env=env)
        assert list_result.exit_code == 0
        assert "• test-marketplace" in list_result.stdout
        assert "• test-one-bundle" in list_result.stdout
        assert "A test marketplace for manual CLI testing" in list_result.stdout


def test_list_no_marketplaces() -> None:
    """Journey 11: list shows message when no marketplaces configured."""
    with RUNNER.isolated_filesystem():
        base = Path.cwd()
        env = _create_env(base)

        result = _invoke(["marketplace", "list"], env=env)

        assert result.exit_code == 0
        assert "No marketplaces configured" in result.stdout


def test_show_marketplace() -> None:
    """Journey 12: show details for specific marketplace."""
    with RUNNER.isolated_filesystem():
        base = Path.cwd()
        env = _create_env(base)
        local_dir = base / "local-marketplace"
        _copy_marketplace_fixture("valid-basic", local_dir)

        add_result = _invoke(["marketplace", "add", str(local_dir)], env=env)
        assert add_result.exit_code == 0

        show_result = _invoke(["marketplace", "show", "test-marketplace"], env=env)
        assert show_result.exit_code == 0
        assert "test-marketplace" in show_result.stdout
        assert "Description: A test marketplace for manual CLI testing" in show_result.stdout
        assert "Source:" in show_result.stdout
        assert "Bundles:" in show_result.stdout


def test_show_marketplace_not_found() -> None:
    """Journey 13: show non-existent marketplace shows error."""
    with RUNNER.isolated_filesystem():
        base = Path.cwd()
        env = _create_env(base)

        result = _invoke(["marketplace", "show", "non-existent"], env=env)

        assert result.exit_code == 1
        assert "error: marketplace 'non-existent' not found" in result.stderr
