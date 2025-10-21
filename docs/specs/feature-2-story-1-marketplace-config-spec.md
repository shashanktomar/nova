# Feature 2, Story 1: Marketplace Configuration Foundation - Implementation Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Updated:** 2025-10-20
**Author:** AI Architecture Team (zen-architect)

## Overview

This specification defines the implementation for marketplace configuration infrastructure (Feature 2, Story 1, P0 priority). It follows the "bricks and studs" modular design philosophy - each module is a self-contained brick with clear contracts (studs) that can be independently generated and regenerated.

This story establishes the foundational configuration for marketplace sources, enabling users to configure which marketplaces Nova should use. It integrates with Feature 1's configuration management system and provides CLI commands for managing marketplace sources.

**Story Scope:**
- Configuration schema for marketplace sources
- Integration with NovaConfig (Feature 1)
- CLI commands for managing marketplace sources
- Validation of marketplace configuration

**Out of Scope:**
- Bundle type definitions (Feature 3, 5)
- Platform-specific configuration (Feature 4)
- Bundle loading/discovery logic (later stories)
- Actual marketplace content/manifests (later stories)

## Architecture Summary

**Approach:** Extend NovaConfig with marketplace configuration section

**Key Decisions:**
- Integrate with existing NovaConfig system (Feature 1)
- Use Pydantic models for marketplace config schema
- Support multiple marketplace sources
- Simple manifest-based approach initially
- Default marketplace can be configured per source
- Validation ensures URL format and unique names

**Configuration Structure:**
```yaml
marketplace:
  sources:
    - name: "official"
      url: "https://marketplace.nova.dev/manifest.json"
      type: "manifest"
      default: true
    - name: "company-internal"
      url: "https://marketplace.company.com/manifest.json"
      type: "manifest"
      default: false
```

## Module Structure

```
src/nova/
├── marketplace/
│   ├── __init__.py          # Public API exports
│   ├── models.py            # Pydantic models for marketplace config
│   └── config.py            # Marketplace config operations
├── config/
│   └── models.py            # Update NovaConfig to include marketplace
└── cli/
    └── commands/
        └── marketplace.py   # CLI marketplace commands
```

---

## Module Specifications

### Module: marketplace.models

**Purpose:** Define marketplace configuration schema using Pydantic models

**Location:** `src/nova/marketplace/models.py`

**Contract:**
- **Inputs:** Dictionary data from YAML files or CLI arguments
- **Outputs:** Validated Pydantic model instances
- **Side Effects:** None (pure data models)
- **Dependencies:** pydantic, typing

**Public Interface:**

