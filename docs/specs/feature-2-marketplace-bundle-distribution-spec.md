---
status: draft
priority: p0
updated: "2025-10-21"
review_status: "in-progress"
---

# Feature 2: Marketplace & Bundle Distribution - Technical Specification

**Status:** 🚧 Draft (Interactive Design Session)
**Priority:** P0 (Must Have)
**Last Updated:** 2025-10-21

## Overview

This specification defines the technical implementation for Nova's marketplace and bundle distribution system, enabling discovery, installation, and publishing of Nova bundles through manifest-based marketplaces.

### Goals

- Enable marketplace source management (add, remove, list, show)
- Support multiple marketplace sources (public + private/org)
- Support git-based and local marketplace distribution
- Clone and cache marketplace repositories locally
- Use YAML for Nova config files, JSON for marketplace manifests

### Non-Goals

- Bundle discovery/search (next feature)
- Bundle installation/management (next feature)
- Building a centralized registry service (decentralized, manifest-based only)
- Bundle dependency resolution (future feature)
- Bundle publishing workflows (future feature)
- Bundle versioning and version pinning (future feature)

### Design Philosophy

- **Inspired by Claude Code**: Follow Claude's plugin marketplace patterns with Nova naming/structure
- **Manifest-based**: Marketplaces are static JSON files, not services
- **Git-centric**: Bundles distributed via git repos or local paths
- **Minimal and complete**: Simplest API that solves the problem
- **File formats**: YAML for Nova config files (config.yaml), JSON for marketplace/bundle manifests

## Design Decisions (Captured During Interactive Session)

### Decision 1: Marketplace & Bundle Structure
**Date:** 2025-10-21

Following Claude Code's pattern with Nova-specific naming:
- **Marketplace** = JSON file (`marketplace.json`) listing available bundles
- **Bundle** = Directory with `.nova/bundle.json` manifest
- **Nova config files** = YAML (config.yaml) for user-facing configuration
- **Marketplace/Bundle manifests** = JSON for consistency with Claude Code

**Rationale:**
- Proven pattern from Claude Code uses JSON for plugin/marketplace manifests
- YAML reserved for Nova's own config files only
- Clear separation between user config (YAML) and manifest data (JSON)

---

### Decision 2: Marketplace Configuration Scopes
**Date:** 2025-10-21

Marketplace sources configured in **global and project config only** (not user scope):
- Global config (`~/.config/nova/config.yaml`): User-wide marketplaces
- Project config (`.nova/config.yaml`): Project-specific marketplaces
- Lists **merge** across scopes (all marketplaces available)

**Config schema (YAML for Nova config files):**
```yaml
# global config (~/.config/nova/config.yaml)
marketplaces:
  - name: "official"              # From marketplace.json
    source:
      type: github
      repo: nova-team/bundles
  - name: "public-registry"
    source:
      type: url
      url: https://nova-bundles.com/marketplace.json

# project config (.nova/config.yaml)
marketplaces:
  - name: "company-internal"
    source:
      type: git
      url: https://git.acme.com/nova/marketplace
  - name: "local-dev"
    source:
      type: local
      path: ./marketplaces/dev

# Effective: lists merged, all marketplaces available
```

**How marketplace names are determined:**
1. User runs: `nova marketplace add owner/repo`
2. System fetches `marketplace.json` from source
3. Reads `name` field from marketplace.json
4. Stores entry with that name in config list
5. If name conflicts with existing marketplace, error

**Source types:**
- `github`: GitHub repository (owner/repo format)
- `git`: Generic git repository URL
- `local`: Local filesystem path
- `url`: Direct URL to marketplace.json file

**Rationale:**
- Global: Personal marketplace preferences
- Project: Team/org distribution (committed to git)
- User scope excluded: Marketplaces are discoverable resources, not personal overrides

---

### Decision 3: Marketplace Schema
**Date:** 2025-10-21

Minimal marketplace.json schema (JSON format):
```json
{
  "name": "marketplace-name",
  "owner": {
    "name": "Owner Name"
  },
  "bundles": [
    {
      "name": "bundle-name",
      "source": "./bundles/bundle-name",
      "description": "Brief description"
    }
  ]
}
```

