---
status: "backlog"
priority: "tbd"
updated: "2025-10-18"
review_status: "draft"
---

# Feature 5: Extension Bundles
**Priority:** P0 (Must Have)
**Status:** Not Started

**Description:**
Extension bundles layer specialization on top of domain bundles (e.g., `coding/python`, `coding/ddd`, `obsidian-knowledge/zettelkasten`). They inherit and extend the baseline artifacts from their parent domain, adding language-specific, methodology-specific, or workflow-specific context, prompts, and tools. Includes both Nova Core library support and Nova CLI commands for managing extensions.

**Functional Requirements:**
- FR-5.1: Bundle type `extension` with clear manifest declaration
- FR-5.2: Extensions must declare domain dependency in manifest
- FR-5.3: Extensions can depend on other extensions
- FR-5.4: Extension bundles include specialized artifacts (prompts, context, tools, evals, docs)
- FR-5.5: Standard extension bundle structure and conventions
- FR-5.6: Nova CLI: List available extensions from marketplace (optionally filtered by domain)
- FR-5.7: Nova CLI: Install extension to repository
- FR-5.8: Nova CLI: Uninstall extension from repository
- FR-5.9: Nova Core: Load and expose extension artifacts via library API
- FR-5.10: Extension artifacts overlay/extend domain artifacts
- FR-5.11: Initial extensions to support: `coding/python`, `coding/typescript`, `coding/ddd`

**Acceptance Criteria:**
- [ ] Can create extension bundle with valid structure
- [ ] Extension bundle validates as type `extension`
- [ ] Extension manifest correctly declares domain dependency
- [ ] Can list available extensions via CLI
- [ ] Can filter extensions by compatible domain
- [ ] Can install extension to repository via CLI
- [ ] Can uninstall extension from repository via CLI
- [ ] Extension installation validates domain dependency exists
- [ ] Extension artifacts are accessible to Nova Core
- [ ] Extension artifacts properly overlay domain artifacts
- [ ] `coding/python` extension bundle exists and works
- [ ] `coding/typescript` extension bundle exists and works
- [ ] `coding/ddd` extension bundle exists and works

**Dependencies:**
- Feature 3: Domain Bundles (extensions depend on domains)
- Feature 2: Marketplace & Bundle Distribution (for discovering/installing extensions)
- Feature 1: Config Management (extension config)

**Open Questions:**
- [ ] Can extensions depend on multiple domains or just one?
- [ ] How do artifact overlays work - merge or replace?
- [ ] Extension dependency chains - how deep can they go?
- [ ] Conflict resolution when multiple extensions modify same artifact?
- [ ] Can extensions be installed without a domain present (error or warn)?

---
