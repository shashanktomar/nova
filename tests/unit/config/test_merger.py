from __future__ import annotations

from pathlib import Path

from nova.config.merger import merge_configs
from nova.config.models import GlobalConfig, NovaConfig, ProjectConfig, UserConfig


def test_merge_precedence_and_deep_merge() -> None:
    global_cfg = GlobalConfig.model_validate(
        {
            "section": {
                "value": 1,
                "nested": {"flag": False, "origin": "global"},
                "items": ["g1", "g2"],
            }
        }
    )
    project_cfg = ProjectConfig.model_validate(
        {
            "section": {
                "value": 2,
                "nested": {"extra": "project"},
                "items": ["p1"],
            }
        }
    )
    user_cfg = UserConfig.model_validate(
        {
            "section": {
                "nested": {"flag": True},
            }
        }
    )

    result = merge_configs(global_cfg, project_cfg, user_cfg)

    data = result.model_dump()
    assert data["section"]["value"] == 2
    assert data["section"]["nested"] == {"flag": True, "origin": "global", "extra": "project"}
    assert data["section"]["items"] == ["p1"]


def test_merge_none_configs_returns_empty() -> None:
    result = merge_configs(None, None, None)

    assert isinstance(result, NovaConfig)
    assert result.marketplaces == []
    assert result.logging.enabled is True
    assert result.logging.log_level == "INFO"


def test_merge_ignores_none_values() -> None:
    global_cfg = GlobalConfig.model_validate({"feature": {"enabled": True, "threshold": 10}})
    project_cfg = ProjectConfig.model_validate({"feature": {"enabled": None}})

    result = merge_configs(global_cfg, project_cfg, None)

    assert result.model_dump()["feature"] == {"enabled": True, "threshold": 10}


def test_merge_marketplaces_combines_scopes(tmp_path: Path) -> None:
    global_cfg = GlobalConfig.model_validate(
        {
            "marketplaces": [
                {
                    "name": "official",
                    "source": {"type": "github", "repo": "owner/official"},
                }
            ]
        }
    )

    local_marketplace_dir = tmp_path / "internal"
    local_marketplace_dir.mkdir()
    project_cfg = ProjectConfig.model_validate(
        {
            "marketplaces": [
                {
                    "name": "internal",
                    "source": {"type": "local", "path": str(local_marketplace_dir)},
                }
            ]
        }
    )

    result = merge_configs(global_cfg, project_cfg, None)

    names = [entry.name for entry in result.marketplaces]
    assert names == ["official", "internal"]
    assert result.marketplaces[0].source.type == "github"
    assert result.marketplaces[1].source.type == "local"
