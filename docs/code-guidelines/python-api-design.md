# Python API Design Guidelines

## Public vs Private API Separation

### Core Principle

**Every module must have a clear, minimal public API.** Internal implementation details should be private and hidden from external callers.

### Two Levels of API Control

#### 1. File-Level API (Individual .py files)

Use **naming conventions only** - no `__all__` needed:

**Public Functions:**
- **No underscore prefix**
- Have comprehensive docstrings
- Considered stable - changes require versioning consideration
- **Placement:** Top of the file (after imports)

```python
# Public API - stable interface
def discover_config_paths() -> tuple[Path | None, Path | None, Path | None]:
    """Discover all Nova configuration file paths.

    This is the primary entry point for config path discovery.
    """
    global_path = _get_global_config_path()
    project_path = _find_project_config()
    user_path = _find_user_config(project_path)
    return global_path, project_path, user_path
```

**Private Functions:**
- **Single underscore prefix** (`_function_name`)
- May have minimal docstrings (focus on implementation notes)
- Can change freely without breaking external code
- **Placement:** Bottom of the file (after public functions)

```python
# Private helper - internal implementation detail
def _get_global_config_path(create_dir: bool = False) -> Path | None:
    """Internal helper to find global config path."""
    # Implementation...
```

#### 2. Module-Level API (__init__.py files)

Use **`__all__`** to explicitly control package exports:

```python
# src/nova/config/__init__.py
from nova.config.loader import load_all_configs
from nova.config.models import NovaConfig
from nova.config.resolver import resolve_config

# Explicitly control what the package exports
__all__ = [
    "NovaConfig",
    "get_config",
    "refresh_config",
]

# Module-level public functions
_config: NovaConfig | None = None

def get_config(reload: bool = False) -> NovaConfig:
    """Get cached config."""
    # Implementation...

def refresh_config() -> NovaConfig:
    """Force reload."""
    return get_config(reload=True)
```

#### 3. Cross-Module Import Rules

**Critical Principle:** External modules must ONLY import from a module's `__init__.py` public API, never from internal implementation files.

This respects module boundaries and enables the module to refactor internals without breaking external code.

```python
# ✅ GOOD - importing from module's public API
from nova.config import get_config, NovaConfig

# ❌ BAD - importing from internal implementation files
from nova.config.loader import load_config_file
from nova.config.paths import discover_config_paths
from nova.config.models import NovaConfig
from nova.config.resolver import resolve_config
```

**Why This Matters:**

1. **Respects Module Boundaries**
   - Module owns its internal structure
   - Can reorganize files without breaking external code
   - Clear contract between modules

2. **Enables Refactoring**
   - Rename internal files freely
   - Move functions between internal modules
   - Change internal APIs without external impact

3. **Enforces Encapsulation**
   - Only documented public API is accessible
   - Internal helpers remain truly private
   - Reduces coupling between modules

4. **Better Documentation**
   - One place to look for module API (`__init__.py`)
   - Clear what's supported vs internal
   - Easier onboarding for new developers

**Real Example - Feature 1 Violation:**

```python
# nova/cli/commands/config.py (CURRENT - WRONG)
from nova.config.loader import load_config_file      # ❌ Internal module
from nova.config.models import NovaConfig            # ❌ Internal module
from nova.config.paths import discover_config_paths  # ❌ Internal module

# This breaks encapsulation and couples CLI to config internals
```

```python
# nova/cli/commands/config.py (CORRECT)
from nova.config import get_config, get_config_by_scope  # ✅ Public API only

# Now config module can refactor internals without breaking CLI
```

**Exception:** Internal imports within the same module are fine:

```python
# Inside nova/config/loader.py - this is OK
from nova.config.paths import discover_config_paths  # ✅ Within same module
from .models import NovaConfig                        # ✅ Relative import
```

### File Organization

```python
"""Module docstring explaining public API."""

# Imports
from pathlib import Path
from typing import Optional

# Public API (top of file)
# =====================

def public_function_one() -> Result:
    """User-facing API with full documentation."""
    return _internal_helper()

def public_function_two() -> Result:
    """Another user-facing API."""
    return _another_helper()

# Private Implementation (bottom of file)
# =====================================

def _internal_helper() -> Result:
    """Internal helper - implementation detail."""
    # Can change freely without breaking public API
    pass

def _another_helper() -> Result:
    """Another internal helper."""
    pass
```

