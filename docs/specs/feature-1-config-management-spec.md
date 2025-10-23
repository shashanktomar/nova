---
status: completed
priority: p0
updated: "2025-10-23"
implemented: "2025-10-21"
review_status: "implemented"
---

# Feature 1: Configuration Management - Technical Specification

**Status:** ✅ Completed
**Priority:** P0 (Must Have)
**Last Updated:** 2025-10-23 (Updated with ConfigStore protocol)

## Overview

This specification defines the technical implementation for Nova's configuration management system, which supports multi-layer configuration with clear precedence rules and schema validation.

### Goals

- Provide a clean, minimal public API for configuration access
- Support three configuration scopes: global, project, and user
- Enable environment variable overrides
- Use Result types for predictable error handling
- Support schema validation with clear error reporting
- Implement singleton pattern for performance

### Non-Goals

- Runtime configuration updates (config is loaded once and cached)
- Configuration encryption or secrets management (defer to environment variables)
- Configuration migration/versioning (forward compatibility via schema evolution)

## Public API Contract

The `nova.config` module provides a protocol-based API that abstracts configuration storage. The primary abstraction is the `ConfigStore` protocol, with `FileConfigStore` as the file-based implementation.

### Design Philosophy

- **Protocol-based abstraction**: Configuration storage is abstracted behind `ConfigStore` protocol
- **Implementation flexibility**: Users can implement custom stores (database, remote, in-memory)
- **No caching**: FileConfigStore reads from disk every time for simplicity and freshness
- **Validation is automatic**: No separate validation API needed
- **Errors contain context**: All errors include scope information for debugging
- **Dependency injection**: Feature modules accept `ConfigStore` instances

### Module Exports

```python
# nova/config/__init__.py

__all__ = [
    "ConfigScope",
    "NovaConfig",
    "ConfigError",
    "ConfigNotFoundError",
    "ConfigYamlError",
    "ConfigValidationError",
    "ConfigIOError",
    "ConfigStore",        # Protocol
    "FileConfigStore",    # Implementation
]
```

### Enums

```python
class ConfigScope(str, Enum):
    """Configuration scope levels."""
    GLOBAL = "global"      # ~/.config/nova/config.yaml
    PROJECT = "project"    # .nova/config.yaml
    USER = "user"          # .nova/config.local.yaml
    EFFECTIVE = "effective"  # Merged result with env overrides
```

### Error Models

All error models are Pydantic BaseModel subclasses for type safety and validation.

```python
class ConfigNotFoundError(BaseModel):
    """Configuration file not found at expected location."""
    scope: ConfigScope
    expected_path: Path
    message: str


class ConfigYamlError(BaseModel):
    """YAML parsing error in configuration file."""
    scope: ConfigScope
    path: Path
    line: Optional[int]
    column: Optional[int]
    message: str


class ConfigValidationError(BaseModel):
    """Schema validation error in configuration."""
    scope: ConfigScope
    path: Path
    field: Optional[str]
    message: str


class ConfigIOError(BaseModel):
    """File I/O error reading configuration."""
    scope: ConfigScope
    path: Path
    message: str


# Union of all config errors
type ConfigError = (
    ConfigNotFoundError
    | ConfigYamlError
    | ConfigValidationError
    | ConfigIOError
)
```

### Data Models

Nova uses separate models for each configuration scope that merge into a single effective model.

```python
class GlobalConfig(BaseModel):
    """Global configuration (~/.config/nova/config.yaml).

    User-wide settings that apply to all Nova projects.
    All fields are optional - provides defaults that can be overridden.
    """
    # Fields TBD - will be defined as features are implemented
    pass


class ProjectConfig(BaseModel):
    """Project configuration (.nova/config.yaml).

    Project-specific settings shared by all developers.
    Committed to version control.
    All fields are optional at parse time.
    """
    # Fields TBD - will be defined as features are implemented
    pass


class UserConfig(BaseModel):
    """User configuration (.nova/config.local.yaml).

    Personal overrides for local development.
    NOT committed to version control.
    All fields are optional - only contains overrides.
    """
    # Fields TBD - will be defined as features are implemented
    pass


class NovaConfig(BaseModel):
    """Effective configuration (merged result).

    Final configuration after merging global, project, and user configs
    with environment variable overrides applied.

    This is the model returned by parse_config() and used by all consumers.
    Field requirements (required vs optional) TBD based on feature needs.
    """
    # Fields TBD - will be defined as features are implemented
    pass
```

