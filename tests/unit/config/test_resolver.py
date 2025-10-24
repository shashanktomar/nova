from __future__ import annotations

import os

import pytest

from nova.config.models import NovaConfig
from nova.config.resolver import apply_env_overrides


@pytest.fixture(autouse=True)
def _clear_config_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ.keys()):
        if key.startswith("NOVA_CONFIG__"):
            monkeypatch.delenv(key, raising=False)


# FIX: Make this test parameterized like in other test classes.
def test_apply_env_overrides_updates_nested_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    base = NovaConfig.model_validate(
        {
            "feature": {
                "enabled": False,
                "threshold": 10,
                "metadata": {"source": "base"},
            },
            "items": [1, 2, 3],
        }
    )

    monkeypatch.setenv("NOVA_CONFIG__FEATURE__ENABLED", "true")
    monkeypatch.setenv("NOVA_CONFIG__FEATURE__THRESHOLD", "20")
    monkeypatch.setenv("NOVA_CONFIG__FEATURE__METADATA__SOURCE", "env")
    monkeypatch.setenv("NOVA_CONFIG__ITEMS", "[4, 5]")

    resolved = apply_env_overrides(base)

    data = resolved.model_dump()
    assert data["feature"]["enabled"] is True
    assert data["feature"]["threshold"] == 20
    assert data["feature"]["metadata"]["source"] == "env"
    assert data["items"] == [4, 5]


def test_apply_env_overrides_no_env_returns_original() -> None:
    base = NovaConfig.model_validate({"feature": {"enabled": False}})

    resolved = apply_env_overrides(base)

    assert resolved == base