**Key points:**
- Version stored in bundle's `.nova/bundle.json`, NOT marketplace listing
- Keep marketplace minimal; additional metadata in bundle manifest
- Can extend with tags/categories later

**Rationale:** Start minimal, add fields as needed; JSON matches Claude Code's marketplace format

---

### Decision 4: Marketplace Source Types
**Date:** 2025-10-21

Support all source types Claude Code supports:
```bash
nova marketplace add owner/repo                      # GitHub shorthand
nova marketplace add https://git.url/repo            # Git URL
nova marketplace add ./local-path                    # Local directory
nova marketplace add https://url/marketplace.json    # Direct JSON URL
```

For git sources, assume `marketplace.json` is at repo root.

**Rationale:** Maximum flexibility for public, private, and development workflows

---

### Decision 5: Marketplace Identification
**Date:** 2025-10-21

Use **source as primary unique identifier**, with name as friendly reference:

**Primary ID:** The source itself (inherently unique)
- `owner/repo`
- `https://git.url/repo`
- `./local-path`
- `https://url/marketplace.json`

**Display name:** The `name` field from marketplace.json (for user convenience)

**Removal semantics:**
```bash
# If name is unique across all configured marketplaces:
nova marketplace remove my-marketplace

# If name conflict exists, use source for precision:
nova marketplace remove owner/repo
nova marketplace remove https://git.url/repo
```

**Rationale:**
- Source is already guaranteed unique (URLs, paths, GitHub repos)
- No need for user-provided aliases or generated IDs
- Name provides convenience for common case (unique names)
- Source provides precision when disambiguation needed
- Store both source and name when adding marketplace

---

### Decision 6: Marketplace Storage Structure
**Date:** 2025-10-21

**Both global and project follow identical structure:**

```
~/.config/nova/                    .nova/
├── config.yaml (YAML)             ├── config.yaml (YAML)
└── marketplaces/                  └── marketplaces/
    ├── data.json                      ├── data.json
    ├── official/                      └── project-marketplace/
    │   ├── marketplace.json               ├── marketplace.json (JSON)
    │   └── bundles/                       └── bundles/
    │       └── coding-python/                 └── custom-bundle/
    │           └── .nova/                         └── .nova/
    │               └── bundle.json                    └── bundle.json (JSON)
    └── company-internal/
```

**Key principles:**
- **Bundles ONLY exist inside marketplaces** - no separate `bundles/` directory
- **Marketplaces are cloned** to `marketplaces/<name>/` directory
- **Marketplace metadata** tracked in `marketplaces/data.json`
- **Bundle "installation"** = adding reference in config, not copying files
- **Same structure** for global (`~/.config/nova/`) and project (`.nova/`)

**Workflow:**
1. `nova marketplace add owner/repo --scope global` → Clone to `~/.config/nova/marketplaces/<name>/`
2. Marketplace metadata stored in `marketplaces/data.json`
3. Marketplace config entry added to config.yaml

**Config vs Data separation:**
- **config.yaml**: User-facing configuration (which marketplaces/bundles to use)
- **marketplaces/data.json**: Internal app state (clone location, last update time, etc.)

**Marketplace metadata file (internal state):**
```json
// marketplaces/data.json
{
  "official": {
    "source": {
      "type": "github",
      "repo": "nova-team/bundles"
    },
    "installLocation": "/Users/user/.config/nova/marketplaces/official",
    "lastUpdated": "2025-10-21T12:00:00Z"
  }
}
```

**Rationale:**
- Bundles stay in marketplace repos (easy updates via git pull)
- No duplication - reference, don't copy
- Consistent global/project structure
- Mirrors Claude Code's proven pattern

---

### Decision 7: File Format Separation
**Date:** 2025-10-21

**Clear separation between Nova config and marketplace/bundle manifests:**

- **Nova config files**: YAML format (`config.yaml`)
  - User-facing configuration
  - Configures which marketplaces and bundles to use
  - Follows Feature 1 config system patterns

- **Marketplace manifests**: JSON format (`marketplace.json`)
  - Defines marketplace metadata and bundle listings
  - Follows Claude Code's marketplace.json format
  - Located at repo root for git sources

- **Bundle manifests**: JSON format (`.nova/bundle.json`)
  - Defines bundle metadata
  - Follows Claude Code's plugin.json format
  - Located in bundle's `.nova/` directory

