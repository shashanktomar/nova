from __future__ import annotations

import pytest

from nova.config.models import ProjectConfig, UserConfig


def test_project_config_rejects_logging_section() -> None:
    with pytest.raises(
        ValueError,
        match="Logging configuration can only be set in global config",
    ):
        ProjectConfig.model_validate({"logging": {"enabled": False}})


def test_user_config_rejects_logging_section() -> None:
    with pytest.raises(
        ValueError,
        match="Logging configuration can only be set in global config",
    ):
        UserConfig.model_validate({"logging": {"enabled": False}})


def test_project_config_without_logging_is_valid() -> None:
    config = ProjectConfig.model_validate({"marketplaces": []})
    assert config.marketplaces == []


def test_user_config_without_logging_is_valid() -> None:
    config = UserConfig.model_validate({})
    assert config.model_dump() == {}