```python
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Literal

class MarketplaceSource(BaseModel):
    """Configuration for a single marketplace source.

    A marketplace source represents a catalog of available bundles that
    Nova can discover and install from. Sources are referenced by name
    throughout Nova commands.

    Attributes:
        name: Unique identifier for this marketplace source
        url: HTTP(S) URL to the marketplace manifest file
        type: Type of marketplace (currently only "manifest" supported)
        default: Whether this is the default marketplace for operations

    Example:
        >>> source = MarketplaceSource(
        ...     name="official",
        ...     url="https://marketplace.nova.dev/manifest.json",
        ...     type="manifest",
        ...     default=True
        ... )
    """
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Unique name for this marketplace source"
    )
    url: HttpUrl = Field(
        description="URL to marketplace manifest file"
    )
    type: Literal["manifest"] = Field(
        default="manifest",
        description="Marketplace type (currently only 'manifest' supported)"
    )
    default: bool = Field(
        default=False,
        description="Whether this is the default marketplace"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate marketplace name format.

        Args:
            v: Name to validate

        Returns:
            Validated name

        Raises:
            ValueError: If name contains invalid characters
        """
        # Name must be alphanumeric with hyphens/underscores only
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Marketplace name must contain only letters, numbers, "
                "hyphens, and underscores"
            )
        return v


class MarketplaceConfig(BaseModel):
    """Marketplace configuration section.

    Contains the list of configured marketplace sources. Each source
    represents a catalog of bundles that Nova can discover and install.

    Attributes:
        sources: List of configured marketplace sources

    Validation Rules:
        - Source names must be unique
        - At most one source can be marked as default
        - Empty sources list is valid (no marketplaces configured)

    Example:
        >>> config = MarketplaceConfig(sources=[
        ...     MarketplaceSource(
        ...         name="official",
        ...         url="https://marketplace.nova.dev/manifest.json",
        ...         default=True
        ...     ),
        ...     MarketplaceSource(
        ...         name="company",
        ...         url="https://marketplace.company.com/manifest.json"
        ...     )
        ... ])
    """
    sources: list[MarketplaceSource] = Field(
        default_factory=list,
        description="List of marketplace sources"
    )

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, v: list[MarketplaceSource]) -> list[MarketplaceSource]:
        """Validate marketplace sources list.

        Args:
            v: List of sources to validate

        Returns:
            Validated sources list

        Raises:
            ValueError: If validation fails
        """
        # Check for duplicate names
        names = [source.name for source in v]
        if len(names) != len(set(names)):
            raise ValueError("Marketplace source names must be unique")

        # Check for multiple defaults
        defaults = [source for source in v if source.default]
        if len(defaults) > 1:
            raise ValueError(
                "Only one marketplace source can be marked as default. "
                f"Found {len(defaults)}: {[s.name for s in defaults]}"
            )

        return v

    def get_source(self, name: str) -> MarketplaceSource | None:
        """Get marketplace source by name.

        Args:
            name: Source name to find

        Returns:
            MarketplaceSource if found, None otherwise
        """
        for source in self.sources:
            if source.name == name:
                return source
        return None

    def get_default_source(self) -> MarketplaceSource | None:
        """Get the default marketplace source.

        Returns:
            Default MarketplaceSource if one is marked default, None otherwise
        """
        for source in self.sources:
            if source.default:
                return source
        return None

    def has_source(self, name: str) -> bool:
        """Check if a marketplace source exists.

        Args:
            name: Source name to check

        Returns:
            True if source exists, False otherwise
        """
        return self.get_source(name) is not None
```

**Validation Rules:**
- `name`: Required, 1-100 characters, alphanumeric with hyphens/underscores
- `url`: Must be valid HTTP(S) URL (validated by Pydantic HttpUrl)
- `type`: Currently only "manifest" allowed (extensible for future types)
- `default`: Boolean flag, at most one source can be default
- Source names must be unique across all sources
- Empty sources list is valid

**Testing Requirements:**
- Unit tests for MarketplaceSource validation
- Test valid source creation
- Test invalid name formats (special chars, empty, too long)
- Test invalid URLs
- Test MarketplaceConfig validation
- Test duplicate name detection
- Test multiple default sources detection
- Test get_source(), get_default_source(), has_source() methods
- Test empty sources list

---

### Module: marketplace.config

**Purpose:** Operations for managing marketplace configuration

**Location:** `src/nova/marketplace/config.py`

**Contract:**
- **Inputs:** NovaConfig instance, marketplace source data
- **Outputs:** Updated NovaConfig instance or operation results
- **Side Effects:** None (pure functions, caller handles persistence)
- **Dependencies:** nova.config, nova.marketplace.models

**Public Interface:**

