---
version: 0.1
updated: 2025-10-16
status: in-progress
---

# Nova PRD

## 1. Overview

### Product Summary

Nova is a CLI + library that helps teams set up prompts, context, tools, and agents for any agentic system. Nova Core remains agent-agnostic while adapters add support for specific platforms (Claude Code, Codex, Copilot, etc.). Nova organizes everything through bundles in `.nova/` directories, enabling teams to share context across repos while keeping discoveries local and validating changes through evals.

### Goals

- Enable teams to build consistent agentic systems without rebuilding infrastructure per project
- Provide distributed, shared context that prompts, tools, and agents can reliably access
- Support composition through domains (baseline artifacts) and extensions (specializations)
- Validate changes through evaluation artifacts that travel with bundles
- Maintain agent-agnostic core while supporting platform-specific adapters

### Success Metrics

- Number of repos successfully using Nova
- Time saved vs. manual setup (baseline TBD)
- Bundle reuse rate across projects
- Eval pass rates before/after bundle updates
- Adapter ecosystem growth (number of platforms supported)

### Non-Goals

- Building agent execution engines (we're infrastructure, not runtime)
- Becoming platform-specific (core stays agnostic)

---

## 2. User Personas & Use Cases

### Primary Users

**Persona 1: Platform Builder**

- **Role:** Developer creating agentic tooling/platforms (e.g., building Nova itself or similar tools)
- **Goals:** Build reusable infrastructure for agentic systems
- **Pain points:**
  - Every project rebuilds context management from scratch
  - No standard way to organize prompts, tools, agents
  - Hard to validate improvements systematically
- **How Nova helps:** Provides the scaffolding and conventions to build once, reuse everywhere

**Persona 2: Application Team Lead**

- **Role:** Engineering lead on team using AI-assisted development
- **Goals:** Standardize team's agentic workflows across multiple repos
- **Pain points:**
  - Each repo has different patterns and setups
  - Knowledge doesn't transfer between projects
  - Changes break things unpredictably
- **How Nova helps:** Bundles provide consistent patterns; evals catch regressions before distribution

**Persona 3: Bundle Author / DevOps Lead**

- **Role:** Creates team/org-specific bundles for internal standards
- **Goals:** Package company conventions, approved tools, and context for broad distribution
- **Pain points:**
  - No standard way to distribute internal patterns
  - Teams diverge without central guidance
  - Hard to update practices across multiple repos
- **How Nova helps:** Author custom bundles once, teams install via marketplace; updates propagate cleanly

**Persona 4: Solo Developer / Tool Builder**

- **Role:** Individual building AI-powered development tools
- **Goals:** Leverage existing prompts/tools without reinventing
- **Pain points:**
  - Starting from zero every time
  - No ecosystem to pull from
  - Isolated experimentation, no shared learning
- **How Nova helps:** Install domains/extensions from marketplace; contribute discoveries back

**Persona 5: Non-Technical User / Knowledge Worker**

- **Role:** Content creator, PM, analyst using AI for non-coding workflows
- **Goals:** Use AI agents for domain-specific work (e.g., obsidian-knowledge, content-creation)
- **Pain points:**
  - Technical setup barriers prevent adoption
  - Coding-focused tools don't fit their workflow
  - No clear path to organize their domain context
- **How Nova helps:** Install non-coding domains (obsidian-knowledge, writing, research); same infrastructure, different context

### Use Cases

**UC-1: Setting Up New Repo with Coding Context**

- **Actor:** Application Team Lead
- **Goal:** Get a new repository set up with standard coding prompts and tools
- **Scenario:**
  1. Run `nova init` in new repo
  2. Select `coding` domain
  3. Add `coding/python` extension
  4. Nova creates `.nova/` structure with base prompts and tool configs
  5. Team can immediately use consistent agentic workflows
- **Success criteria:** Repo has working Nova setup in < 5 minutes

**UC-2: Creating & Sharing Custom Org Bundle**

- **Actor:** Bundle Author / DevOps Lead
- **Goal:** Package company-specific standards and distribute to all team repos
- **Scenario:**
  1. Create new bundle with company-specific contexts, prompts, approved tools
  2. Define as `domain` or `extension` based on scope
  3. Use Nova CLI to publish to internal marketplace or git repo
  4. Team members install bundle using Nova CLI
  5. DevOps lead updates bundle and republishes via Nova CLI; teams pull updates via Nova CLI
- **Success criteria:** Custom bundle works across N repos; updates propagate smoothly

**UC-3: Bundle Author Validating Changes Before Publishing**

- **Actor:** Bundle Author / Platform Builder
- **Goal:** Validate bundle updates don't break existing behavior before publishing
- **Scenario:**
  1. Bundle author modifies prompts or artifacts in a bundle
  2. Before publishing, use Nova CLI to execute the bundle's eval suite
  3. Platform validates behavior hasn't regressed
  4. If evals pass, author publishes bundle update using Nova CLI
  5. Users pull updated bundle with confidence in quality
- **Success criteria:** Platform catches regressions before distribution; users get validated updates

**UC-4: Enforcing Mandatory Org-Wide Context Bundle**

- **Actor:** DevOps Lead / Platform Admin
- **Goal:** Push organization-wide shared context as a mandatory bundle to all repos
- **Scenario:**
  1. DevOps lead creates bundle with org-wide context (security policies, coding standards, compliance requirements, etc.)
  2. Marks bundle as mandatory for the organization
  3. Publishes bundle to org marketplace using Nova CLI
  4. All repos in the org automatically pull the mandatory bundle (or are required to on next init/update)
  5. When bundle is updated, changes automatically propagate to all repos via Nova CLI
- **Success criteria:** Mandatory bundle is present in all org repos; updates distribute automatically; non-compliance is detectable

**UC-5: Non-Technical User Setting Up Knowledge Management**

- **Actor:** Non-Technical User (Knowledge Worker)
- **Goal:** Set up AI agent to help manage Obsidian notes and research
- **Scenario:**
  1. Run `nova init` in Obsidian vault
  2. Select `obsidian-knowledge` domain
  3. Nova sets up context, prompts for note organization, linking, research
  4. User can use agent in their vault.
- **Success criteria:** Non-coder successfully uses Nova for domain-specific AI assistance

> **Note:** Additional use cases to be added as we refine requirements.

---

## 3. Features & Requirements

### Feature 1: Config Management
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

### Feature 2: Marketplace & Bundle Distribution
**Priority:** P0 (Must Have)
**Status:** Not Started

**Description:**
Marketplace system for discovering, distributing, and managing Nova bundles. Takes inspiration from Claude Code's manifest-based marketplace approach. Supports both public and private (org-internal) marketplaces. Enables bundle authors to publish bundles and users to discover and install them. Includes both Nova Core library support and Nova CLI commands for managing marketplaces.

**Functional Requirements:**
- FR-2.1: Manifest-based catalog for listing available bundles
- FR-2.2: Support multiple marketplace sources (public, org-internal, custom)
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

### Feature 3: Domain Bundles
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

### Feature 4: Platform Adapters
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

### Feature 5: Extension Bundles
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

### Feature 6: Template Engine
**Priority:** TBD
**Status:** Not Started

**Description:**
Support for project-specific templating in prompts and artifacts. Allows bundles to include template variables that get resolved with project-specific values from Nova config, enabling teams to adapt shared assets to their context.

**Details:** To be decided

---

### Feature 7: Evaluation System
**Priority:** TBD
**Status:** Not Started

**Description:**
Evaluation framework for bundle authors to validate that bundle changes don't regress behavior. Eval artifacts travel with bundles and can be executed via Nova CLI before publishing updates.

**Details:** To be decided

---

### Feature 8: Mandatory Bundle Enforcement
**Priority:** TBD
**Status:** Not Started

**Description:**
Organization-wide policy enforcement system allowing platform admins to mark bundles as mandatory. Ensures all repos in an org have required bundles (security policies, standards, compliance) installed and updated.

**Details:** To be decided

---

### Feature 9: Discovery System
**Priority:** P2 (Future/Exploratory)
**Status:** Not Started

**Description:**
System for capturing repo-specific learnings, insights, and discoveries about what works or fails. Provides path for promoting successful discoveries into shared bundles.

**Details:** To be decided

---

### Feature 10: Learning Mode
**Priority:** P2 (Future/Exploratory)
**Status:** Not Started

**Description:**
Interactive conversational mode (inspired by BMAD's kb-mode-interaction) that helps users explore and understand the project's Nova setup, documentation, and context through guided prompts.

**Details:** To be decided

---

## 4. Technical Considerations

[To be completed]

---

## 5. Risks & Mitigations

[To be completed]

---

## 6. Open Questions & Decisions

[To be completed]

---

## 7. Appendix

### Related Documents

- Vision Document: docs/vision.md

### Changelog

| Date       | Version | Changes                               | Author    |
| ---------- | ------- | ------------------------------------- | --------- |
| 2025-10-16 | 0.1     | Initial draft - Sections 1-2 complete | John (PM) |
