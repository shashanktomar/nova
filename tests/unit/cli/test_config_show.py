from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from nova.cli.main import app

runner = CliRunner()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_config_show_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    with runner.isolated_filesystem():
        base = Path.cwd()
        _write(
            base / "xdg" / "nova" / "config.yaml",
            """
log:
  level: INFO
feature:
  retries: 1
""",
        )
        project_root = base / "project"
        _write(
            project_root / ".nova" / "config.yaml",
            """
feature:
  retries: 2
""",
        )
        _write(
            project_root / ".nova" / "config.local.yaml",
            """
feature:
  enabled: true
""",
        )

        env = {"XDG_CONFIG_HOME": str(base / "xdg")}
        result = runner.invoke(app, ["config", "show", "--working-dir", str(project_root)], env=env)

        assert result.exit_code == 0
        payload = yaml.safe_load(result.stdout)
        assert payload["log"]["level"] == "INFO"
        assert payload["feature"]["retries"] == 2
        assert payload["feature"]["enabled"] is True


def test_config_show_json_with_env(monkeypatch: pytest.MonkeyPatch) -> None:
    with runner.isolated_filesystem():
        base = Path.cwd()
        project_root = base / "project"
        _write(
            project_root / ".nova" / "config.yaml",
            """
feature:
  retries: 3
""",
        )
        env = {
            "XDG_CONFIG_HOME": str(base / "xdg"),
            "NOVA_CONFIG__FEATURE__RETRIES": "5",
        }
        result = runner.invoke(
            app,
            [
                "config",
                "show",
                "--working-dir",
                str(project_root),
                "--format",
                "json",
            ],
            env=env,
        )

        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["feature"]["retries"] == 5


def test_config_show_reports_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    with runner.isolated_filesystem():
        base = Path.cwd()
        broken = base / "xdg" / "nova" / "config.yaml"
        _write(broken, "invalid: [")
        env = {"XDG_CONFIG_HOME": str(base / "xdg")}
        result = runner.invoke(app, ["config", "show"], env=env)

        assert result.exit_code == 1
        assert "global" in result.stderr.lower()
        assert str(broken) in result.stderr


def test_cli_without_subcommand_shows_help() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Usage" in result.stdout
        assert "config" in result.stdout


def test_config_subcommand_without_args_shows_help() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "Usage" in result.stdout
        assert "show" in result.stdout