```python
from nova.config import NovaConfig, get_config
from nova.marketplace.models import MarketplaceConfig, MarketplaceSource

def get_marketplace_config(config: NovaConfig | None = None) -> MarketplaceConfig:
    """Get marketplace configuration from NovaConfig.

    Args:
        config: NovaConfig instance (uses get_config() if None)

    Returns:
        MarketplaceConfig instance (empty if not configured)

    Example:
        >>> marketplace = get_marketplace_config()
        >>> print(f"Configured sources: {len(marketplace.sources)}")
    """
    if config is None:
        config = get_config()

    # Get marketplace section from config
    config_dict = config.model_dump()
    marketplace_data = config_dict.get("marketplace", {})

    return MarketplaceConfig(**marketplace_data)


def add_marketplace_source(
    name: str,
    url: str,
    set_default: bool = False,
    marketplace_type: str = "manifest"
) -> MarketplaceSource:
    """Create a new marketplace source configuration.

    Args:
        name: Unique name for the marketplace
        url: URL to marketplace manifest
        set_default: Whether to make this the default marketplace
        marketplace_type: Type of marketplace (default: "manifest")

    Returns:
        Validated MarketplaceSource instance

    Raises:
        ValueError: If validation fails

    Note:
        This function creates the source model but does not persist it.
        Caller is responsible for updating config and saving to file.

    Example:
        >>> source = add_marketplace_source(
        ...     name="official",
        ...     url="https://marketplace.nova.dev/manifest.json",
        ...     set_default=True
        ... )
    """
    return MarketplaceSource(
        name=name,
        url=url,
        type=marketplace_type,
        default=set_default
    )


def validate_marketplace_addition(
    marketplace_config: MarketplaceConfig,
    new_source: MarketplaceSource
) -> None:
    """Validate that a new source can be added to marketplace config.

    Args:
        marketplace_config: Current marketplace configuration
        new_source: New source to add

    Raises:
        ValueError: If source cannot be added (duplicate name, etc.)

    Example:
        >>> marketplace = get_marketplace_config()
        >>> new_source = add_marketplace_source("test", "https://test.com/manifest.json")
        >>> validate_marketplace_addition(marketplace, new_source)
    """
    # Check for duplicate name
    if marketplace_config.has_source(new_source.name):
        raise ValueError(
            f"Marketplace source '{new_source.name}' already exists. "
            f"Use 'nova marketplace remove {new_source.name}' first to replace it."
        )

    # Check for multiple defaults
    if new_source.default and marketplace_config.get_default_source() is not None:
        existing_default = marketplace_config.get_default_source()
        raise ValueError(
            f"Cannot set '{new_source.name}' as default. "
            f"Marketplace '{existing_default.name}' is already the default. "
            f"Remove the default flag or use --force to replace the default."
        )


def list_marketplace_sources(
    marketplace_config: MarketplaceConfig | None = None
) -> list[MarketplaceSource]:
    """List all configured marketplace sources.

    Args:
        marketplace_config: MarketplaceConfig instance (loads from config if None)

    Returns:
        List of MarketplaceSource instances (may be empty)

    Example:
        >>> sources = list_marketplace_sources()
        >>> for source in sources:
        ...     print(f"{source.name}: {source.url}")
    """
    if marketplace_config is None:
        marketplace_config = get_marketplace_config()

    return marketplace_config.sources
```

**Implementation Notes:**
- Functions are pure - they don't modify config files directly
- Caller (CLI commands) handles config persistence
- Validation is explicit and provides helpful error messages
- get_marketplace_config() returns empty config if marketplace not configured
- Supports future marketplace types via extensible "type" field

**Testing Requirements:**
- Test get_marketplace_config() with and without marketplace section
- Test get_marketplace_config() returns empty config when not configured
- Test add_marketplace_source() creates valid source
- Test validate_marketplace_addition() detects duplicate names
- Test validate_marketplace_addition() detects multiple defaults
- Test list_marketplace_sources() returns correct list
- Test list_marketplace_sources() with empty config

---

### Module: config.models (Update)

**Purpose:** Update NovaConfig to include marketplace configuration

**Location:** `src/nova/config/models.py`

**Contract:**
- **Inputs:** Dictionary data from YAML files (including marketplace section)
- **Outputs:** Validated NovaConfig instance with marketplace config
- **Side Effects:** None (pure data model)
- **Dependencies:** pydantic, nova.marketplace.models

**Public Interface Update:**

```python
from pydantic import BaseModel, ConfigDict
from typing import Any

# Import will be added
from nova.marketplace.models import MarketplaceConfig


class NovaConfig(BaseModel):
    """Nova configuration model.

    Root configuration object for Nova. This model uses additive schema evolution.

    Schema Evolution Strategy:
    - Never remove fields (only deprecate)
    - Never change field meaning (add new field instead)
    - Only add optional fields with defaults
    - Tool version determines parsing behavior

    Attributes:
        marketplace: Marketplace configuration (Feature 2, Story 1)

    Future fields will be added as features are implemented:
    - bundles: BundlesConfig | None = None (Feature 3)
    - context: ContextConfig | None = None (Feature 6)
    """
    model_config = ConfigDict(extra="allow")

    # Feature 2, Story 1: Marketplace configuration
    marketplace: MarketplaceConfig | None = None
```

**Migration Notes:**
- This is an additive change - existing configs remain valid
- Empty/missing marketplace section is valid (None default)
- No breaking changes to existing NovaConfig functionality
- Follows schema evolution strategy from Feature 1

**Testing Requirements:**
- Test NovaConfig with marketplace section
- Test NovaConfig without marketplace section (None)
- Test NovaConfig with empty marketplace section
- Test backward compatibility (old configs still work)
- Test model_dump() includes marketplace when present

