---
status: "backlog"
priority: "p0"
updated: "2025-10-18"
review_status: "draft"
---

# Feature 1: Config Management
**Priority:** P0 (Must Have)
**Status:** Not Started

**Description:**
Complete configuration management system supporting global, project-level, and user-level configuration. Includes both Nova Core library implementation for reading/resolving config and Nova CLI commands for managing config. Handles config precedence, validation, and merging across different scopes.

**Functional Requirements:**
- FR-1.1: Support three config scopes: global (system-wide), project (repo-specific), user (per-developer)
- FR-1.2: Config precedence order: user > project > global
- FR-1.3: Nova Core library API to read and resolve config from all scopes
- FR-1.4: Nova CLI command to list config values
- FR-1.5: Config validation against schema
- FR-1.6: Config file format is YAML
- FR-1.7: Environment variable overrides for config values

**Config File Locations:**
- Global: `~/.config/nova/config.yaml`
- Project: `.nova/config.yaml`
- User: `.nova/config.local.yaml`

**Acceptance Criteria:**
- [ ] Can list config at global, project, and user levels via CLI
- [ ] Config precedence works correctly (user overrides project overrides global)
- [ ] Nova Core can read and resolve config programmatically
- [ ] Invalid config is rejected with clear error messages
- [ ] Can inspect effective config (merged from all scopes)
- [ ] Environment variables can override config values

**Dependencies:**
- None (foundational feature)

**Open Questions:**
- [ ] Schema definition format and validation approach?

---
