---
version: 1.0
updated: 2025-10-16
status: ready
---

# Nova Vision Document

## 1. Vision & Mission

**Vision**: Enable every development team to build consistent, intelligent, and reliable agentic systems through shared context and composable building blocks.

**Mission**: Ship a CLI + library that helps teams set up prompts, context, tools, and agents for any agentic system—maintaining agent-agnostic core principles while supporting diverse platforms through adapters.

---

## 2. Problem Statement

### The Challenge

Teams building agentic systems face several critical challenges:

- **Fragmented Context**: Prompts, tools, and agents lack access to shared, distributed knowledge across repositories
- **Inconsistent Scaffolding**: No reliable framework for organizing and maintaining agentic system components
- **Local Discoveries Lost**: Insights and learnings remain siloed without a path to broader distribution
- **Validation Gaps**: Changes to prompts and agents lack systematic evaluation to ensure improvements

### Why Existing Solutions Fall Short

Current approaches require teams to rebuild infrastructure for each project, leading to:
- Duplicated effort across repositories
- Inconsistent patterns and practices
- No systematic way to share and reuse successful patterns
- Difficulty validating that changes actually improve system behavior

---

## 3. Solution Overview

Nova provides consistent, distributed context so prompts, tools, and agents can tap shared knowledge across repos while keeping discoveries local, maintaining reliable scaffolding, and validating changes through evals.

### What Nova Delivers

- **Nova Core**: Agent-agnostic library that loads `.nova/` assets, resolves bundles, and prepares artifacts for any client system
- **Nova CLI**: Command interface for repo setup, validation, and workflow management
- **Bundle System**: Versioned packages that organize related artifacts and enable composition
- **Adapter Support**: Platform-specific implementations (Claude Code, Codex, Copilot, etc.) built on the agent-agnostic core

### Target Users

- Development teams building AI-assisted development workflows
- Organizations standardizing agentic system patterns across multiple repositories
- Tool builders creating AI-powered development experiences

---

## 4. Core Principles

Nova is built on six foundational pillars:

### **Bundles Everywhere**
`.nova/` organizes Nova through bundles, each delivering a collection of artifacts and declaring its role through a type flag (domain, extension, or future roles we introduce).

### **Domains & Extensions**
Domains (e.g., `coding`, `obsidian-knowledge`) are bundle types that curate baseline artifacts for a problem space. Extensions (e.g., `coding/python`, `coding/ddd`) are bundle types that layer specialization on top of a domain.

### **Strong Conventions**
Directory and naming rules keep artifacts linkable so prompts, tools, and agents can depend on one another safely.

### **Config Driven**
Repos manage `.nova/config` to enable bundles, provide project values, and point Nova Core at relevant inputs.

### **Templated Artifacts**
Prompts and related artifacts support project-specific templating so teams can adapt shared assets.

### **Eval Hooks**
Evaluation artifacts travel with bundles so bundle authors can validate changes before publishing. Nova Core runs eval suites to ensure updates don't regress behavior, providing quality assurance for the ecosystem.

---

## 5. System Architecture

### Nova Core Responsibilities

The agent-agnostic library handles:

- Load `.nova/` configuration
- Resolve bundle manifests and dependency graph
- Apply templates to prompts
- Expose run-ready prompts, tools, and agent metadata through a neutral API

### Nova CLI Responsibilities

The command interface drives Nova Core to:

- Perform repository setup and initialization
- Execute validation workflows
- Manage bundle installation and updates
- Run evaluation suites (primarily for bundle authors to validate before publishing)
- Provide interactive learning mode (inspired by BMAD's kb-mode-interaction)

### Bundle System Architecture

**Bundle Types:**
- **Domain**: Establishes baseline artifacts for a problem space
- **Extension**: Layers specialization on top of a domain
- **Future Types**: Room to grow as we learn

Bundles group related artifacts—individual assets like context snippets, prompt specs, tool adapters, agent briefs, eval outlines, supporting docs, etc.

---

## 6. Key Concepts & Terminology

### Core Concepts

- **Nova Core**: Agent-agnostic library that loads `.nova/` assets, resolves bundles, and prepares artifacts for whatever client invokes it.

- **Nova CLI**: Command interface that drives Nova Core to perform repo setup, validation, and other workflows.

- **Bundle**: Versioned package within `.nova/` that groups related artifacts and declares a `type` describing its role (currently `domain` or `extension`, with room for more types as we learn).

- **Artifact**: Individual asset supplied by a bundle (context snippet, prompt spec, tool adapter, agent brief, eval outline, supporting doc, etc.).

- **Domain**: Bundle type that establishes the baseline artifacts for a problem space (e.g., coding, knowledge management).

- **Extension**: Bundle type that layers on top of a domain to add specialization.

- **Eval Suite**: Named grouping of evaluation artifacts that can be executed together. Primarily used by bundle authors to validate changes before publishing updates.

- **Discovery**: Repo-specific learning we may record and potentially promote into a bundle; format and storage still to be decided.

- **Marketplace**: Concept for sharing bundles across repos, likely inspired by manifest-driven catalogs (design TBD).

---

## 7. Future Directions & Exploration

### Discoveries

Teams can capture local notes and insights about what works or fails in their specific context.

**Status**: Exact format, tooling, and storage remain open questions.

**Potential Directions**:
- Structured annotation system for prompt/agent performance
- Automated capture during eval runs
- Path for promoting discoveries into shared bundles

### Learning Mode

**Inspiration**: BMAD's `kb-mode-interaction` demonstrates the value of interactive knowledge exploration.

**Vision**: Nova CLI should offer a conversational learning mode so users can understand the project holistically without digging through files manually.

**Capabilities**:
- Guided exploration of project's Nova setup
- Interactive documentation browsing
- Context-aware help based on current workflow

### Marketplace

**Inspiration**: Claude's manifest-based plugin marketplaces provide models for bundle distribution.

**Exploration Areas**:
- Referencing bundles from local or shared catalogs
- Version management and dependency resolution
- Publishing and discovery workflows
- Community bundle ecosystem

**Note**: No specific implementation locked in yet—learning from existing patterns.

---

## 8. Open Questions & Decisions

### Distribution & Publishing
- What should the marketplace publishing flow look like?
- Git tags, version field schemes, or other versioning approaches?
- Centralized vs. decentralized catalog models?

### Template Implementation
- Jinja subset vs. custom template syntax?
- What level of template complexity do we need?
- How to balance power with simplicity?

### Discovery Promotion
- How should discoveries be promoted into bundles?
- What review/validation process makes sense?
- Automated vs. manual curation?

### Additional Considerations
- Bundle dependency resolution strategy
- Eval framework design and integration points
- Adapter development patterns and guidelines