**Rationale:**
- Consistency with Claude Code (uses JSON for plugin/marketplace manifests)
- Clear separation: YAML for user config, JSON for data/manifests
- JSON is standard for manifest/metadata files in ecosystems
- Easier programmatic parsing of manifests

---

### Decision 8: Marketplace Management Edge Cases

---

### Decision 9: Configuration Ownership and Dependencies
**Date:** 2025-10-21

The existing `nova.config` package remains the single entry point for discovering, parsing, and merging configuration across scopes. Marketplace-specific configuration is modelled in `nova.marketplace` and imported by `nova.config` when building the merged configuration.

**Rules:**

- `nova.marketplace` exposes a `MarketplaceConfig` model that describes a single marketplace entry (`name` + `source`).
- `nova.config` includes `marketplaces: list[MarketplaceConfig] = []` in the global/project/effective config models so the YAML loader produces fully-typed entries after merging scopes.
- Marketplace APIs accept configuration objects (or lists of `MarketplaceConfig`) supplied by callers and **must not** call `parse_config()` internally. This keeps dependencies one-directional and lets other applications embed the marketplace library with their own configuration pipeline.
- Future feature modules that own configuration follow the same pattern: publish config models, let `nova.config` import them, and expect callers to pass typed config objects into their APIs.

**Rationale:**

- Keeps configuration aggregation centralised while allowing feature modules to remain reusable and independent of file I/O.
- Avoids cyclic dependencies between `nova.config` and feature packages.
- Makes tests and library consumers free to construct configuration objects directly.

**Date:** 2025-10-21

**A) Marketplace updates:**
- Deferred to future feature
- No auto-update checking initially
- Manual update workflow to be designed later

**B) Marketplace removal:**
- No bundle installation in this feature, so no dependency checks needed
- Simple removal from config and cleanup of cloned directory

---

## CLI User Experience

This feature provides **marketplace management only**. Bundle discovery and installation will be in follow-up features.

### Marketplace Commands

**Add Marketplace**
```bash
nova marketplace add <source> --scope <global|project>

# Examples:
nova marketplace add anthropics/nova-bundles --scope global
nova marketplace add https://git.company.com/bundles.git --scope project
nova marketplace add ./local-marketplace --scope global
nova marketplace add https://example.com/marketplace.json --scope global
```

**Remove Marketplace**
```bash
nova marketplace remove <name-or-source> [--scope <global|project>]

# Examples:
nova marketplace remove official-nova-bundles
nova marketplace remove anthropics/nova-bundles --scope global
```

**List Marketplaces**
```bash
nova marketplace list
```

**Show Marketplace Details**
```bash
nova marketplace show <name>

# Example:
nova marketplace show official-nova-bundles
```

---

## Public API Contract

The `nova.marketplace` module exports a minimal API for marketplace management.

### Module Exports

```python
# nova/marketplace/__init__.py

__all__ = [
    # Enums
    "MarketplaceSourceType",
    "MarketplaceScope",

    # Error Models
    "MarketplaceError",
    "MarketplaceNotFoundError",
    "MarketplaceAddError",
    "MarketplaceAlreadyExistsError",
    "MarketplaceInvalidManifestError",

    # Data Models
    "GitHubMarketplaceSource",
    "GitMarketplaceSource",
    "LocalMarketplaceSource",
    "URLMarketplaceSource",
    "MarketplaceSource",
    "Contact",
    "BundleEntry",
    "MarketplaceInfo",

    # Public Functions
    "add_marketplace",
    "remove_marketplace",
    "list_marketplaces",
    "get_marketplace",
]
```

### Enums

```python
class MarketplaceSourceType(str, Enum):
    """Marketplace source types."""
    GITHUB = "github"
    GIT = "git"
    LOCAL = "local"
    URL = "url"


class MarketplaceScope(str, Enum):
    """Marketplace configuration scope."""
    GLOBAL = "global"
    PROJECT = "project"
```

### Error Models

All error models are Pydantic BaseModel subclasses for type safety and validation.

