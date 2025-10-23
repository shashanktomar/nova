---
status: backlog
priority: tbd
updated: "2025-10-21"
review_status: "draft"
---

# Feature 3: Bundle Management - Technical Specification

**Status:** 📋 Backlog (Notes from Feature 2 Interactive Session)
**Priority:** TBD
**Last Updated:** 2025-10-21

## Overview

This specification will define bundle discovery, installation, and management. This feature depends on Feature 2 (Marketplace Management).

### Goals (TBD)

- Bundle discovery and search across marketplaces
- Bundle installation (global and project scopes)
- Bundle uninstallation
- List installed bundles
- Bundle updates (future)

### Non-Goals (TBD)

- Bundle versioning and version pinning (deferred)
- Bundle dependency resolution (deferred)
- Bundle publishing workflows (deferred)

---

## Notes from Feature 2 (Marketplace) Interactive Design Session

**Date:** 2025-10-21

During the Feature 2 design session, we discussed bundle management extensively before deciding to split it into a separate feature. The following notes capture those discussions.

### Bundle Installation Model (Decided)

Bundles are **always installed from a configured marketplace** (never directly from git/local):

**CLI mode (scope required):**

```bash
# Install from specific marketplace
nova bundle install coding-python@official --scope global
nova bundle install coding-python@official --scope project

# Search all configured marketplaces (if unique)
nova bundle install coding-python --scope global
```

**Interactive mode:**

```bash
# Browse and select from all marketplace bundles
nova bundle install
# User will be prompted to select scope (global or project)
```

**Scope requirement:**

- **CLI mode:** `--scope` flag is required (global|project)
- **TUI mode:** User prompted to select scope interactively
- **No default:** Avoids confusion about where bundle is installed

**Key points:**

- No direct git URL installation (`nova bundle install https://...` not supported)
- No local path installation (`nova bundle install ./path` not supported)
- Bundles must be listed in a marketplace to be installable
- Simplifies bundle discovery and versioning

**Rationale:**

- Marketplaces provide metadata, versioning, and discoverability
- Forces curation through marketplace listings
- Simplifies implementation (one installation path)
- Users can add local/dev marketplaces for testing

---

### Bundle Storage and References (Decided)

**Key principle: Bundles ONLY exist inside marketplaces**

- No separate `bundles/` directory
- Bundles stay in cloned marketplace repos
- "Installation" = adding reference in config.yaml, NOT copying files

**Config tracks installed bundles:**

```yaml
# config.yaml (global or project)
bundles:
  - name: coding-python
    marketplace: official
  - name: company-standards
    marketplace: company-internal
```

**Directory structure:**

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

**Workflow:**

1. `nova bundle install coding-python@official --scope global`
2. Add entry to `~/.config/nova/config.yaml` under `bundles:` list
3. Bundle referenced from `~/.config/nova/marketplaces/official/bundles/coding-python/`
4. No copying - bundle stays in marketplace directory

**Rationale:**

- Easy updates via marketplace git pull
- No duplication of bundle files
- Clear source of truth (marketplace repo)

---

### Bundle Installation Scope (Decided)

**Installation requires explicit scope:**

```bash
# CLI mode - scope required
nova bundle install coding-python@official --scope global
nova bundle install coding-python@official --scope project

# Interactive mode - user prompted for scope
nova bundle install
```

**Removal allows scope inference:**

```bash
# CLI mode - scope optional
nova bundle uninstall coding-python --scope global  # Explicit
nova bundle uninstall coding-python                 # Infer from config, confirm if in both

# Interactive mode - user picks from categorized list
nova bundle uninstall
# Shows: Global Bundles: [...], Project Bundles: [...]
```

**Rationale:**

- Installation: Explicit scope avoids confusion about where bundle goes
- Removal: Can infer since we know where bundle is referenced
- Confirmation prompt if bundle exists in both scopes

---

### Bundle Name Conflicts (Decided)

If multiple marketplaces have the same bundle name:

**Behavior:**

- `nova bundle install coding-python` → Error if "coding-python" exists in >1 marketplace
- Must use explicit marketplace: `nova bundle install coding-python@official`

**Error message:**

```
✗ Error: Bundle 'coding-python' found in multiple marketplaces:
  - official-nova-bundles
  - community-bundles

Please specify marketplace: nova bundle install coding-python@official --scope global
```

**Rationale:**

- Explicit is better than implicit marketplace selection
- No priority/ordering needed between marketplaces
- Clear user intent required

---

### Marketplace Removal with Installed Bundles (Decided)

What happens when removing a marketplace that has installed bundles:

**Behavior:**

1. Warn user if removing marketplace with installed bundles
2. Ask for confirmation
3. If confirmed: auto-uninstall all bundles from that marketplace

**Example flow:**

```bash
$ nova marketplace remove official-nova-bundles

⚠ Warning: The following bundles from 'official-nova-bundles' are installed:
  - coding-python (global)
  - testing-utils (project)

Remove marketplace and uninstall these bundles? [y/N]: y
✓ Uninstalled 2 bundles
✓ Marketplace 'official-nova-bundles' removed
```

**Rationale:**

- Prevents broken bundle references
- Clear user confirmation required
- Clean state after removal

---

### Bundle Manifest Format (Noted)

**Bundle manifest: `.nova/bundle.json` (JSON format)**

**Key decisions:**

- JSON format (consistent with marketplace.json)
- Located in bundle's `.nova/` directory
- Full schema to be designed during feature 3

---

## References

- [Feature 2: Marketplace Management Spec](./feature-2-marketplace-bundle-distribution-spec.md)
- [Feature 3 PRD](../explore/prd/3-features-requirements/feature-3-domain-bundles.md)
- Claude Code Plugin System (`.tmp/claude/plugins/`)
