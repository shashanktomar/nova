# Feature 1: Config Management - Implementation Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Updated:** 2025-10-19
**Author:** AI Architecture Team (zen-architect)

## Overview

This specification defines the complete implementation for Nova's configuration management system (Feature 1, P0 priority). It follows the "bricks and studs" modular design philosophy - each module is a self-contained brick with clear contracts (studs) that can be independently generated and regenerated.

## Architecture Summary

**Approach:** Pydantic-Native Configuration System

**Key Decisions:**
- Use Pydantic models as schema definition (leverages existing dependency, type-safe)
- YAML for config files (human-friendly, widely supported)
- Singleton pattern for config access (simple for 99% of use cases)
- Environment variable override convention: `NOVA_SECTION_KEY`
- Lazy loading with caching (load on first access)
- No config file watching (keep simple - restart to reload)

**Precedence Order (highest to lowest):**
1. Environment variables (`NOVA_*`)
2. User config (`.nova/config.local.yaml`)
3. Project config (`.nova/config.yaml`)
4. Global config (`$XDG_CONFIG_HOME/nova/config.yaml` or `~/.config/nova/config.yaml`)

## Module Structure

```
src/nova/
├── config/
│   ├── __init__.py       # Public API exports
│   ├── models.py         # Pydantic config models (schema)
│   ├── loader.py         # Config loading and merging logic
│   ├── resolver.py       # Environment variable resolution
│   └── paths.py          # Config file path utilities
└── cli/
    └── commands/
        └── config.py     # CLI config commands
```

---

## Module Specifications

### Module: config.models

**Purpose:** Define configuration schema using Pydantic models

**Location:** `src/nova/config/models.py`

**Contract:**
- **Inputs:** Dictionary data from YAML files
- **Outputs:** Validated Pydantic model instances
- **Side Effects:** None (pure data models)
- **Dependencies:** pydantic, typing

**Public Interface:**

```python
from pydantic import BaseModel, ConfigDict

class NovaConfig(BaseModel):
    """Root configuration model for Nova

    This model uses additive schema evolution:
    - Fields are added as features are implemented
    - All fields are optional with sensible defaults
    - Old configs work with new Nova versions
    - No explicit version field needed

    Schema Evolution Strategy:
    - Never remove fields (only deprecate)
    - Never change field meaning (add new field instead)
    - Only add optional fields with defaults
    - Tool version determines parsing behavior

    Future fields will be added here as features are implemented:
    - bundles: BundlesConfig | None = None
    - marketplace: MarketplaceConfig | None = None
    - context: ContextConfig | None = None
    """
    model_config = ConfigDict(extra="allow")

    # Currently no required fields - all future fields will be optional
    # This allows empty config files to be valid
```

**Validation Rules:**
- `extra="allow"` - Accept unknown config keys (forwards compatibility for future features)
- Currently no required fields - empty config is valid
- All future fields will be optional with sensible defaults
- Store unknown fields as-is for forward compatibility
- Provide helpful field descriptions for documentation

**Schema Evolution Philosophy:**
- Follow industry patterns (npm, Cargo, Python packaging)
- Additive-only changes (never remove or change field meaning)
- Tool version drives parsing behavior
- No explicit config version field needed
- Breaking changes only via major Nova version bumps

**Testing Requirements:**
- Unit tests for model validation (valid inputs, invalid inputs)
- Test that unknown keys are accepted and preserved
- Test that empty config (`{}`) is valid
- Test that additional fields are accessible via model_dump()
- Test forward compatibility (fields from "future" versions ignored gracefully)

---

### Module: config.paths

**Purpose:** Manage configuration file paths and discovery

**Location:** `src/nova/config/paths.py`

**Contract:**
- **Inputs:** None (uses environment and filesystem)
- **Outputs:** Path objects for config locations
- **Side Effects:**
  - Reads filesystem to find project root
  - May create `~/.config/nova/` directory if needed
- **Dependencies:** pathlib, os

**Public Interface:**

