---
status: "backlog"
priority: "tbd"
updated: "2025-10-18"
review_status: "draft"
---

# Feature 4: Platform Adapters
**Priority:** P0 (Must Have)
**Status:** Not Started

**Description:**
Platform-specific adapters that integrate Nova with different agentic systems. Nova Core remains agent-agnostic, while adapters translate Nova's bundles, artifacts, and configuration into platform-specific formats and integration points. Each adapter implements the platform's specific conventions for prompts, tools, and context. This feature focuses on building the adapter infrastructure and implementing the Claude Code adapter.

**Functional Requirements:**
- FR-4.1: Adapter interface/contract that platforms must implement
- FR-4.2: Nova Core exposes platform-agnostic artifact API
- FR-4.3: Adapters translate Nova artifacts to platform-specific formats
- FR-4.4: Support for multiple adapters simultaneously (multi-platform repos)
- FR-4.5: Adapter registration and discovery mechanism
- FR-4.6: Platform detection and auto-selection of appropriate adapter
- FR-4.7: Adapter configuration via Nova config
- FR-4.8: Claude Code adapter implementation
- FR-4.9: Adapter can specify required artifact types and formats
- FR-4.10: Error handling when platform-specific features unavailable

**Acceptance Criteria:**
- [ ] Adapter interface is well-defined and documented
- [ ] Nova Core artifact API works independently of adapters
- [ ] Can register and discover available adapters
- [ ] Can configure which adapter to use via config
- [ ] Claude Code adapter exists and works end-to-end
- [ ] Adapters correctly translate artifacts to platform formats
- [ ] Clear error messages when adapter requirements not met
- [ ] Adapter infrastructure supports future adapter implementations

**Dependencies:**
- Feature 1: Config Management (adapter config)

**Open Questions:**
- [ ] How do adapters handle platform-specific artifact types?
- [ ] Versioning strategy for adapters vs. Nova Core?
- [ ] Should future adapters be installable bundles or built-in?
- [ ] How to handle conflicts when multiple adapters want same artifact?

---