---

### Module: cli.commands.marketplace

**Purpose:** CLI commands for managing marketplace sources

**Location:** `src/nova/cli/commands/marketplace.py`

**Contract:**
- **Inputs:** Command-line arguments from user
- **Outputs:** Terminal output, updated config files
- **Side Effects:**
  - Reads and writes config files
  - Displays formatted output to terminal
- **Dependencies:** typer, rich, nova.config, nova.marketplace

**Public Interface:**

```python
import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
import yaml

from nova.config import get_config, refresh_config
from nova.config.paths import get_project_config_path, get_global_config_path
from nova.marketplace.config import (
    get_marketplace_config,
    add_marketplace_source,
    validate_marketplace_addition,
    list_marketplace_sources
)
from nova.marketplace.models import MarketplaceConfig

app = typer.Typer(help="Manage marketplace sources")
console = Console()


@app.command("add")
def marketplace_add(
    name: str = typer.Argument(..., help="Unique name for the marketplace"),
    url: str = typer.Argument(..., help="URL to marketplace manifest"),
    default: bool = typer.Option(False, "--default", help="Set as default marketplace"),
    scope: str = typer.Option(
        "project",
        "--scope",
        help="Config scope to update (global|project)"
    ),
) -> None:
    """Add a new marketplace source.

    Adds a marketplace source to Nova configuration. By default, adds to
    project config (.nova/config.yaml). Use --scope global to add to
    global config instead.

    Example:
        nova marketplace add official https://marketplace.nova.dev/manifest.json --default
        nova marketplace add company https://company.com/nova/manifest.json --scope global
    """
    # Validate scope
    if scope not in ["global", "project"]:
        console.print(f"[red]Error: Invalid scope '{scope}'. Must be 'global' or 'project'[/red]")
        raise typer.Exit(1)

    # Get current marketplace config
    marketplace_config = get_marketplace_config()

    try:
        # Create new source
        new_source = add_marketplace_source(
            name=name,
            url=url,
            set_default=default,
            marketplace_type="manifest"
        )

        # Validate addition
        validate_marketplace_addition(marketplace_config, new_source)

        # Determine config file to update
        if scope == "global":
            config_path = get_global_config_path(create_dir=True)
        else:
            config_path = get_project_config_path()
            if config_path is None:
                console.print("[red]Error: Not in a Nova project[/red]")
                console.print("Tip: Run 'nova init' to create a project or use --scope global")
                raise typer.Exit(1)

        # Load existing config file
        if config_path.exists():
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f) or {}
        else:
            config_data = {}

        # Update marketplace section
        if "marketplace" not in config_data:
            config_data["marketplace"] = {"sources": []}

        # Add new source
        config_data["marketplace"]["sources"].append(new_source.model_dump(mode="json"))

        # Write updated config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            yaml.safe_dump(config_data, f, default_flow_style=False, sort_keys=False)

        # Success message
        console.print(f"[green]✓[/green] Added marketplace source '{name}'")
        if default:
            console.print(f"  Set as default marketplace")
        console.print(f"  Config updated: {config_path}")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("remove")
def marketplace_remove(
    name: str = typer.Argument(..., help="Name of marketplace to remove"),
    scope: str = typer.Option(
        "project",
        "--scope",
        help="Config scope to update (global|project)"
    ),
) -> None:
    """Remove a marketplace source.

    Removes a marketplace source from Nova configuration.

    Example:
        nova marketplace remove old-marketplace
        nova marketplace remove company --scope global
    """
    # Validate scope
    if scope not in ["global", "project"]:
        console.print(f"[red]Error: Invalid scope '{scope}'. Must be 'global' or 'project'[/red]")
        raise typer.Exit(1)

    # Determine config file to update
    if scope == "global":
        config_path = get_global_config_path(create_dir=False)
    else:
        config_path = get_project_config_path()
        if config_path is None:
            console.print("[red]Error: Not in a Nova project[/red]")
            raise typer.Exit(1)

    # Check if config file exists
    if not config_path.exists():
        console.print(f"[yellow]Warning: Config file does not exist: {config_path}[/yellow]")
        raise typer.Exit(1)

    # Load config file
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f) or {}

    # Check marketplace section exists
    if "marketplace" not in config_data or "sources" not in config_data["marketplace"]:
        console.print(f"[yellow]Warning: No marketplace sources configured in {scope} config[/yellow]")
        raise typer.Exit(1)

    # Find and remove source
    sources = config_data["marketplace"]["sources"]
    original_count = len(sources)
    config_data["marketplace"]["sources"] = [
        s for s in sources if s.get("name") != name
    ]

    # Check if source was found
    if len(config_data["marketplace"]["sources"]) == original_count:
        console.print(f"[yellow]Warning: Marketplace source '{name}' not found in {scope} config[/yellow]")
        raise typer.Exit(1)

    # Write updated config
    with open(config_path, "w") as f:
        yaml.safe_dump(config_data, f, default_flow_style=False, sort_keys=False)

    # Success message
    console.print(f"[green]✓[/green] Removed marketplace source '{name}'")
    console.print(f"  Config updated: {config_path}")


@app.command("list")
def marketplace_list() -> None:
    """List all configured marketplace sources.

    Shows marketplace sources from all config scopes (global, project, user)
    with their effective configuration after merging.

    Example:
        nova marketplace list
    """
    # Get effective marketplace config
    marketplace_config = get_marketplace_config()
    sources = list_marketplace_sources(marketplace_config)

    if not sources:
        console.print("[yellow]No marketplace sources configured[/yellow]")
        console.print("\nTip: Add a marketplace source:")
        console.print("  nova marketplace add <name> <url>")
        return

    # Create table
    table = Table(title="Configured Marketplace Sources")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("URL", style="blue")
    table.add_column("Type", style="green")
    table.add_column("Default", style="yellow")

    # Add rows
    for source in sources:
        table.add_row(
            source.name,
            str(source.url),
            source.type,
            "✓" if source.default else ""
        )

    console.print(table)
    console.print(f"\nTotal sources: {len(sources)}")
```