```python
from pathlib import Path
from typing import Optional

def get_global_config_path(create_dir: bool = True) -> Path:
    """Get path to global config file using XDG Base Directory spec.

    Args:
        create_dir: If True, create config directory if it doesn't exist

    Returns:
        Path to $XDG_CONFIG_HOME/nova/config.yaml
        or ~/.config/nova/config.yaml if XDG_CONFIG_HOME not set

    Side Effects:
        May create config directory

    Algorithm:
        1. Check for XDG_CONFIG_HOME environment variable
        2. If set: use $XDG_CONFIG_HOME/nova/config.yaml
        3. If not: use ~/.config/nova/config.yaml (XDG default)
        4. Create directory if create_dir=True
    """
    pass

def get_project_config_path(start_dir: Path | None = None) -> Path | None:
    """Find project config by searching up directory tree.

    Args:
        start_dir: Directory to start search from (default: cwd)

    Returns:
        Path to .nova/config.yaml if found, None otherwise

    Algorithm:
        1. Start from start_dir (or cwd)
        2. Check for .nova/config.yaml
        3. Move up one directory
        4. Repeat until found or reach filesystem root
    """
    pass

def get_user_config_path(project_root: Path | None = None) -> Path | None:
    """Get path to user-specific config file.

    Args:
        project_root: Project root directory (uses get_project_config_path if None)

    Returns:
        Path to .nova/config.local.yaml if project found, None otherwise
    """
    pass

def discover_config_paths() -> tuple[Path | None, Path | None, Path | None]:
    """Discover all config file paths.

    Returns:
        Tuple of (global_path, project_path, user_path)
        Any may be None if not found/applicable
    """
    pass
```

**Implementation Notes:**
- Use `os.environ.get('XDG_CONFIG_HOME')` for XDG config directory
- Fall back to `Path.home() / '.config'` if XDG_CONFIG_HOME not set
- Use `Path.cwd()` as default start directory for project search
- Search up to filesystem root (stop when `path.parent == path`)
- Global config path always exists (create directory if needed)
- Project/user paths may be None if not in a Nova project

**Testing Requirements:**
- Test global path creation
- Test project path discovery (found, not found)
- Test user path construction
- Test directory tree traversal logic
- Mock filesystem for isolation

---

### Module: config.loader

**Purpose:** Load and merge YAML configuration files

**Location:** `src/nova/config/loader.py`

**Contract:**
- **Inputs:** Path objects to config files
- **Outputs:** Merged configuration dictionary
- **Side Effects:** Reads files from filesystem
- **Dependencies:** yaml, pathlib, typing

**Public Interface:**

```python
from pathlib import Path
from typing import Any

def load_config_file(path: Path) -> dict[str, Any]:
    """Load a single YAML config file.

    Args:
        path: Path to YAML config file

    Returns:
        Dictionary of config values (empty dict if file doesn't exist)

    Raises:
        ConfigError: If YAML is invalid or file cannot be read

    Notes:
        - Returns {} if file doesn't exist (not an error)
        - Uses safe YAML loading only
    """
    pass

def merge_configs(*configs: dict[str, Any]) -> dict[str, Any]:
    """Deep merge multiple config dictionaries.

    Args:
        *configs: Config dictionaries in precedence order (lowest to highest)

    Returns:
        Single merged dictionary

    Algorithm:
        For each key in configs (right to left):
            - If value is dict: recursively merge
            - If value is list: replace (don't merge lists)
            - Otherwise: use rightmost (highest precedence) value

    Example:
        global = {"bundles": {"search_paths": ["/global"]}}
        project = {"bundles": {"search_paths": ["/project"]}}
        merged = merge_configs(global, project)
        # Result: {"bundles": {"search_paths": ["/project"]}}
    """
    pass

def load_all_configs() -> dict[str, Any]:
    """Load and merge all config files.

    Returns:
        Merged configuration dictionary

    Process:
        1. Discover config file paths
        2. Load global config (or {})
        3. Load project config (or {})
        4. Load user config (or {})
        5. Merge with precedence: user > project > global
    """
    pass
```

**Merge Strategy:**
- Dictionaries: Deep merge (recursive)
- Lists: Replace (highest precedence wins, no concatenation)
- Primitives: Replace (highest precedence wins)
- Missing files: Treat as empty dict (not an error)

