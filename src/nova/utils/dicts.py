"""Dictionary helpers used across Nova."""

from __future__ import annotations

from collections.abc import Callable, Mapping

ListMergeStrategy = Callable[[str, list[object], list[object]], list[object]]

__all__ = ["ListMergeStrategy", "deep_merge"]


def deep_merge(
    base: Mapping[str, object],
    override: Mapping[str, object],
    *,
    list_merge_strategy: ListMergeStrategy | None = None,
) -> dict[str, object]:
    """Recursively merge two mappings, giving precedence to override."""
    result: dict[str, object] = dict(base)

    for key, override_value in override.items():
        if override_value is None:
            continue

        existing_value = result.get(key)

        if isinstance(existing_value, Mapping) and isinstance(override_value, Mapping):
            result[key] = deep_merge(
                dict(existing_value),
                dict(override_value),
                list_merge_strategy=list_merge_strategy,
            )
        elif isinstance(existing_value, list) and isinstance(override_value, list):
            if list_merge_strategy is not None:
                result[key] = list_merge_strategy(
                    key,
                    list(existing_value),
                    list(override_value),
                )
            else:
                result[key] = list(override_value)
        else:
            result[key] = override_value

    return result