**CLI Behavior:**

1. **`nova marketplace add <name> <url> [--default] [--scope]`**
   - Adds marketplace source to config
   - Validates name and URL format
   - Checks for duplicate names
   - Optionally sets as default
   - Updates specified scope (default: project)
   - Creates config file if needed

2. **`nova marketplace remove <name> [--scope]`**
   - Removes marketplace source from config
   - Validates source exists
   - Updates specified scope (default: project)
   - Warns if source not found

3. **`nova marketplace list`**
   - Shows all configured sources (merged from all scopes)
   - Displays in formatted table
   - Shows which source is default
   - Provides helpful tip if no sources configured

**Error Handling:**

```
❌ Error: Marketplace source 'official' already exists.
   Use 'nova marketplace remove official' first to replace it.

❌ Error: Invalid scope 'local'. Must be 'global' or 'project'

❌ Error: Not in a Nova project
   Tip: Run 'nova init' to create a project or use --scope global

❌ Error: Marketplace name must contain only letters, numbers, hyphens, and underscores
   Got: 'my marketplace!'

❌ Error: Cannot set 'company' as default. Marketplace 'official' is already the default.
```

**Testing Requirements:**
- Test add command with valid inputs
- Test add command with invalid name
- Test add command with invalid URL
- Test add command with duplicate name
- Test add command with --default flag
- Test add command with --scope global
- Test add command in non-project directory (should fail for project scope)
- Test remove command with existing source
- Test remove command with non-existent source
- Test remove command with --scope global
- Test list command with sources
- Test list command with no sources
- Test list command shows default marker

---

## Example Configuration Files

### Project Config (`.nova/config.yaml`)

```yaml
marketplace:
  sources:
    - name: "official"
      url: "https://marketplace.nova.dev/manifest.json"
      type: "manifest"
      default: true

    - name: "experimental"
      url: "https://marketplace.nova.dev/experimental/manifest.json"
      type: "manifest"
      default: false
```

### Global Config (`~/.config/nova/config.yaml`)

```yaml
marketplace:
  sources:
    - name: "company-internal"
      url: "https://marketplace.company.com/manifest.json"
      type: "manifest"
      default: false
```

### Empty Marketplace Config (Valid)

```yaml
# No marketplace section - completely valid
# Nova works without marketplace configured
```

### Minimal Marketplace Config

```yaml
marketplace:
  sources: []  # Empty sources list - valid
```

---

## CLI Usage Examples