**Error Handling:**
- Wrap YAML errors with helpful context
- Include file path in error messages
- Provide suggestions for common YAML mistakes

**Testing Requirements:**
- Test loading valid YAML
- Test loading invalid YAML (syntax errors)
- Test loading non-existent file (should return {})
- Test deep merge logic
- Test list replacement (not concatenation)
- Test nested dictionary merging
- Test primitive value replacement

---

### Module: config.resolver

**Purpose:** Resolve final configuration with environment variable overrides

**Location:** `src/nova/config/resolver.py`

**Contract:**
- **Inputs:** Merged config dictionary, environment variables
- **Outputs:** Validated NovaConfig instance
- **Side Effects:** Reads from os.environ
- **Dependencies:** os, pydantic, config.models

**Public Interface:**

```python
import os
from typing import Any
from nova.config.models import NovaConfig

def get_env_overrides() -> dict[str, Any]:
    """Extract Nova config overrides from environment variables.

    Returns:
        Dictionary of config overrides from env vars

    Environment Variable Convention:
        NOVA_SECTION_KEY=value

    Examples:
        NOVA_BUNDLES_SEARCH_PATHS=/custom:/another
        NOVA_CONTEXT_MAX_SIZE_KB=2048

    Type Conversion:
        - Paths with : separator -> list of paths
        - Numeric strings -> int
        - "true"/"false" -> bool
        - Otherwise -> string

    Algorithm:
        1. Find all env vars starting with NOVA_
        2. Parse NOVA_SECTION_KEY format
        3. Convert to nested dict structure
        4. Apply type conversions
    """
    pass

def resolve_config(merged: dict[str, Any]) -> NovaConfig:
    """Apply environment overrides and validate config.

    Args:
        merged: Merged config from all file sources

    Returns:
        Validated NovaConfig instance

    Raises:
        ValidationError: If final config is invalid

    Process:
        1. Get environment variable overrides
        2. Deep merge env overrides into merged config
        3. Parse with Pydantic (validates and type-checks)
        4. Return validated NovaConfig instance
    """
    pass
```

**Environment Variable Naming:**
- Format: `NOVA_{SECTION}_{KEY}` (uppercase, underscores)
- Section: Top-level config key (bundles, context, etc.)
- Key: Nested key within section (search_paths, max_size_kb, etc.)
- Multi-level nesting: `NOVA_SECTION_SUBSECTION_KEY`

**Type Conversion Rules:**
- Lists: Colon-separated values (`:` delimiter)
- Integers: Numeric strings converted to int
- Booleans: "true"/"false" (case-insensitive)
- Paths: Expanded with `~` and environment variables
- JSON: Support `NOVA_*_JSON` suffix for complex types

**Testing Requirements:**
- Test env var discovery (find NOVA_* vars)
- Test name parsing (NOVA_SECTION_KEY format)
- Test type conversions (list, int, bool, path)
- Test deep merge with env overrides
- Test validation errors are surfaced
- Test precedence (env > user > project > global)

---

### Module: config (Main API)

**Purpose:** Public API for Nova configuration system

**Location:** `src/nova/config/__init__.py`

**Contract:**
- **Inputs:** None (discovers and loads automatically)
- **Outputs:** NovaConfig instance (cached singleton)
- **Side Effects:**
  - Loads config files on first access
  - Caches result for subsequent calls
- **Dependencies:** All other config modules

**Public Interface:**

