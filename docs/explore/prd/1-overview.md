# 1. Overview

## Product Summary

Nova is a CLI + library that helps teams set up prompts, context, tools, and agents for any agentic system. Nova Core remains agent-agnostic while adapters add support for specific platforms (Claude Code, Codex, Copilot, etc.). Nova organizes everything through bundles in `.nova/` directories, enabling teams to share context across repos while keeping discoveries local and validating changes through evals.

## Goals

- Enable teams to build consistent agentic systems without rebuilding infrastructure per project
- Provide distributed, shared context that prompts, tools, and agents can reliably access
- Support composition through domains (baseline artifacts) and extensions (specializations)
- Validate changes through evaluation artifacts that travel with bundles
- Maintain agent-agnostic core while supporting platform-specific adapters

## Success Metrics

- Number of repos successfully using Nova
- Time saved vs. manual setup (baseline TBD)
- Bundle reuse rate across projects
- Eval pass rates before/after bundle updates
- Adapter ecosystem growth (number of platforms supported)

## Non-Goals

- Building agent execution engines (we're infrastructure, not runtime)
- Becoming platform-specific (core stays agnostic)

---
