from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from nova.config.loader import (
    load_global_config,
    load_project_config,
    load_user_config,
)
from nova.config.models import (
    ConfigIOError,
    ConfigNotFoundError,
    ConfigScope,
    ConfigValidationError,
    ConfigYamlError,
)
from nova.utils.functools.models import is_err, is_ok


def _write_yaml(path: Path, data: object) -> None:
    path.write_text(yaml.dump(data))


@pytest.mark.parametrize(
    ("loader", "scope"),
    [
        (load_global_config, ConfigScope.GLOBAL),
        (load_project_config, ConfigScope.PROJECT),
        (load_user_config, ConfigScope.USER),
    ],
)
def test_load_scope_success(
    tmp_path: Path,
    loader,
    scope: ConfigScope,
) -> None:
    config_path = tmp_path / f"{scope.value}.yaml"
    _write_yaml(config_path, {"enabled": True})

    result = loader(config_path)

    assert is_ok(result)


def test_load_missing_file_returns_not_found(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"

    result = load_project_config(missing)

    assert is_err(result)
    error = result.err_value
    assert isinstance(error, ConfigNotFoundError)
    assert error.scope is ConfigScope.PROJECT
    assert error.expected_path == missing


def test_load_invalid_yaml(tmp_path: Path) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text("foo: [")

    result = load_global_config(path)

    assert is_err(result)
    error = result.err_value
    assert isinstance(error, ConfigYamlError)
    assert error.scope is ConfigScope.GLOBAL
    assert error.path == path
    assert error.message


def test_load_non_mapping_root(tmp_path: Path) -> None:
    path = tmp_path / "list.yaml"
    _write_yaml(path, ["not", "a", "mapping"])

    result = load_user_config(path)

    assert is_err(result)
    error = result.err_value
    assert isinstance(error, ConfigValidationError)
    assert error.scope is ConfigScope.USER
    assert error.message == "Configuration root must be a mapping of keys to values."


def test_load_handles_io_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "io.yaml"
    _write_yaml(path, {})

    original = Path.read_text

    def fake_read_text(self: Path, *args, **kwargs):
        if self == path:
            raise OSError("boom")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read_text, raising=False)

    result = load_global_config(path)

    assert is_err(result)
    error = result.err_value
    assert isinstance(error, ConfigIOError)
    assert error.scope is ConfigScope.GLOBAL
    assert error.path == path
    assert error.message == "boom"
