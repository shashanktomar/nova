---
status: "backlog"
priority: "tbd"
updated: "2025-10-18"
review_status: "draft"
---

# Feature 3: Domain Bundles
**Priority:** P0 (Must Have)
**Status:** Not Started

**Description:**
Domain bundles establish baseline artifacts for specific problem spaces (e.g., `coding`, `obsidian-knowledge`, `writing`). They provide foundational context, prompts, tools, and conventions that extensions can build upon. Domains are the starting point for repository initialization and define the core capabilities for a particular use case. Includes both Nova Core library support and Nova CLI commands for managing domains.

**Functional Requirements:**
- FR-3.1: Bundle type `domain` with clear manifest declaration
- FR-3.2: Domain bundles include baseline artifacts (prompts, context, tools, evals, docs)
- FR-3.3: Standard domain bundle structure and conventions
- FR-3.4: Nova CLI: List available domains from marketplace
- FR-3.5: Nova CLI: Install domain to repository
- FR-3.6: Nova CLI: Uninstall domain from repository
- FR-3.7: Nova CLI: `nova init` flow includes domain selection and installation
- FR-3.8: Nova Core: Load and expose domain artifacts via library API
- FR-3.9: Domain defines artifact organization conventions for extensions to follow
- FR-3.10: Initial domains to support: `coding` (software development), `obsidian-knowledge` (knowledge management)

**Acceptance Criteria:**
- [ ] Can create domain bundle with valid structure
- [ ] Domain bundle validates as type `domain`
- [ ] Can list available domains via CLI
- [ ] Can install domain to repository via CLI
- [ ] Can uninstall domain from repository via CLI
- [ ] `nova init` allows domain selection and installation
- [ ] Domain artifacts are accessible to Nova Core
- [ ] Extensions can reference domain they build upon
- [ ] `coding` domain bundle exists and works
- [ ] `obsidian-knowledge` domain bundle exists and works

**Dependencies:**
- Feature 2: Marketplace & Bundle Distribution (for discovering/installing domains)
- Feature 1: Config Management (domain config)

**Open Questions:**
- [ ] Can a repo have multiple domains or composition rules?
- [ ] What's the minimum required content for a valid domain?
- [ ] How do we version domains vs. extensions?
- [ ] Domain conflict resolution if multiple installed?

---
