---
status: accepted
date: 2025-10-23
updated: 2025-10-24
decision: Feature-Specific Config Protocols and Settings Injection
context: Configuration management and dependency injection
---

# ADR-002: Feature-Specific Config Protocols and Settings Injection

## Status

**Accepted** - 2025-10-23
**Updated** - 2025-10-24 (Added settings injection pattern)

## Context

Nova requires two types of configuration:

1. **User configuration** - User's preferences (which marketplaces, feature toggles, etc.) stored in config files
2. **App settings** - How the application operates (directory names, file names, paths) from `settings.py`

Feature modules need both:
- Access to user configuration without coupling to `nova.config` implementation
- App settings to know where to store data, what directories to use, etc.

The challenge is providing these dependencies while maintaining:
- Module independence (features don't depend on config system internals)
- No hardcoded values scattered throughout modules
- Testability (ability to inject mock implementations)
- Clear dependency flow (no circular dependencies)

## Decision

**Use protocol-based dependency injection for user config and direct injection for app settings.**

### Part 1: User Configuration via Protocols

Feature modules define protocols for accessing user configuration. Config module implements these protocols.

**Key principles:**
1. **Feature-Specific Protocols** - Each feature defines a protocol (e.g., `MarketplaceConfigProvider`)
2. **Config Implements Protocols** - `FileConfigStore` implements feature protocols
3. **Dependency Inversion** - Features depend on their protocols, not on config implementation
4. **Acyclic Dependencies** - Flow: `nova.config` → `nova.marketplace.protocol`

### Part 2: App Settings via Direct Injection

Feature modules receive app settings as constructor parameters.

**Key principles:**
1. **Settings Objects** - Structured settings classes (e.g., `AppDirectories`, `ConfigStoreSettings`)
2. **Constructor Injection** - Settings passed as required constructor parameters
3. **CLI Responsibility** - CLI layer creates settings from `settings.py` and injects them
4. **No Hardcoding** - Modules never hardcode directory names or paths

### Combined Pattern

Feature modules receive BOTH:
- Protocol for user config (e.g., `config_provider: MarketplaceConfigProvider`)
- Settings for app behavior (e.g., `directories: AppDirectories`)

```python
class Marketplace:
    def __init__(
        self,
        config_provider: MarketplaceConfigProvider,  # User config
        datastore: DataStore,
        directories: AppDirectories,                 # App settings
    ):
        ...
```

CLI layer wires everything:
```python
from nova.settings import settings

directories = settings.to_app_directories()
config_store = FileConfigStore(settings=settings.to_config_store_settings())
datastore = FileDataStore(namespace="marketplaces", directories=directories)
marketplace = Marketplace(config_store, datastore, directories)
```

## Rationale

### For Protocol-Based User Config

1. **No Circular Dependencies** - Features define protocols. Config imports protocols. One-way flow.
2. **Library Friendliness** - Library users can implement custom config providers
3. **Testability** - Tests inject mock protocol implementations
4. **Single Responsibility** - Features own config contracts, config owns file I/O
5. **Clear Contracts** - Protocols explicitly declare config needs

### For Direct Settings Injection

1. **No Hardcoding** - Eliminates scattered hardcoded values like `"nova"`, `".nova"`, `"marketplaces"`
2. **Single Source of Truth** - All app settings flow from `settings.py`
3. **Environment Customization** - Settings can be overridden via environment variables
4. **Testability** - Tests inject custom directories without touching real paths
5. **Explicit Dependencies** - Constructor parameters make dependencies visible
6. **Type Safety** - Structured settings objects with type hints

### Why Not Singletons or Globals?

Hardcoding like `PathsConfig(config_dir_name="nova")` scattered throughout code:
- Violates DRY (duplicated in multiple modules)
- Impossible to customize without code changes
- Hard to test (requires mocking filesystem paths)
- Hides dependencies (unclear what module needs)

Dependency injection makes dependencies explicit and testable.

## Consequences

### Benefits

**For Protocol-Based Config:**
- Library users can implement custom config backends (database, API, etc.)
- Tests inject mock providers for isolated testing
- Feature modules work in any context with a protocol implementation
- Clean separation: config owns files, features own business logic

**For Settings Injection:**
- No hardcoded values scattered throughout codebase
- Single source of truth in `settings.py`
- Easy to customize via environment variables
- Tests inject custom settings without filesystem mocking
- Explicit dependencies visible in constructors

### Trade-offs

**For Protocols:**
- `nova.config` must import feature models (e.g., `MarketplaceConfig`)
- Creates one-way dependency: config → features

**For Settings:**
- Feature modules have more constructor parameters
- CLI layer responsible for wiring (creates settings objects and injects them)
- More verbose initialization (explicit beats implicit)

### Implementation Guidelines

**Feature Module Pattern:**
```python
class FeatureModule:
    def __init__(
        self,
        config_provider: FeatureConfigProvider,  # User config protocol
        dependencies: Dependencies,               # Other dependencies
        directories: AppDirectories,              # App settings
    ):
        self._config_provider = config_provider
        self._directories = directories
```

**CLI Layer Pattern:**
```python
from nova.settings import settings

# Create settings objects
directories = settings.to_app_directories()
store_settings = settings.to_config_store_settings()

# Create config store (implements protocols)
config_store = FileConfigStore(working_dir=Path.cwd(), settings=store_settings)

# Create dependencies
datastore = FileDataStore(namespace="namespace", directories=directories)

# Wire up feature module
feature = FeatureModule(config_store, dependencies, directories)
```

**Test Pattern:**
```python
from nova.utils.directories import AppDirectories

def test_feature():
    # Create test settings
    directories = AppDirectories(app_name="test-app", project_marker=".test")

    # Create mock config provider
    mock_provider = MockConfigProvider()

    # Inject into feature
    feature = FeatureModule(mock_provider, dependencies, directories)
```

### Example: Complete Marketplace Module

```python
# 1. Settings definition
# nova/utils/directories.py
@dataclass(frozen=True)
class AppDirectories:
    app_name: str = "nova"
    project_marker: str = ".nova"

# 2. Feature protocol
# nova/marketplace/protocol.py
class MarketplaceConfigProvider(Protocol):
    def get_marketplace_config(self) -> Result[list[MarketplaceConfig], MarketplaceError]:
        ...

# 3. Feature module with both user config and settings
# nova/marketplace/api.py
class Marketplace:
    def __init__(
        self,
        config_provider: MarketplaceConfigProvider,  # User config
        datastore: DataStore,
        directories: AppDirectories,                 # App settings
    ):
        self._config_provider = config_provider
        self._datastore = datastore
        self._directories = directories

    def add(self, source: str, scope: MarketplaceScope) -> Result[MarketplaceInfo, MarketplaceError]:
        # Uses directories to know where to store data
        data_dir = get_data_directory_from_dirs(self._directories)
        marketplaces_dir = data_dir / "marketplaces"
        ...

# 4. Config store implements protocol
# nova/config/file/store.py
class FileConfigStore(ConfigStore):
    def __init__(self, working_dir: Path, settings: ConfigStoreSettings):
        self.working_dir = working_dir
        self.settings = settings

    def get_marketplace_config(self) -> Result[list[MarketplaceConfig], MarketplaceError]:
        config = self.load().unwrap()
        return Ok(config.marketplaces)

# 5. CLI wires everything
# nova/cli/commands/marketplace.py
from nova.settings import settings

directories = settings.to_app_directories()
config_store = FileConfigStore(
    working_dir=Path.cwd(),
    settings=settings.to_config_store_settings()
)
datastore = FileDataStore(namespace="marketplaces", directories=directories)
marketplace = Marketplace(config_store, datastore, directories)
```

## Settings Structure

Settings use composition to combine directory structure and feature-specific configuration:

```python
# Base directory settings (shared across all modules)
@dataclass(frozen=True)
class AppDirectories:
    app_name: str = "nova"
    project_marker: str = ".nova"

# Config module-specific settings
@dataclass(frozen=True)
class ConfigFileNames:
    global_file: str = "config.yaml"
    project_file: str = "config.yaml"
    user_file: str = "config.local.yaml"

@dataclass(frozen=True)
class ConfigStoreSettings:
    directories: AppDirectories
    filenames: ConfigFileNames

    # Convenience properties expose nested fields
    @property
    def app_name(self) -> str:
        return self.directories.app_name

    @property
    def global_file(self) -> str:
        return self.filenames.global_file
```

This composition pattern:
- Separates directory structure (reusable) from module-specific settings
- Provides convenience properties to reduce nested access
- Keeps settings immutable (frozen dataclasses)
- Makes dependencies explicit

## Related Documents

- [Feature 2 Specification](../specs/feature-2-marketplace-bundle-distribution-spec.md)
- [ADR-001: Separation of CLI and Business Logic](./adr-001-cli-business-logic-separation.md)
- [ADR-003: XDG Directory Structure](./adr-003-xdg-directory-structure.md)