```python
from nova.config.models import NovaConfig, BundlesConfig, ContextConfig
from nova.config.resolver import resolve_config
from nova.config.loader import load_all_configs

# Global cached instance
_config: NovaConfig | None = None

def get_config(reload: bool = False) -> NovaConfig:
    """Get the Nova configuration (singleton pattern).

    Args:
        reload: If True, reload config from files (default: use cache)

    Returns:
        Validated NovaConfig instance

    Notes:
        - First call loads and caches config
        - Subsequent calls return cached instance
        - Use reload=True to force reload (rare)
    """
    global _config
    if _config is None or reload:
        merged = load_all_configs()
        _config = resolve_config(merged)
    return _config

def load_config(project_root: Path | None = None, reload: bool = True) -> NovaConfig:
    """Load configuration with explicit project root.

    Args:
        project_root: Explicit project root (for testing/special cases)
        reload: Whether to force reload (default: True)

    Returns:
        Validated NovaConfig instance

    Notes:
        - Use for testing or explicit control
        - Most code should use get_config() instead
    """
    pass

def refresh_config() -> NovaConfig:
    """Refresh configuration from files.

    Returns:
        Newly loaded NovaConfig instance

    Shorthand for: get_config(reload=True)
    """
    return get_config(reload=True)

# Re-export models for convenience
__all__ = [
    "NovaConfig",
    "get_config",
    "load_config",
    "refresh_config",
]
```

**Usage Examples:**

```python
# Simple usage (99% of cases)
from nova.config import get_config

config = get_config()
all_config = config.model_dump()  # Get all config as dict

# Access config sections (when implemented)
# if hasattr(config, 'bundles'):
#     bundles = config.bundles

# Testing with specific project root
from nova.config import load_config

config = load_config(project_root=Path("/test/project"))

# Force reload after external changes
from nova.config import refresh_config

config = refresh_config()
```

**Testing Requirements:**
- Test singleton behavior (same instance returned)
- Test caching (no reload without flag)
- Test reload functionality
- Test integration with all modules
- Mock filesystem for isolation

---

## CLI Command Specifications

**Location:** `src/nova/cli/commands/config.py`

### Command: `nova config show`

**Purpose:** Display resolved configuration

**Usage:**
```bash
nova config show                    # Show all config (effective)
nova config show --scope global     # Show only global config
nova config show --scope project    # Show only project config
nova config show --scope user       # Show only user config
nova config show --format yaml      # Output as YAML (default)
nova config show --format json      # Output as JSON
```

**Options:**
- `--scope`: Filter to specific scope (global|project|user|effective)
- `--format`: Output format (yaml|json)

**Output:**
- YAML or JSON representation of config
- Include source annotation for each value in effective view
- Clear indication if scope doesn't exist (e.g., no project config)

**Implementation:**
```python
import typer
from nova.config import get_config
from nova.config.loader import load_config_file
from nova.config.paths import discover_config_paths

def show(
    scope: str = typer.Option("effective", help="Config scope to show"),
    format: str = typer.Option("yaml", help="Output format"),
) -> None:
    """Show configuration values."""
    if scope == "effective":
        config = get_config()
        # Show merged config with source annotations
    else:
        paths = discover_config_paths()
        # Load specific scope file
```

---

### Command: `nova config validate`

**Purpose:** Validate configuration files

**Usage:**
```bash
nova config validate                # Validate all config files
nova config validate --scope global # Validate specific scope
```

**Options:**
- `--scope`: Validate specific scope only

**Output:**
- Success message if valid
- Detailed error messages if invalid
- File path and line number for errors (if possible)
- Exit code 0 for valid, 1 for invalid

**Implementation:**
```python
def validate(
    scope: str = typer.Option("all", help="Scope to validate"),
) -> None:
    """Validate configuration files."""
    try:
        config = get_config()
        typer.echo("✓ Configuration is valid")
    except ValidationError as e:
        # Format and display validation errors
        typer.echo(f"✗ Configuration is invalid:\n{e}", err=True)
        raise typer.Exit(1)
```

---

## Example Configuration Files

### Global Config (`$XDG_CONFIG_HOME/nova/config.yaml` or `~/.config/nova/config.yaml`)

```yaml
# Placeholder sections - will be defined by future features
# These are examples showing the config system works with any key-value pairs
# Note: Empty config file is also valid!

example_section:
  # Example string setting
  api_url: "https://api.example.com"

  # Example list setting
  search_paths:
    - "/usr/local/share/nova"
    - "~/.local/share/nova"

  # Example number setting
  timeout_seconds: 30

  # Example boolean setting
  enabled: true
```

### Project Config (`.nova/config.yaml`)

