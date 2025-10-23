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

## Parameterized Tests for Readability

**Use `@pytest.mark.parametrize` to make tests more readable and maintainable.**

### Benefits of Parameterized Tests

1. **Eliminates repetition** - One test function covers multiple cases
2. **Clear test matrix** - All test cases visible at a glance
3. **Better failure reporting** - pytest shows exactly which parameter failed
4. **Easier to add cases** - Just add to the parameter list
5. **Self-documenting** - Parameter names describe what's being tested

### Pattern: Extract Constants

Define reusable test constants at the module level:

```python
# At top of test file
VALID_NAME = "Ada Lovelace"
VALID_REPO = "owner/repo"
VALID_GIT_URL = "https://github.com/owner/repo.git"
VALID_EMAIL = "ada@example.com"
```

### Pattern: Valid Input Tests

Test multiple valid inputs with one parameterized test:

```python
# ❌ BAD: Repetitive tests
def test_contact_accepts_ada() -> None:
    contact = Contact(name="Ada Lovelace")
    assert contact.name == "Ada Lovelace"

def test_contact_accepts_grace() -> None:
    contact = Contact(name="Grace Hopper")
    assert contact.name == "Grace Hopper"

# ✅ GOOD: Parameterized test
@pytest.mark.parametrize("name", ["Ada Lovelace", "Grace Hopper"])
def test_contact_accepts_valid_name(name: str) -> None:
    contact = Contact(name=name)
    assert contact.name == name
```

### Pattern: Invalid Input Tests

Test multiple invalid inputs that should all raise ValidationError:

```python
# ❌ BAD: Repetitive validation tests
def test_contact_rejects_empty_email() -> None:
    with pytest.raises(ValidationError):
        Contact(name="Ada", email="")

def test_contact_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        Contact(name="Ada", email="not-an-email")

def test_contact_rejects_incomplete_email() -> None:
    with pytest.raises(ValidationError):
        Contact(name="Ada", email="@example.com")

# ✅ GOOD: Parameterized validation test
@pytest.mark.parametrize(
    "email",
    [
        "",
        "not-an-email",
        "@example.com",
        "user@",
    ],
)
def test_contact_rejects_invalid_email(email: str) -> None:
    with pytest.raises(ValidationError):
        Contact(name=VALID_NAME, email=email)
```

### Pattern: Multiple Parameters

Test combinations of inputs with descriptive names:

```python
@pytest.mark.parametrize(
    ("loader", "scope"),
    [
        (load_global_config, ConfigScope.GLOBAL),
        (load_project_config, ConfigScope.PROJECT),
        (load_user_config, ConfigScope.USER),
    ],
)
def test_load_scope_success(tmp_path: Path, loader, scope: ConfigScope) -> None:
    config_path = tmp_path / f"{scope.value}.yaml"
    write_yaml(config_path, {"enabled": True})

    result = loader(config_path)

    assert is_ok(result)
```

### Pattern: Custom Test IDs for Clarity

Use `ids` parameter to make test output more readable:

```python
@pytest.mark.parametrize(
    ("create_project", "nested_depth"),
    [
        (True, 0),
        (True, 3),
        (False, 2),
    ],
    ids=["project-root", "nested-deep", "no-project"],
)
def test_discover_paths_scenarios(create_project: bool, nested_depth: int) -> None:
    # Test implementation
    pass
```

### Pattern: Testing Empty/Invalid Fields

Use field names as parameters to test multiple fields with same validation:

```python
@pytest.mark.parametrize(
    "field_name",
    ["description", "source", "name"],
)
def test_bundle_entry_requires_non_empty_fields(field_name: str) -> None:
    kwargs = {
        "name": "bundle",
        "description": "A useful bundle",
        "source": "./bundles/bundle",
    }
    kwargs[field_name] = ""  # Make this field empty

    with pytest.raises(ValidationError):
        BundleEntry(**kwargs)
```

### When NOT to Parameterize

Don't parameterize when:

1. **Test logic differs significantly** between cases
2. **Setup/assertions are different** for each case
3. **Single case** is sufficient
4. **Readability suffers** from parameterization

```python
# ❌ BAD: Over-parameterized when logic differs
@pytest.mark.parametrize(
    ("input", "expected", "description"),
    [
        ({"a": 1}, {"a": 1}, "simple"),
        ({"a": {"b": 2}}, {"a": {"b": 2}}, "nested"),
        ([1, 2, 3], None, "invalid"),  # Different assertion needed!
    ],
)
def test_complex_cases(input, expected, description) -> None:
    result = process(input)
    assert result == expected  # Breaks for invalid case

# ✅ GOOD: Separate tests when logic differs
def test_process_simple_dict() -> None:
    assert process({"a": 1}) == {"a": 1}

def test_process_nested_dict() -> None:
    assert process({"a": {"b": 2}}) == {"a": {"b": 2}}

def test_process_rejects_list() -> None:
    with pytest.raises(ValidationError):
        process([1, 2, 3])
```

## Summary

**Golden Rule:** If it starts with `_`, don't test it directly. Test it through the public function that uses it.

- Private function `_get_global_config_path()` → Test via `discover_config_paths()`
- Private function `_deep_merge()` → Test via `load_all_configs()`
- Private function `_convert_env_value()` → Test via `resolve_config()`

**Parameterization Rule:** Use `@pytest.mark.parametrize` when testing the same logic with different inputs to improve readability and maintainability.

This keeps tests stable, meaningful, and focused on user-facing behavior.
