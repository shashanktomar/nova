---
status: "backlog"
priority: "tbd"
updated: "2025-10-18"
review_status: "draft"
---

# Feature 2: Marketplace & Bundle Distribution

**Priority:** P0 (Must Have)
**Status:** Not Started

**Description:**
Marketplace system for discovering, distributing, and managing Nova bundles. Takes inspiration from Claude Code's manifest-based marketplace approach. Supports both public and private (org-internal) marketplaces. Enables bundle authors to publish bundles and users to discover and install them. Includes both Nova Core library support and Nova CLI commands for managing marketplaces.

**Functional Requirements:**

- FR-2.1: Manifest-based catalog for listing available bundles
- FR-2.2: Support multiple marketplaces
- FR-2.3: Nova CLI: Add marketplace source
- FR-2.4: Nova CLI: Remove marketplace source
- FR-2.5: Nova CLI: List configured marketplace sources
- FR-2.6: Bundle discovery via marketplace (search, browse, filter)
- FR-2.7: Install bundles from marketplace by reference
- FR-2.8: Publish bundles to marketplace
- FR-2.9: Bundle versioning and release management
- FR-2.10: Marketplace manifest includes bundle metadata (name, description, version, dependencies, type, etc.)
- FR-2.11: Support git-based bundle distribution (reference bundles via git URLs)
- FR-2.12: Marketplace configuration in Nova config (which marketplaces to use)

**Acceptance Criteria:**

- [ ] Can configure marketplace sources in Nova config
- [ ] Can add marketplace source via CLI
- [ ] Can remove marketplace source via CLI
- [ ] Can list configured marketplace sources via CLI
- [ ] Can discover available bundles from marketplace
- [ ] Can install bundle from marketplace by name/reference
- [ ] Can publish bundle to marketplace
- [ ] Bundle versioning works (can install specific versions)
- [ ] Can use both public and private marketplaces simultaneously
- [ ] Git-based bundle references work (can install from git URL)

**Dependencies:**

- Feature 1: Config Management (marketplace config)

**Open Questions:**

- [ ] Marketplace manifest format and schema?
- [ ] How to handle marketplace authentication (for private/org marketplaces)?
- [ ] Centralized registry vs. decentralized (git-only)?
- [ ] Publishing workflow - automated CI or manual upload?
- [ ] How to handle bundle ownership and permissions?
- [ ] Versioning scheme - strict semver or flexible?

---
