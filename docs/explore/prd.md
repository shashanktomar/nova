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

[To be completed]

---

## 4. Technical Considerations

[To be completed]

---

## 5. Release Planning

[To be completed]

---

## 6. Risks & Mitigations

[To be completed]

---

## 7. Open Questions & Decisions

[To be completed]

---

## 8. Appendix

### Related Documents

- Vision Document: docs/vision.md

### Changelog

| Date       | Version | Changes                               | Author    |
| ---------- | ------- | ------------------------------------- | --------- |
| 2025-10-16 | 0.1     | Initial draft - Sections 1-2 complete | John (PM) |
