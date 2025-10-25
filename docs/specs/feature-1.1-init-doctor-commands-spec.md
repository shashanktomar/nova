---
status: draft
priority: p1
created: "2025-10-23"
---

# Feature 1.1: Init & Doctor Commands - Technical Specification

**Status:** 🚧 Draft
**Priority:** P1 (Should Have - Needed before Feature 2)
**Created:** 2025-10-23

## Overview

This specification defines the `nova init` and `nova doctor` commands for project initialization and system health checks. These commands ensure Nova's prerequisites are met before users attempt marketplace operations.

### Goals

- Provide `nova init` command to initialize Nova in a project directory
- Provide `nova doctor` command to check system dependencies and health
- Verify git installation (required for marketplace cloning)
- Create `.nova/config.yaml` structure when initializing projects

### Non-Goals

- Installing missing dependencies automatically
- Deep system diagnostics beyond Nova's requirements
- Configuration migration or upgrade tools

## Design Philosophy

- **Fail fast**: Detect missing dependencies early with clear error messages
- **Simple diagnostics**: Check only what Nova actually needs
- **Standard patterns**: Follow conventions from tools like `npm doctor`, `brew doctor`

## Commands

### `nova init`

Initialize Nova in the current directory.

**Behavior:**
1. Check if `.nova/config.yaml` already exists
2. If exists, report "Already initialized" and exit
3. If not, create `.nova/` directory
4. Create `.nova/config.yaml` with empty/default structure
5. Report success with next steps

**Usage:**
```bash
nova init
```

**Output (success):**
```
✓ Initialized Nova project
Created .nova/config.yaml

Next steps:
  - Add a marketplace: nova marketplace add <source>
  - Run health check: nova doctor
```

**Output (already initialized):**
```
✗ Nova project already initialized
Found .nova/config.yaml
```

**Exit codes:**
- 0: Success (initialized)
- 1: Already initialized
- 2: Permission denied / filesystem error

---

### `nova doctor`

Check system health and Nova dependencies.

**Checks:**
1. **Git installed**: Verify `git` command is available
2. **Git version**: Check git version is >= 2.0
3. **Config readable**: Verify config files are valid YAML
4. **Paths accessible**: Check XDG directories are writable

**Usage:**
```bash
nova doctor
```

**Output (all checks pass):**
```
Running Nova health checks...

✓ Git installed (version 2.39.0)
✓ Config files valid
✓ Data directory writable (~/.local/share/nova)

All checks passed! 🎉
```

**Output (git missing):**
```
Running Nova health checks...

✗ Git not installed
  Git is required for cloning marketplace repositories.
  Install: https://git-scm.com/downloads

✓ Config files valid
✓ Data directory writable (~/.local/share/nova)

1 issue found.
```

**Exit codes:**
- 0: All checks passed
- 1: One or more checks failed

## Implementation

### Git Utility Module

Create `src/nova/utils/git.py` for git operations:

```python
from nova.utils.functools.models import Result

def is_git_installed() -> bool:
    """Check if git command is available."""
    ...

def get_git_version() -> Result[str, str]:
    """Get installed git version."""
    ...

def clone_repository(url: str, destination: Path) -> Result[Path, str]:
    """Clone a git repository."""
    ...
```

### CLI Commands

**Location:** `src/nova/cli/commands/init.py`, `src/nova/cli/commands/doctor.py`

Both commands follow ADR-001: CLI layer only handles argument parsing and output formatting. Business logic lives in core modules.

## Dependencies

- **Feature 1 (Config Management)**: Required for config file creation
- **Feature 2 (Marketplace)**: Blocked by this feature (needs git utils)

## Future Enhancements

- Check network connectivity
- Verify GitHub API access
- Check disk space for marketplace clones
- Validate installed bundles

## References

- [ADR-001: CLI and Business Logic Separation](../architecture/adr-001-cli-business-logic-separation.md)
- [Feature 2 Specification](./feature-2-marketplace-bundle-distribution-spec.md)
