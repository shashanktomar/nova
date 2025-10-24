---
status: accepted
date: 2025-10-23
decision: XDG Base Directory Structure for Config and Data Separation
context: Feature 2 (Marketplace & Bundle Distribution)
---

# ADR-003: XDG Base Directory Structure for Config and Data Separation

## Status

**Accepted** - 2025-10-23

## Context

Nova needs to store two distinct types of information:

1. **Configuration**: User-facing settings that define behavior (which marketplaces to use, what bundles are enabled, etc.)
2. **Data**: Application state and cached resources (cloned marketplace repositories, metadata, timestamps, etc.)

During Feature 2 implementation, we initially designed marketplace storage to mirror config structure (both global and project having their own data directories). This created several issues:

- Configuration couldn't be easily managed in dotfiles without including large data directories
- Multiple projects would duplicate marketplace clones
- Unclear what should be committed to git vs ignored
- No standard convention for users to understand directory purposes

## Decision

**Nova adopts the XDG Base Directory Specification for organizing configuration and data.**

### Directory Structure

```
~/.config/nova/              (XDG_CONFIG_HOME/nova)
├── config.yaml              User configuration

~/.local/share/nova/         (XDG_DATA_HOME/nova)
├── marketplaces/            Marketplace clones
│   ├── data.json            Marketplace metadata
│   ├── official/
│   │   ├── marketplace.json
│   │   └── bundles/
│   └── company-internal/
│       └── ...

.nova/                       (Project root)
└── config.yaml              Project configuration (no data)
```

### Key Rules

1. **All configuration** goes in `~/.config/nova/` (global) or `.nova/` (project)
   - User-facing settings
   - Committable to git
   - Can be managed in dotfiles

2. **All data** goes in `~/.local/share/nova/` (global only)
   - Cloned marketplace repositories
   - Application state and metadata
   - Never committed to git
   - Local to the machine

3. **No project data directory** - `.nova/data/` does not exist
   - Project config references global data
   - Multiple projects share marketplace clones
   - Project config is purely configuration

## Rationale

### 1. Industry Standard
Popular CLI tools follow XDG Base Directory:
- `kubectl`: Config in `~/.kube/config`, data in `~/.kube/cache/`
- `helm`: Config in `~/.config/helm/`, cache in `~/.cache/helm/`
- `gh` (GitHub CLI): Config in `~/.config/gh/`, data in `~/.local/share/gh/`

Users already understand this pattern.

### 2. Clean Separation of Concerns
- **Configuration** = "what I want"
- **Data** = "cached state to make it work"

This makes it obvious what to commit, backup, or share.

### 3. Dotfile Management
Users can symlink `~/.config/nova/` to their dotfiles repo without including large marketplace clones or local state.

### 4. No Duplication
Marketplace clones are shared globally. If 5 projects use the same marketplace, it's cloned once, not 5 times.

### 5. Clear Git Semantics
- `.nova/config.yaml` → Commit (team shares marketplace configuration)
- `.nova/data/` → Doesn't exist (no confusion about what to ignore)

## Consequences

### Benefits
- Users can manage Nova config in dotfiles cleanly
- Marketplace clones are shared across all projects
- Clear mental model: config vs data
- Follows established CLI conventions
- Project config can be committed without bundling data

### Tradeoffs
- Marketplace clones are global even for project-specific marketplaces
  - **Impact**: Teams sharing project config still need to `nova marketplace add` locally
  - **Mitigation**: This is expected behavior (like `npm install` after cloning a repo)

### Implementation Impact
- Path resolution must check both `~/.config/nova/` and `~/.local/share/nova/`
- XDG environment variables should be respected:
  - `XDG_CONFIG_HOME` (defaults to `~/.config`)
  - `XDG_DATA_HOME` (defaults to `~/.local/share`)
- Windows support may need platform-specific paths (future consideration)

## Examples

### Adding a Marketplace (Global)
```bash
nova marketplace add anthropics/bundles --scope global
```
- Config written to: `~/.config/nova/config.yaml`
- Repo cloned to: `~/.local/share/nova/marketplaces/official/`
- Metadata written to: `~/.local/share/nova/marketplaces/data.json`

### Adding a Marketplace (Project)
```bash
nova marketplace add company/bundles --scope project
```
- Config written to: `.nova/config.yaml` (committable)
- Repo cloned to: `~/.local/share/nova/marketplaces/company-bundles/` (same global data directory)
- Metadata written to: `~/.local/share/nova/marketplaces/data.json`

### Team Workflow
1. Developer A adds marketplace to project: `nova marketplace add acme/bundles --scope project`
2. Developer A commits `.nova/config.yaml` to git
3. Developer B pulls the project
4. Developer B runs `nova marketplace sync` (or first command auto-syncs)
5. Nova clones marketplace to Developer B's `~/.local/share/nova/marketplaces/`

## References

- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
- [Feature 2 Specification](../specs/feature-2-marketplace-bundle-distribution-spec.md)
- [ADR-002: Config Aggregation and Module Independence](./adr-002-config-aggregation-and-module-independence.md)
