# Python Testing Guidelines

## Core Principle: Test Public APIs, Not Private Implementation

**Tests should exercise the public API, not internal implementation details.**

This ensures:
- Tests verify actual user-facing behavior
- Tests remain stable when refactoring internals
- Tests don't break when you rename private functions or change internal structure

## Example: Testing Config Paths Module

### ❌ BAD: Testing Private Functions Directly

```python
# test_paths.py - DON'T DO THIS

from nova.config.paths import (
    get_global_config_path,    # ❌ Private helper
    get_project_config_path,   # ❌ Private helper
    get_user_config_path,      # ❌ Private helper
)

def test_get_global_config_path():
    """Testing private function directly."""
    path = get_global_config_path()
    assert path.exists()

def test_get_project_config_path():
    """Testing private function directly."""
    path = get_project_config_path()
    assert path is not None

def test_get_user_config_path():
    """Testing private function directly."""
    path = get_user_config_path()
    assert path is not None
```

**Problems:**
- Tests break when you rename `get_global_config_path()` to `_get_global_config_path()`
- Tests are coupled to implementation details
- Tests don't verify the actual public API works

### ✅ GOOD: Testing Through Public API

```python
# test_paths.py - DO THIS

from nova.config.paths import discover_config_paths  # ✅ Public API only

def test_discover_config_paths_finds_all_configs(temp_config_files):
    """Test discovering all config file locations."""
    global_path, project_path, user_path = discover_config_paths()

    assert global_path is not None
    assert project_path is not None
    assert user_path is not None

def test_discover_config_paths_returns_none_when_missing():
    """Test handling of missing config files."""
    with temp_empty_directory():
        global_path, project_path, user_path = discover_config_paths()

        assert project_path is None
        assert user_path is None
```

**Benefits:**
- Tests verify actual user behavior
- Can refactor internal helpers (`_get_global_config_path()`) without breaking tests
- Tests remain stable and meaningful

## When Private Testing Is Acceptable

**Rarely.** Only test private functions directly when:

1. **Complex algorithm** needing isolated validation
2. **Performance-critical code** requiring detailed benchmarking
3. **Security-critical logic** needing thorough edge case testing

**Always document why:**

```python
def test_internal_deep_merge_algorithm():
    """Test internal merge logic directly.

    NOTE: Testing private function because merge algorithm is complex
    and needs isolated validation. Public API tested separately in
    test_load_all_configs().
    """
    from nova.config.loader import _deep_merge

    result = _deep_merge(base, override)
    assert result == expected
```

## Summary

**Golden Rule:** If it starts with `_`, don't test it directly. Test it through the public function that uses it.

- Private function `_get_global_config_path()` → Test via `discover_config_paths()`
- Private function `_deep_merge()` → Test via `load_all_configs()`
- Private function `_convert_env_value()` → Test via `resolve_config()`

This keeps tests stable, meaningful, and focused on user-facing behavior.
