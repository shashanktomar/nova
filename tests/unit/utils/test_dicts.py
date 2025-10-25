from __future__ import annotations

from collections.abc import Mapping

from nova.utils.dicts import deep_merge


def test_deep_merge_merges_nested_mappings() -> None:
    base: Mapping[str, object] = {
        "feature": {"enabled": False, "retries": 2},
        "log": {"level": "INFO"},
    }
    override: Mapping[str, object] = {
        "feature": {"retries": 5, "mode": "fast"},
        "new": 42,
    }

    merged = deep_merge(base, override)

    assert merged == {
        "feature": {"enabled": False, "retries": 5, "mode": "fast"},
        "log": {"level": "INFO"},
        "new": 42,
    }
    # Ensure originals are untouched
    assert base["feature"] == {"enabled": False, "retries": 2}
    assert override["feature"] == {"retries": 5, "mode": "fast"}


def test_deep_merge_replaces_lists_by_default() -> None:
    merged = deep_merge({"items": [1, 2]}, {"items": [3, 4]})
    assert merged["items"] == [3, 4]


def test_deep_merge_uses_custom_list_strategy() -> None:
    def merge_by_name(key: str, base_list: list[object], override_list: list[object]) -> list[object]:
        assert key == "items"

        index = {entry["name"]: entry for entry in base_list}
        for entry in override_list:
            index[entry["name"]] = entry
        return list(index.values())

    merged = deep_merge(
        {"items": [{"name": "a", "value": 1}, {"name": "b", "value": 2}]},
        {"items": [{"name": "b", "value": 3}, {"name": "c", "value": 4}]},
        list_merge_strategy=merge_by_name,
    )

    assert merged["items"] == [
        {"name": "a", "value": 1},
        {"name": "b", "value": 3},
        {"name": "c", "value": 4},
    ]


def test_deep_merge_skips_none_values() -> None:
    merged = deep_merge({"feature": {"enabled": True}}, {"feature": None, "log": None})
    assert merged == {"feature": {"enabled": True}}