### Add Official Marketplace

```bash
# Add official Nova marketplace as default
nova marketplace add official https://marketplace.nova.dev/manifest.json --default

# Output:
# ✓ Added marketplace source 'official'
#   Set as default marketplace
#   Config updated: /path/to/project/.nova/config.yaml
```

### Add Company Marketplace to Global Config

```bash
# Add to global config (available to all projects)
nova marketplace add company https://marketplace.company.com/manifest.json --scope global

# Output:
# ✓ Added marketplace source 'company'
#   Config updated: /home/user/.config/nova/config.yaml
```

### List Configured Marketplaces

```bash
nova marketplace list

# Output:
# ┌──────────────┬──────────────────────────────────────────────┬──────────┬─────────┐
# │ Name         │ URL                                          │ Type     │ Default │
# ├──────────────┼──────────────────────────────────────────────┼──────────┼─────────┤
# │ official     │ https://marketplace.nova.dev/manifest.json   │ manifest │ ✓       │
# │ company      │ https://marketplace.company.com/manifest.json│ manifest │         │
# └──────────────┴──────────────────────────────────────────────┴──────────┴─────────┘
#
# Total sources: 2
```

### Remove Marketplace

```bash
nova marketplace remove experimental

# Output:
# ✓ Removed marketplace source 'experimental'
#   Config updated: /path/to/project/.nova/config.yaml
```

---

## Environment Variable Support

Following Feature 1's environment variable convention, marketplace config can be overridden:

```bash
# Override marketplace sources via environment variable
# Note: This is complex, so JSON format is recommended
export NOVA_MARKETPLACE_SOURCES_JSON='[
  {
    "name": "official",
    "url": "https://marketplace.nova.dev/manifest.json",
    "type": "manifest",
    "default": true
  }
]'
```

**Note:** Environment variable overrides for marketplace are possible but not the primary use case. CLI commands are the recommended way to manage marketplace sources.

---

## Testing Strategy

### Unit Tests

**Test each module independently:**

- `test_marketplace_models.py` - Pydantic model validation
  - Test MarketplaceSource validation (valid/invalid names, URLs)
  - Test MarketplaceConfig validation (duplicate names, multiple defaults)
  - Test get_source(), get_default_source(), has_source() methods

- `test_marketplace_config.py` - Config operations
  - Test get_marketplace_config() with and without marketplace section
  - Test add_marketplace_source() creates valid source
  - Test validate_marketplace_addition() validation logic
  - Test list_marketplace_sources()

- `test_config_models_update.py` - NovaConfig with marketplace
  - Test NovaConfig with marketplace section
  - Test NovaConfig without marketplace (backward compatibility)
  - Test model_dump() includes marketplace

### Integration Tests

**Test complete marketplace config system:**

- `test_marketplace_integration.py` - End-to-end config loading
  - Test loading config with marketplace section
  - Test marketplace config merging from multiple scopes
  - Test effective marketplace config after merging

- `test_marketplace_cli.py` - CLI commands with real filesystem
  - Test add command updates config file correctly
  - Test remove command updates config file correctly
  - Test list command displays sources correctly
  - Test scope parameter (global vs project)
  - Test error cases (duplicate names, not in project, etc.)

### Test Fixtures

**Minimal test fixtures:**

```python
@pytest.fixture
def sample_marketplace_config():
    """Sample marketplace configuration for testing."""
    return MarketplaceConfig(sources=[
        MarketplaceSource(
            name="official",
            url="https://marketplace.nova.dev/manifest.json",
            default=True
        ),
        MarketplaceSource(
            name="test",
            url="https://test.example.com/manifest.json"
        )
    ])


@pytest.fixture
def temp_nova_project(tmp_path):
    """Create temporary Nova project structure."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    nova_dir = project_dir / ".nova"
    nova_dir.mkdir()

    config_file = nova_dir / "config.yaml"
    config_file.write_text("marketplace:\n  sources: []\n")

    return {
        "project_dir": project_dir,
        "config_file": config_file
    }
```

---

## Success Criteria

