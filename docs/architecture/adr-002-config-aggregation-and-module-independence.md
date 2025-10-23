---
status: accepted
date: 2025-10-23
updated: 2025-10-23
decision: Config Store Protocol and Module Independence
context: Feature 2 (Marketplace & Bundle Distribution)
---

# ADR-002: Config Store Protocol and Module Independence

## Status

**Accepted** - 2025-10-23
**Updated** - 2025-10-23 (Added ConfigStore protocol)

## Context

While implementing marketplace management we needed to decide how the existing configuration system should interact with feature-specific modules. The `nova.config` package already owns discovery, parsing, and merging for global/project/user configuration scopes. Marketplace functionality introduces new configuration sections (e.g., a list of marketplace sources) and internal state (e.g., clone metadata).

Two competing options emerged:

1. Extend `nova.config` so it parses marketplace configuration directly, handing back typed marketplace entries.
2. Keep `nova.config` unaware of marketplace concerns and let `nova.marketplace` parse raw dictionaries provided by callers.

Option 2 keeps feature modules independent, but it forces each consumer to reimplement merging/validation logic and scatters configuration rules across modules. Option 1 risks coupling feature modules tightly to `nova.config`, but preserves the single source of truth for configuration parsing.

## Decision

**Configuration storage and retrieval is abstracted behind the `ConfigStore` protocol. Feature modules depend on this protocol, not on specific implementations.**

Key principles:

1. **ConfigStore Protocol** - `nova.config` defines a `ConfigStore` protocol with a single method: `load() -> Result[NovaConfig, ConfigError]`
2. **File-based Implementation** - `nova.config.file.FileConfigStore` implements the protocol for YAML file-based configuration
3. **Feature Module Independence** - Feature modules (e.g., `nova.marketplace`) depend on the `ConfigStore` protocol, not on file-based implementation
4. **Consumer Choice** - Consumers (CLI, library users) choose which `ConfigStore` implementation to use

Practical implications:

- `nova.config` exposes both the `ConfigStore` protocol and `FileConfigStore` implementation
- Feature modules accept a `ConfigStore` instance (dependency injection) rather than reading files directly
- `nova.config` may import models from feature packages (e.g., `MarketplaceConfig`) to describe configuration sections
- CLI uses `FileConfigStore` directly for file-based configuration
- Library users can implement their own `ConfigStore` (e.g., database-backed) and pass it to feature modules

## Rationale

1. **Abstraction** – The `ConfigStore` protocol decouples feature modules from file-based implementation. Feature modules work with any configuration source.
2. **Library friendliness** – Library users can implement `ConfigStore` backed by databases, remote services, or in-memory structures without changing feature module code.
3. **Testability** – Tests can provide mock `ConfigStore` implementations without touching the filesystem.
4. **Single responsibility** – File-specific logic (YAML parsing, path discovery) is isolated in `FileConfigStore`. Feature modules don't need to know about files.
5. **Acyclic dependencies** – Feature modules depend on the protocol in `nova.config`, not on implementations. Dependency flows one direction: `nova.marketplace` → `nova.config.ConfigStore` protocol.
6. **Validation reuse** – Feature modules own their configuration schemas (e.g., `MarketplaceConfig`). `nova.config` imports and uses these models.

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
- Feature module APIs accept `ConfigStore` instances: `add_marketplace(source, config_store=...)`
- Tests can create mock stores: `class MockConfigStore: def load(self) -> Result[NovaConfig, ConfigError]: ...`

## Related Documents

- [Feature 2 Specification](../specs/feature-2-marketplace-bundle-distribution-spec.md)
- [ADR-001: Separation of CLI and Business Logic](./adr-001-cli-business-logic-separation.md)