### ConfigStore Protocol

The core abstraction for configuration storage and retrieval:

```python
from typing import Protocol
from nova.utils.functools.models import Result

class ConfigStore(Protocol):
    """Protocol for configuration storage and retrieval."""

    def load(self) -> Result[NovaConfig, ConfigError]:
        """Load merged configuration."""
        ...
```

### FileConfigStore Implementation

File-based implementation of the ConfigStore protocol:

```python
class FileConfigStore:
    """File-based configuration store using YAML files.

    Implements the ConfigStore protocol for file-based configuration.
    """

    def __init__(self, working_dir: Path | None = None) -> None:
        """Initialize file config store.

        Args:
            working_dir: Directory to start searching for project config.
                        Defaults to current working directory (Path.cwd()).
                        Used to find .nova/config.yaml by walking up the tree.
        """
        ...

    def load(self) -> Result[NovaConfig, ConfigError]:
        """Load and validate effective configuration from YAML files.

        This method:
        1. Discovers config files in all scopes (global, project, user)
        2. Loads and parses YAML from each scope
        3. Validates each scope against schema
        4. Merges configs with precedence: env > user > project > global
        5. Applies environment variable overrides
        6. Returns the final validated configuration

        Reads from disk on every call - no caching for simplicity and freshness.

        Returns:
            Result[NovaConfig, ConfigError]:
                - Ok(config): Successfully loaded and validated configuration
                - Err(ConfigNotFoundError): Explicitly requested config scope missing (rare)
                - Err(ConfigYamlError): YAML syntax error (includes scope, line, column)
                - Err(ConfigValidationError): Schema validation failed (includes scope, field)
                - Err(ConfigIOError): File system error reading config

        Error Context:
            All errors include the `scope` field indicating which config file failed
            (global, project, or user), enabling users to locate and fix the issue.

        Example:
            # Normal usage (current directory)
            store = FileConfigStore()
            result = store.load()
            if result.is_ok():
                config = result.ok()
                # Use config fields as defined by NovaConfig model
            else:
                error = result.err()
                print(f"Config error in {error.scope}: {error.message}")

            # Explicit working directory (useful for testing)
            store = FileConfigStore(working_dir=Path("/path/to/project"))
            result = store.load()

        Note:
            If no configuration files are discovered, the method still returns `Ok`
            with an empty `NovaConfig` using default values.
        """
        ...
```

### Usage Examples

**CLI Usage (File-based):**
```python
from nova.config import FileConfigStore

store = FileConfigStore()
result = store.load()
```

**Library Usage (Custom Store):**
```python
from nova.config import ConfigStore, NovaConfig, ConfigError
from nova.utils.functools.models import Result, Ok

class DatabaseConfigStore:
    """Custom config store backed by database."""

    def load(self) -> Result[NovaConfig, ConfigError]:
        # Load config from database
        data = database.query("SELECT * FROM config")
        config = NovaConfig.model_validate(data)
        return Ok(config)

# Use custom store
store = DatabaseConfigStore()
result = store.load()
```

## CLI Commands

```bash
# Show effective configuration (merged from all scopes)
nova config show

# Show in JSON format
nova config show --format json
```

## Configuration Merging

The `parse_config()` function merges configurations from multiple scopes into a single `NovaConfig`:

### Merging Process

1. **Parse each scope independently**:

   - Parse global YAML → `GlobalConfig`
   - Parse project YAML → `ProjectConfig`
   - Parse user YAML → `UserConfig`

2. **Validate each scope** against its model schema

3. **Merge into effective config** with precedence order:

   - Start with global config (lowest priority)
   - Overlay project config
   - Overlay user config (highest priority)
   - Apply environment variable overrides

4. **Convert to `NovaConfig`** and validate final result

### Merging Rules

- **Field-level merging**: Config merges at the field level, not file level
- **Deep merging**: Nested objects are merged recursively
- **List replacement**: Lists are replaced entirely, not merged
- **None values**: `None` or missing fields don't override existing values

### Example

```yaml
# Global: ~/.config/nova/config.yaml
section_a:
  field_1: value_from_global
  field_2: 100
section_b:
  enabled: true

# Project: .nova/config.yaml
section_a:
  field_1: value_from_project  # Overrides global
section_c:
  name: example

# User: .nova/config.local.yaml
section_a:
  field_2: 200  # Overrides global, keeps project's field_1

# Effective result (NovaConfig):
section_a:
  field_1: value_from_project  # From project
  field_2: 200                 # From user
section_b:
  enabled: true                # From global
section_c:
  name: example                # From project
```