```python
class MarketplaceNotFoundError(BaseModel):
    """Marketplace not found."""
    name_or_source: str
    message: str


class MarketplaceAddError(BaseModel):
    """Error adding marketplace (clone, fetch, or validation failed)."""
    source: str
    message: str


class MarketplaceAlreadyExistsError(BaseModel):
    """Marketplace with this name already exists."""
    name: str
    existing_source: str
    message: str


class MarketplaceInvalidManifestError(BaseModel):
    """Invalid or missing marketplace.json."""
    source: str
    message: str


# Union of all marketplace errors
type MarketplaceError = (
    MarketplaceNotFoundError
    | MarketplaceAddError
    | MarketplaceAlreadyExistsError
    | MarketplaceInvalidManifestError
)
```

### Data Models

```python
class GitHubMarketplaceSource(BaseModel):
    """GitHub marketplace source (stored in config.yaml)."""
    type: Literal["github"]
    repo: str  # Format: "owner/repo"


class GitMarketplaceSource(BaseModel):
    """Git repository marketplace source (stored in config.yaml)."""
    type: Literal["git"]
    url: str  # Git URL


class LocalMarketplaceSource(BaseModel):
    """Local filesystem marketplace source (stored in config.yaml)."""
    type: Literal["local"]
    path: str  # Local directory path


class URLMarketplaceSource(BaseModel):
    """Direct URL marketplace source (stored in config.yaml)."""
    type: Literal["url"]
    url: str  # Direct URL to marketplace.json


# Union of all marketplace source types
type MarketplaceSource = (
    GitHubMarketplaceSource
    | GitMarketplaceSource
    | LocalMarketplaceSource
    | URLMarketplaceSource
)


class Contact(BaseModel):
    """Contact information for owner or author."""
    name: str
    email: str | None = None


class BundleEntry(BaseModel):
    """Bundle entry in marketplace manifest."""
    name: str
    description: str
    source: str  # Relative path like "./bundles/bundle-name"
    category: str | None = None
    version: str | None = None
    author: Contact | None = None


class MarketplaceInfo(BaseModel):
    """Marketplace information for listing."""
    name: str
    description: str
    source: MarketplaceSource
    bundle_count: int
```

### Internal Models

These models are used internally and not exported in the public API.

```python
class MarketplaceManifest(BaseModel):
    """Marketplace manifest (from marketplace.json).

    Internal model - not exported from public API.
    """
    name: str
    version: str
    description: str
    owner: Contact
    bundles: list[BundleEntry]


class MarketplaceState(BaseModel):
    """Marketplace state (internal state in data.json).

    Tracks cloned marketplace state for internal use.
    Internal model - not exported from public API.
    """
    name: str
    source: MarketplaceSource
    install_location: Path
    last_updated: str  # ISO datetime string
```

### Public API Functions

```python
def add_marketplace(
    source: str,
    *,
    scope: MarketplaceScope,
    working_dir: Path | None = None
) -> Result[MarketplaceInfo, MarketplaceError]:
    ...


def remove_marketplace(
    name_or_source: str,
    *,
    scope: MarketplaceScope | None = None,
    working_dir: Path | None = None
) -> Result[MarketplaceInfo, MarketplaceError]:
    ...


def list_marketplaces(
    *,
    working_dir: Path | None = None
) -> Result[list[MarketplaceInfo], MarketplaceError]:
    ...


def get_marketplace(
    name: str,
    *,
    working_dir: Path | None = None
) -> Result[MarketplaceInfo, MarketplaceError]:
    ...
```

## Internal Module Structure

[TBD - will design after public API]

## Implementation Checklist

- [ ] Define marketplace.json schema
- [ ] Implement marketplace source configuration in config.yaml
- [ ] Extend `nova.config` models to include `marketplaces: list[MarketplaceConfig]`
- [ ] Implement marketplace data.json management
- [ ] Implement marketplace add command (clone + config update)
- [ ] Implement marketplace remove command (cleanup + config update)
- [ ] Implement marketplace list command
- [ ] Implement marketplace show command
- [ ] Write comprehensive tests
- [ ] Document usage patterns

## References

- [Feature 2 PRD](../explore/prd/3-features-requirements/feature-2-marketplace-bundle-distribution.md)
- [Feature 1 Config Spec](./feature-1-config-management-spec.md)
- Claude Code Plugin System (`.tmp/claude/plugins/`)
