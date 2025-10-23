---
status: accepted
date: 2025-10-23
decision: Config Module Owns Aggregation, Feature Modules Remain Config-Agnostic
context: Feature 2 (Marketplace & Bundle Distribution)
---

# ADR-002: Config Aggregation and Module Independence

## Status

**Accepted** - 2025-10-23

## Context

While implementing marketplace management we needed to decide how the existing configuration system should interact with feature-specific modules. The `nova.config` package already owns discovery, parsing, and merging for global/project/user configuration scopes. Marketplace functionality introduces new configuration sections (e.g., a list of marketplace sources) and internal state (e.g., clone metadata).

Two competing options emerged:

1. Extend `nova.config` so it parses marketplace configuration directly, handing back typed marketplace entries.
2. Keep `nova.config` unaware of marketplace concerns and let `nova.marketplace` parse raw dictionaries provided by callers.

Option 2 keeps feature modules independent, but it forces each consumer to reimplement merging/validation logic and scatters configuration rules across modules. Option 1 risks coupling feature modules tightly to `nova.config`, but preserves the single source of truth for configuration parsing.

## Decision

**`nova.config` remains responsible for aggregating and validating configuration across scopes. Feature modules (e.g., `nova.marketplace`) expose typed models that `nova.config` may depend on, but feature modules must not depend on `nova.config`.**

Practical implications:

- `nova.config` may import models and helper types from feature packages to describe configuration sections (e.g., `MarketplaceConfig`).
- Feature modules receive configuration as arguments (typically instances of their own config models) and must not call `parse_config()` or otherwise try to read YAML themselves.
- Consumers that already have a parsed configuration (e.g., applications embedding Nova) can construct the typed feature configs manually and pass them to feature APIs without going through `nova.config`.

## Rationale

1. **Single responsibility** – All configuration discovery and scope merging lives in one place (`nova.config`). Feature modules focus on business logic.
2. **Library friendliness** – Marketplace APIs accept configuration data supplied by callers, so they can be reused in contexts where the caller manages configuration manually.
3. **Acyclic dependencies** – Allowing `nova.marketplace` to call back into `nova.config` would create cyclic imports. By keeping the dependency one-directional (`nova.config` → feature modules), package boundaries remain clear.
4. **Validation reuse** – Feature modules own their configuration schemas. `nova.config` reuses those models instead of duplicating field validation logic.

## Consequences

- When a new feature introduces configuration, its package must publish the relevant config models, and `nova.config` must import and embed them.
- Feature APIs should always accept configuration objects (or the specific data they require) rather than reading files.
- Tests that exercise configuration-sensitive behaviour can construct feature config models directly without invoking the full config loader.

## Related Documents

- [Feature 2 Specification](../specs/feature-2-marketplace-bundle-distribution-spec.md)
- [ADR-001: Separation of CLI and Business Logic](./adr-001-cli-business-logic-separation.md)