```yaml
# Project-specific placeholder configuration
example_section:
  # Override global API URL for this project
  api_url: "https://project-api.example.com"

  # Additional project-specific paths
  search_paths:
    - "./local/share"

  # Project-specific timeout
  timeout_seconds: 60
```

### User Config (`.nova/config.local.yaml`)

```yaml
# User-specific placeholder configuration (not committed to git)
example_section:
  # Personal API URL override
  api_url: "https://dev.example.com"

  # Enable debug mode for development
  debug: true
```

---

## Environment Variable Examples

```bash
# Override any config value using NOVA_SECTION_KEY format

# Override API URL from example_section
export NOVA_EXAMPLE_SECTION_API_URL="https://override.example.com"

# Override search paths (colon-separated for lists)
export NOVA_EXAMPLE_SECTION_SEARCH_PATHS="/custom/path:/another/path"

# Override timeout (numeric values)
export NOVA_EXAMPLE_SECTION_TIMEOUT_SECONDS=120

# Override boolean flag
export NOVA_EXAMPLE_SECTION_ENABLED=false
```

---

## Error Handling

### Validation Errors

**Clear error messages for common issues:**

```
❌ Configuration Error in /path/to/.nova/config.yaml

  Field: example_section.timeout_seconds
  Error: Value must be a positive integer
  Got: "30sec"

  Suggestion: Use a number without units, e.g., timeout_seconds: 30
```

### YAML Syntax Errors

```
❌ YAML Syntax Error in /path/to/.nova/config.yaml:5

  mapping values are not allowed here
  in "<unicode string>", line 5, column 15

  Context:
    3: example_section:
    4:   search_paths:
    5:     - /path: value  # <- Error here

  Suggestion: Check indentation and YAML syntax
```

### Missing Config Files

```
ℹ No project configuration found

  Searched from: /current/directory
  Looking for: .nova/config.yaml

  Tip: Run 'nova init' to create a project configuration
```

---

## Testing Strategy

### Unit Tests

**Test each module independently:**

- `test_config_models.py` - Pydantic model validation
- `test_config_paths.py` - Path discovery logic
- `test_config_loader.py` - YAML loading and merging
- `test_config_resolver.py` - Environment variable resolution
- `test_config_main.py` - Main API and caching

### Integration Tests

**Test complete config system:**

- `test_config_integration.py` - End-to-end config loading
- `test_config_precedence.py` - Verify precedence order
- `test_config_env_override.py` - Environment variable overrides
- `test_config_cli.py` - CLI commands with real filesystem

### Test Fixtures

**Minimal test fixtures:**

```python
@pytest.fixture
def temp_config_files(tmp_path):
    """Create temporary config files for testing."""
    global_config = tmp_path / ".config" / "nova" / "config.yaml"
    global_config.parent.mkdir(parents=True)
    global_config.write_text("""
example_section:
  search_paths:
    - /global/path
  timeout_seconds: 30
    """)

    project_config = tmp_path / "project" / ".nova" / "config.yaml"
    project_config.parent.mkdir(parents=True)
    project_config.write_text("""
example_section:
  search_paths:
    - /project/path
  timeout_seconds: 60
    """)

    return {
        "global": global_config,
        "project": project_config,
        "tmp_path": tmp_path
    }
```

---

## Success Criteria

- [ ] All FR requirements from PRD are met
- [ ] Config loads from all 3 scopes with correct precedence
- [ ] Environment variables override config values correctly
- [ ] YAML validation provides clear, actionable error messages
- [ ] CLI commands work intuitively and provide helpful output
- [ ] Code follows ruthless simplicity principles
- [ ] All modules have clear, single responsibilities
- [ ] Comprehensive test coverage (unit + integration)
- [ ] Documentation includes examples and common use cases
- [ ] Zero unnecessary abstractions or future-proofing

---

## Implementation Phases

### Phase 1: Core Config System (Modules: models, paths, loader)
**Estimated Time:** 2-3 hours
**Deliverables:**
- Config models with Pydantic validation
- Path discovery for all 3 scopes
- YAML loading and deep merge logic
- Unit tests for core functionality