- [ ] MarketplaceConfig and MarketplaceSource models defined and validated
- [ ] NovaConfig updated to include marketplace section (backward compatible)
- [ ] CLI command `nova marketplace add` works correctly
- [ ] CLI command `nova marketplace remove` works correctly
- [ ] CLI command `nova marketplace list` works correctly
- [ ] Marketplace config integrates with Feature 1's config system
- [ ] Config files can contain marketplace section
- [ ] Empty/missing marketplace section is valid
- [ ] Validation prevents duplicate names
- [ ] Validation prevents multiple defaults
- [ ] Error messages are clear and actionable
- [ ] Code follows ruthless simplicity principles
- [ ] All modules have clear, single responsibilities
- [ ] Comprehensive test coverage (unit + integration)
- [ ] CLI output is helpful and well-formatted

---

## Dependencies

**This Story Depends On:**
- Feature 1: Config Management - MUST be complete
  - Uses NovaConfig model
  - Uses config loading system
  - Uses config paths utilities

**This Story Enables:**
- Feature 2, Story 2: Marketplace manifest format
- Feature 2, Story 3: Bundle discovery from marketplace
- Feature 2, Story 4: Bundle installation from marketplace

**Required Packages:**
- pydantic >= 2.12.3 (already in project via Feature 1)
- pyyaml >= 6.0 (already in project via Feature 1)
- typer >= 0.19.2 (already in project via Feature 1)
- rich (for CLI table formatting - should be added)

**New Dependency:**
```bash
cd /path/to/nova
uv add rich
```

---

## Implementation Phases

### Phase 1: Marketplace Models (Module: marketplace.models)
**Estimated Time:** 1 hour
**Deliverables:**
- MarketplaceSource model with validation
- MarketplaceConfig model with validation
- Unit tests for models

### Phase 2: Config Integration (Module: marketplace.config, config.models)
**Estimated Time:** 1 hour
**Deliverables:**
- Update NovaConfig to include marketplace
- Marketplace config operations
- Integration tests

### Phase 3: CLI Commands (Module: cli/commands/marketplace.py)
**Estimated Time:** 1.5 hours
**Deliverables:**
- `nova marketplace add` command
- `nova marketplace remove` command
- `nova marketplace list` command
- CLI integration tests

### Phase 4: Polish and Documentation
**Estimated Time:** 0.5 hours
**Deliverables:**
- Example config files with comments
- Error message improvements
- CLI help text refinement
- Usage examples

**Total Estimated Time:** 4 hours (buffer included beyond original 2-3 hour estimate)

---

## Future Considerations (Not in Scope)

These are explicitly **not** included in this story but may be added in later stories:

- Marketplace manifest format/schema (Story 2)
- Bundle discovery API (Story 3)
- Bundle installation from marketplace (Story 4)
- Marketplace authentication/authorization
- Marketplace health checks/validation
- Marketplace caching
- Multiple marketplace types (git, registry, etc.)
- Marketplace search/filtering
- Bundle publishing workflow

Keep the initial implementation simple. This story focuses purely on marketplace **configuration** infrastructure.

---

## Appendix: Design Rationale

### Why Integrate with NovaConfig?

1. Consistent config management - same system as all other Nova config
2. Inherits precedence order (env > user > project > global)
3. Inherits validation and error handling
4. No need for separate marketplace-specific config system
5. Single source of truth for all Nova configuration

### Why Support Multiple Marketplaces?

1. Users may want to use official + company-internal marketplaces
2. Supports experimentation with different marketplaces
3. Enables private/org-specific bundle catalogs
4. Matches pattern from other package managers (npm, pip, etc.)
5. Simple to implement - just a list of sources

### Why CLI Commands Instead of Manual Config Editing?

1. Better UX - users don't need to understand YAML syntax
2. Validation happens immediately (prevent invalid config)
3. Helpful error messages guide users
4. Easier to document and teach
5. Matches patterns from git, npm, pip, etc.

### Why Allow Empty Marketplace Config?

1. Nova should work without marketplace configured
2. Users may only use local bundles initially
3. Marketplace is an optional enhancement, not a requirement
4. Simplifies onboarding - can add marketplace later
5. Follows "ruthless simplicity" - don't force unnecessary config

### Why "manifest" Type Initially?

1. Simplest marketplace implementation
2. Static file - no server-side logic needed
3. Can be hosted anywhere (GitHub Pages, S3, etc.)
4. Sufficient for MVP
5. Can add other types later (git, registry API, etc.)

This specification provides everything needed to implement Feature 2, Story 1 following the modular design philosophy and ruthless simplicity principles.