## Example: Config Paths Module

### ❌ BAD: Everything Public

```python
# paths.py - CURRENT IMPLEMENTATION (WRONG)

def get_global_config_path(create_dir: bool = True) -> Path:
    """Get global config path."""
    # Implementation...

def get_project_config_path(start_dir: Path | None = None) -> Path | None:
    """Find project config."""
    # Implementation...

def get_user_config_path(project_root: Path | None = None) -> Path | None:
    """Find user config."""
    # Implementation...

def discover_config_paths() -> tuple[Path | None, Path | None, Path | None]:
    """Discover all config paths."""
    global_path = get_global_config_path(create_dir=False)
    project_path = get_project_config_path()
    user_path = get_user_config_path()
    return global_path, project_path, user_path
```

**Problems:**
- All 4 functions are public (no underscore prefix) but only 1 should be
- Callers can bypass `discover_config_paths()` and call helpers directly
- Harder to refactor internal implementation
- Tests become coupled to implementation details

### ✅ GOOD: Clear Public/Private Separation

```python
# paths.py - CORRECTED IMPLEMENTATION

"""Configuration path discovery for Nova.

Public API:
    discover_config_paths() - Main entry point for finding config files
"""

from pathlib import Path

# Public API
# ==========

def discover_config_paths() -> tuple[Path | None, Path | None, Path | None]:
    """Discover all Nova configuration file paths.

    Searches for Nova configuration files in standard locations:
    1. Global config: XDG config directory (~/.config/nova/config.yaml)
    2. Project config: Current directory tree (.nova/config.yaml)
    3. User config: Home or project-specific (.nova/config.local.yaml)

    Returns:
        Tuple of (global_path, project_path, user_path) in precedence order.
        Any may be None if file doesn't exist.

    Example:
        >>> global_cfg, project_cfg, user_cfg = discover_config_paths()
        >>> if project_cfg:
        ...     print(f"Project config: {project_cfg}")
    """
    global_path = _get_global_config_path(create_dir=False)
    project_path = _find_project_config()
    user_path = _find_user_config(project_path)
    return global_path, project_path, user_path

# Private Implementation
# ======================

def _get_global_config_path(create_dir: bool = False) -> Path | None:
    """Internal: Get global config path using XDG spec."""
    # Implementation...

def _find_project_config(start_dir: Path | None = None) -> Path | None:
    """Internal: Search for project config up directory tree."""
    # Implementation...

def _find_user_config(project_root: Path | None = None) -> Path | None:
    """Internal: Find user-specific config."""
    # Implementation...
```

**Benefits:**
- Clear single entry point: `discover_config_paths()`
- Internal helpers can be refactored freely
- Tests focus on public behavior
- Self-documenting API boundary

## Module Design Patterns

### Single Public Entry Point Pattern

Best for modules with one main responsibility:

```python
# ✅ GOOD: One clear entry point
def load_all_configs() -> dict[str, Any]:
    """Load and merge all config files."""
    configs = [
        _load_global_config(),
        _load_project_config(),
        _load_user_config(),
    ]
    return _merge_configs(*configs)

# Private helpers below...
```

### Multiple Related Public Functions Pattern

When module provides several related operations:

```python
# ✅ GOOD: Related public operations
__all__ = [
    "get_config",      # Main operation
    "refresh_config",  # Secondary operation
    "load_config",     # Special case operation
]

def get_config(reload: bool = False) -> NovaConfig:
    """Primary API: Get cached config."""
    # Implementation...

def refresh_config() -> NovaConfig:
    """Secondary API: Force reload."""
    return get_config(reload=True)

def load_config(project_root: Path | None = None) -> NovaConfig:
    """Special case: Load from explicit path."""
    # Implementation...
```

### Class-Based Public API Pattern

When state management is needed:

```python
# ✅ GOOD: Class with clear public interface
class ConfigManager:
    """Manages Nova configuration.

    Public Methods:
        get() - Get current config
        reload() - Reload from disk
        validate() - Validate current config
    """

    def __init__(self):
        self._config: NovaConfig | None = None
        self._cache_time: float | None = None

    # Public methods (no underscore)
    def get(self) -> NovaConfig:
        """Get current configuration."""
        if self._config is None:
            self._load()
        return self._config

    def reload(self) -> NovaConfig:
        """Force reload from disk."""
        self._config = None
        return self.get()

    # Private methods (underscore prefix)
    def _load(self) -> None:
        """Internal: Load config from disk."""
        # Implementation...

    def _validate_cache(self) -> bool:
        """Internal: Check if cache is still valid."""
        # Implementation...
```