**Note**: The internal scope models (`GlobalConfig`, `ProjectConfig`, `UserConfig`) are not exported from the public API. Only `NovaConfig` is exposed.

## Internal Module Structure

```
nova/config/
├── __init__.py          # Public API: ConfigStore, FileConfigStore
├── protocol.py          # ConfigStore protocol definition
├── models.py            # All Pydantic models and error types
├── merger.py            # Config merging with precedence
├── resolver.py          # Environment variable resolution
└── file/                # File-based implementation
    ├── __init__.py      # Exports FileConfigStore
    ├── store.py         # FileConfigStore implementation
    └── paths.py         # Config file path discovery
```

### Module APIs

#### `protocol.py`

```python
class ConfigStore(Protocol):
    """Protocol for configuration storage and retrieval."""

    def load(self) -> Result[NovaConfig, ConfigError]:
        """Load merged configuration."""
```

#### `models.py`

```python
class GlobalConfig(BaseModel):
    """Global scope configuration"""

class ProjectConfig(BaseModel):
    """Project scope configuration"""

class UserConfig(BaseModel):
    """User scope configuration"""

class NovaConfig(BaseModel):
    """Effective merged configuration"""

# Error models
class ConfigNotFoundError(BaseModel): ...
class ConfigYamlError(BaseModel): ...
class ConfigValidationError(BaseModel): ...
class ConfigIOError(BaseModel): ...
```

#### `file/store.py`

```python
class FileConfigStore:
    """File-based configuration store using YAML files."""

    def __init__(self, working_dir: Path | None = None) -> None:
        """Initialize with optional working directory."""

    def load(self) -> Result[NovaConfig, ConfigError]:
        """Load merged configuration from YAML files."""

    # Private methods
    def _load_optional(...) -> Result[T | None, ConfigError]:
        """Load optional config scope."""

    def _load_scope_config(...) -> Result[T, ConfigError]:
        """Load and validate a single scope's config."""
```

#### `file/paths.py`

```python
@dataclass
class ConfigPaths:
    global_path: Path | None
    project_path: Path | None
    user_path: Path | None

def discover_config_paths(working_dir: Path | None = None) -> ConfigPaths:
    """Discover all configuration file paths from working directory."""
```

#### `merger.py`

```python
def merge_configs(
    global_cfg: GlobalConfig | None,
    project_cfg: ProjectConfig | None,
    user_cfg: UserConfig | None
) -> NovaConfig:
    """Merge configs with precedence: user > project > global."""
```

#### `resolver.py`

```python
def apply_env_overrides(config: NovaConfig) -> NovaConfig:
    """Apply environment variable overrides to config."""
```

#### `__init__.py`

```python
# Public exports
__all__ = [
    "ConfigStore",
    "FileConfigStore",
    "NovaConfig",
    "ConfigError",
    ...
]

from .protocol import ConfigStore
from .file import FileConfigStore
from .models import NovaConfig, ConfigError, ...
```

### Data Flow

```
FileConfigStore.load()
  ↓
discover_config_paths()
  ↓
_load_scope_config() for each scope (global, project, user)
  ↓
merge_configs()
  ↓
apply_env_overrides()
  ↓
Result[NovaConfig, ConfigError]
```

## Implementation Checklist

- [x] Define ConfigStore protocol
- [x] Define NovaConfig schema (with marketplace support)
- [x] Implement FileConfigStore
- [x] Implement path discovery
- [x] Implement YAML loading (within FileConfigStore)
- [x] Implement configuration merging
- [x] Implement environment variable resolution
- [x] Implement validation
- [x] Write comprehensive tests (85 tests passing)
- [x] Update CLI commands to use FileConfigStore
- [x] Document usage patterns
- [x] Update ADR-002 with ConfigStore protocol
- [ ] Add examples for custom ConfigStore implementations

## References

- [Feature 1 PRD](../explore/prd/3-features-requirements/feature-1-config-management.md)
- [ADR-001: CLI Business Logic Separation](../architecture/adr-001-cli-business-logic-separation.md)
- [Python API Design Guidelines](../code-guidelines/python-api-design.md)
- [Functional Error Handling Guidelines](../code-guidelines/functools-result.md)
