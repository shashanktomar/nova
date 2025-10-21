from __future__ import annotations

from pathlib import Path

from nova.config import parse_config
from nova.utils.functools.models import is_ok


def write_yaml(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_parse_config_success(tmp_path: Path, monkeypatch) -> None:
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

    result = parse_config(working_dir=working_dir)

    assert is_ok(result)
    config = result.unwrap()
    data = config.model_dump()
    assert data["feature"]["enabled"] is True
    assert data["feature"]["retries"] == 5
    assert data["feature"]["metadata"] == {"source": "project"}
    assert data["log"]["level"] == "INFO"
    assert data["list_value"]["items"] == ["x", "y"]


def test_parse_config_missing_files_returns_defaults(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path, raising=False)

    result = parse_config()

    assert is_ok(result)
    assert result.unwrap().model_dump() == {}