### Phase 2: Resolution and Validation (Modules: resolver, main API)
**Estimated Time:** 1-2 hours
**Deliverables:**
- Environment variable override support
- Main Config class with singleton pattern
- Integration tests for complete loading
- Error handling with clear messages

### Phase 3: CLI Commands (Module: cli/commands/config.py)
**Estimated Time:** 1-2 hours
**Deliverables:**
- `nova config show` command
- `nova config paths` command
- `nova config get` command
- `nova config validate` command
- CLI integration tests

### Phase 4: Polish and Documentation
**Estimated Time:** 1 hour
**Deliverables:**
- Example config files with comments
- Usage documentation
- Error message improvements
- Performance verification

---

## Future Considerations (Not in Scope)

These are explicitly **not** included in this specification but could be added later if needed:

- Config file watching and auto-reload
- Config migration system for version changes
- Config export/import commands
- Config encryption for sensitive values
- Config schema documentation generation
- Config diff command to compare scopes
- Interactive config setup wizard

Keep the initial implementation simple. Add these only if real user needs emerge.

---

## Dependencies

**Required:**
- pydantic >= 2.12.3 (already in project)
- pyyaml >= 6.0 (needs to be added)
- typer >= 0.19.2 (already in cli group)

**Optional:**
- None

---

## Appendix: Design Rationale

### Why Pydantic for Schema?

1. Already in dependencies - zero additional cost
2. Type-safe - excellent IDE support and auto-completion
3. Automatic validation with clear error messages
4. Supports complex validation rules
5. Integrates well with environment variables
6. Generates JSON schema automatically (future marketplace feature)

### Why YAML for Config Files?

1. Human-friendly - easier to read/write than JSON
2. Supports comments - critical for documentation
3. Widely used in similar tools (docker-compose, kubernetes, etc.)
4. PyYAML is stable and well-maintained

### Why Singleton Pattern?

1. Config rarely changes during runtime
2. Simpler API - just call `get_config()`
3. Avoids passing config everywhere
4. Still testable with `reload=True` flag
5. Can refactor to dependency injection later if needed

### Why No Config Watching?

1. Adds significant complexity
2. Requires background threads or async
3. Config changes are rare during execution
4. Simple restart is acceptable for MVP
5. Can add later if users request it

### Why No Version Field?

**Decision:** Use additive schema evolution without explicit version field

**Rationale:**

1. **Industry Standard Practice**
   - npm (package.json), Cargo (Cargo.toml), Python (pyproject.toml) don't use config versions
   - Additive-only changes are the proven pattern
   - Docker Compose is actively removing their version field

2. **YAGNI Principle**
   - Currently at placeholder stage - don't know final schema yet
   - Adding version now is premature
   - Can add later if breaking changes become necessary

3. **Tool Version Drives Behavior**
   - Nova 0.1: Accepts any YAML, stores as-is
   - Nova 0.2: Understands `bundles` section (optional field)
   - Nova 0.3: Understands `context` section (optional field)
   - Old configs work with new Nova versions (backward compatible)

4. **Additive Evolution Path**
   ```python
   # Nova 0.1
   class NovaConfig(BaseModel):
       pass  # No fields

   # Nova 0.2
   class NovaConfig(BaseModel):
       bundles: BundlesConfig | None = None  # Optional field added

   # Nova 0.3
   class NovaConfig(BaseModel):
       bundles: BundlesConfig | None = None
       context: ContextConfig | None = None  # Another optional field
   ```

5. **Clear Migration Path If Needed**
   - If breaking changes required: `nova config migrate` command
   - Can detect "old format" configs and update them
   - Major Nova version bump signals breaking config changes
   - Don't need to pre-plan for this

**When Would We Need Version?**

Only if we need to:
- Remove a field (breaking change)
- Change field meaning (breaking change)
- Restructure significantly (breaking change)

**Alternatives if that happens:**
- Deprecate old field, add new one with different name
- Major version bump of Nova itself (0.x → 1.0)
- `nova config migrate` command for one-time updates
- Support both formats temporarily

This specification provides everything needed to implement Feature 1 following the modular design philosophy.
