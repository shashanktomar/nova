---
status: accepted
date: 2025-10-23
updated: 2025-10-23
decision: Feature-Specific Config Protocols and Module Independence
context: Feature 2 (Marketplace & Bundle Distribution)
---

# ADR-002: Feature-Specific Config Protocols and Module Independence

## Status

**Accepted** - 2025-10-23
**Updated** - 2025-10-23 (Changed from ConfigStore to feature-specific protocols)

## Context

While implementing marketplace management we needed to decide how the existing configuration system should interact with feature-specific modules. The `nova.config` package already owns discovery, parsing, and merging for global/project/user configuration scopes. Marketplace functionality introduces new configuration sections (e.g., a list of marketplace sources) and internal state (e.g., clone metadata).

Two competing options emerged:

1. Extend `nova.config` so it parses marketplace configuration directly, handing back typed marketplace entries.
2. Keep `nova.config` unaware of marketplace concerns and let `nova.marketplace` parse raw dictionaries provided by callers.

Option 2 keeps feature modules independent, but it forces each consumer to reimplement merging/validation logic and scatters configuration rules across modules. Option 1 risks coupling feature modules tightly to `nova.config`, but preserves the single source of truth for configuration parsing.

## Decision

**Feature modules define their own configuration provider protocols. The config module implements these protocols, avoiding circular dependencies.**

Key principles:

1. **Feature-Specific Protocols** - Each feature module (e.g., `nova.marketplace`) defines a protocol for accessing its configuration (e.g., `MarketplaceConfigProvider`)
2. **Config Implements Protocols** - `nova.config.file.FileConfigStore` implements feature protocols by extracting relevant config sections
3. **Dependency Inversion** - Feature modules depend on their own protocols, not on `nova.config`. Config depends on feature modules to implement their protocols.
4. **Acyclic Dependencies** - Dependency flows: `nova.config` → `nova.marketplace.protocol` (one direction only)

Practical implications:

- Feature modules define protocols in their own package: `nova.marketplace.protocol.MarketplaceConfigProvider`
- Feature module APIs accept protocol instances: `Marketplace(config_provider: MarketplaceConfigProvider)`
- `nova.config.file.FileConfigStore` implements all feature protocols by loading and extracting relevant config sections
- `nova.config` may import models from feature packages (e.g., `MarketplaceConfig`) to describe configuration sections
- CLI uses `FileConfigStore` directly, which implements all necessary feature protocols
- Library users can implement feature protocols independently

## Rationale

1. **No Circular Dependencies** – Feature modules define their own protocols. Config imports from features to implement protocols. Dependency is one-way: config → features.
2. **Library friendliness** – Library users can implement feature protocols (e.g., `MarketplaceConfigProvider`) independently without using `nova.config` at all.
3. **Testability** – Tests can provide mock protocol implementations without touching the filesystem or config system.
4. **Single responsibility** – Features own their configuration contracts. Config owns aggregation and file I/O.
5. **Minimal coupling** – Features only depend on their own protocols, not on config system internals.
6. **Clear contracts** – Each feature protocol explicitly declares what configuration it needs (e.g., `get_marketplace_config() -> list[MarketplaceConfig]`).

## Consequences

### Benefits
- **Flexibility**: Library users can implement custom `ConfigStore` backends (database, remote API, etc.) without modifying Nova's core
- **Testability**: Tests can inject mock `ConfigStore` implementations for isolated testing
- **Clean architecture**: File-based implementation details are isolated in `nova.config.file` submodule
- **Reusability**: Feature modules work in any context where a `ConfigStore` is provided

### Trade-offs
- Feature modules must accept `ConfigStore` as a dependency (dependency injection pattern)
- `nova.config` must import feature config models (e.g., `MarketplaceConfig`), creating a one-way dependency
- New configuration features require updating both the feature module (models) and `nova.config` (aggregation)

### Implementation Notes
- CLI uses `FileConfigStore` directly for default file-based behavior
- Feature modules use class-based APIs with protocol dependencies: `Marketplace(config_provider: MarketplaceConfigProvider)`
- Tests can create mock providers: `class MockMarketplaceConfigProvider: def get_marketplace_config(self) -> list[MarketplaceConfig]: ...`

### Example: Marketplace Module

```python
# nova/marketplace/protocol.py
class MarketplaceConfigProvider(Protocol):
    def get_marketplace_config(self) -> list[MarketplaceConfig]:
        ...

# nova/marketplace/api.py
class Marketplace:
    def __init__(self, config_provider: MarketplaceConfigProvider):
        self._config_provider = config_provider

# nova/config/file/store.py
class FileConfigStore:
    def get_marketplace_config(self) -> list[MarketplaceConfig]:
        config = self.load().unwrap()
        return config.marketplaces
```

## Related Documents

- [Feature 2 Specification](../specs/feature-2-marketplace-bundle-distribution-spec.md)
- [ADR-001: Separation of CLI and Business Logic](./adr-001-cli-business-logic-separation.md)