## Common Mistakes and Fixes

### Mistake 1: Exposing All Helper Functions

```python
# ❌ BAD: All helpers are public
def parse_yaml_file(path: Path) -> dict:
    """Parse YAML file."""
    pass

def merge_dicts(base: dict, override: dict) -> dict:
    """Merge two dicts."""
    pass

def load_config() -> dict:
    """Load config."""
    data = parse_yaml_file(path)
    return merge_dicts(defaults, data)
```

```python
# ✅ GOOD: Only main function is public
def load_config() -> dict:
    """Load configuration from file."""
    data = _parse_yaml_file(path)
    return _merge_dicts(defaults, data)

def _parse_yaml_file(path: Path) -> dict:
    """Internal: Parse YAML file."""
    pass

def _merge_dicts(base: dict, override: dict) -> dict:
    """Internal: Merge two dicts."""
    pass
```

### Mistake 2: Unclear What's Public

```python
# ❌ BAD: What's public? Unclear!
def function_one():
    pass

def function_two():
    pass

def function_three():
    pass
```

```python
# ✅ GOOD: Clear naming shows intent
def function_one():
    """Public API."""
    pass

def _function_two():
    """Internal helper."""
    pass

def _function_three():
    """Internal helper."""
    pass
```

### Mistake 3: Public Functions at Bottom

```python
# ❌ BAD: Public API buried at bottom
def _helper_one():
    pass

def _helper_two():
    pass

def _helper_three():
    pass

# Public API hidden way down here
def main_api():
    """The actual public function."""
    pass
```

```python
# ✅ GOOD: Public API immediately visible
def main_api():
    """The actual public function."""
    return _helper_one()

def _helper_one():
    pass

def _helper_two():
    pass
```

## Documentation Requirements

### Public Functions
- **Must** have comprehensive docstrings
- Include parameters, return types, examples
- Document exceptions that may be raised
- Explain purpose and usage

```python
def discover_config_paths() -> tuple[Path | None, Path | None, Path | None]:
    """Discover all Nova configuration file paths.

    Searches for Nova configuration files in standard locations following
    the XDG Base Directory specification for global config and walking
    up the directory tree for project config.

    Returns:
        Tuple of (global_path, project_path, user_path) in precedence order
        (lowest to highest priority). Any path may be None if the
        corresponding config file doesn't exist.

    Example:
        >>> global_cfg, project_cfg, user_cfg = discover_config_paths()
        >>> if project_cfg:
        ...     config = load_config_file(project_cfg)

    Note:
        The global config path is always searched but may not exist.
        Project and user configs are only found when in a Nova project.
    """
```

### Private Functions
- **May** have minimal docstrings
- Focus on implementation notes
- Document why it exists, not how to use it

```python
def _find_project_root(start_dir: Path) -> Path | None:
    """Internal: Walk up directory tree to find project root.

    Stops when finding .git directory or reaching filesystem root.
    """
```

## Migration Checklist

When refactoring existing code to proper public/private separation:

- [ ] Identify the true public API (what external code needs)
- [ ] Rename internal helpers with `_` prefix
- [ ] Move public functions to top of file
- [ ] Move private functions to bottom of file
- [ ] Update tests to use public API (see testing guidelines)
- [ ] Add/update docstrings for public functions
- [ ] Verify no external code uses private functions
- [ ] If working on `__init__.py`, add/update `__all__` to control package exports

## Summary

**Golden Rules:**

1. **One clear public API** - Minimize what's exposed
2. **Private by default** - Everything gets `_` prefix unless explicitly public
3. **Naming convention for files** - Use underscore prefix to indicate private (no `__all__` needed in .py files)
4. **`__all__` for packages** - Use `__all__` in `__init__.py` to control package exports
5. **Public first, private last** - File organization matters
6. **Document public thoroughly** - Private functions need less documentation

**Two-Level Control:**
- **File level (.py files)**: Naming convention with `_` prefix
- **Package level (__init__.py)**: Explicit `__all__` declaration

**Remember:** Public API is a contract. Once published, it's hard to change. Keep it minimal and well-designed from the start.

## See Also

- [Python Testing Guidelines](./python-testing-guidelines.md) - How to test public APIs
