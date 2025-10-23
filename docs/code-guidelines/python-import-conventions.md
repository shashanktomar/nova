# Python Import Conventions

## Critical Rule: Imports at Top of File

**Never use inline imports inside functions, methods, or any code blocks.**

```python
# ❌ WRONG - Never do this
def some_function():
    from nova.config.models import NovaConfig  # BAD!
    from datetime import date  # BAD!
    # ... rest of function

# ✅ CORRECT - All imports at the top
from datetime import date
from nova.config.models import NovaConfig

def some_function():
    # ... function code
```

**Why this is critical:**
- Makes dependencies explicit and visible
- Improves code readability and maintainability
- Prevents import cycles and circular dependency issues
- Enables better IDE support and static analysis
- Follows Python PEP 8 standards
- Makes testing and mocking easier

**The only acceptable exceptions:**
- Avoiding circular imports (but should be fixed architecturally)
- Conditional imports for optional dependencies
- Dynamic imports for plugins (very rare)

## Module Public API

**Always import from a module's public API exposed through `__init__.py`:**

```python
# ✅ Good - importing from module's public API
from nova.config import NovaConfig, parse_config
from nova.marketplace import add_marketplace

# ❌ Bad - importing directly from internal files
from nova.config.models import NovaConfig
from nova.marketplace.api import add_marketplace
```

**Why:**
- Clear module boundaries
- Controlled public APIs
- Easier refactoring of internal structure
- Better IDE support and autocomplete

## Relative Imports Within Modules

**Use relative imports when importing within the same module:**

```python
# Inside src/nova/config/file/loader.py

# ✅ Good - relative imports
from ..models import NovaConfig      # Parent module
from .paths import discover_paths    # Sibling file

# ❌ Bad - absolute imports within same module
from nova.config.models import NovaConfig
from nova.config.file.paths import discover_paths
```

**Pattern:**
- `.` = current directory (sibling files)
- `..` = parent directory
- `...` = grandparent directory (use sparingly)

## Parent and Submodule Conventions

**Submodules import from parents (one direction only):**

```python
# nova/config/file/store.py (submodule)
from ..models import ConfigError        # ✅ Submodule imports from parent
from ..merger import merge_configs      # ✅ OK

# nova/config/__init__.py (parent)
from .file import FileConfigStore       # ✅ Import from submodule's public API

# ❌ WRONG - Don't bypass submodule's __init__.py
from .file.store import FileConfigStore
```

**Rules:**
1. Submodules can freely import from parent modules using `..`
2. Parents should import from submodule's `__init__.py`, not internal files
3. This prevents circular dependencies and maintains clean hierarchy

## Exposing Public APIs

**Every module must expose its public API through `__init__.py`:**

```python
# nova/config/__init__.py
from .protocol import ConfigStore
from .file import FileConfigStore
from .models import NovaConfig

__all__ = [
    "ConfigStore",
    "FileConfigStore",
    "NovaConfig",
    "parse_config",
]

def parse_config() -> NovaConfig:
    """Public API function."""
    ...
```

**Benefits:**
- Single source of truth for module's public interface
- Easy to see what's exported
- Can refactor internals without breaking consumers
- Clear documentation of what's supported

## Cross-Module Import Rules

**External modules must ONLY import from a module's `__init__.py`:**

```python
# ✅ Good - using public API
from nova.config import NovaConfig, parse_config
from nova.marketplace import MarketplaceConfig

# ❌ Bad - importing from internal files
from nova.config.models import NovaConfig
from nova.config.file.loader import load_global_config
from nova.marketplace.config import MarketplaceConfig
```

**Why this matters:**
- Respects module boundaries
- Allows modules to refactor internals freely
- Enforces encapsulation
- Reduces coupling between modules

**Exception:** Imports within the same module are fine:

```python
# Inside nova/config/file/loader.py - OK
from ..models import NovaConfig           # ✅ Within nova.config
from .paths import discover_config_paths  # ✅ Within nova.config.file
```

## Import Order

Organize imports in this order:

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# 1. Standard library
from pathlib import Path
from typing import Protocol

# 2. Third-party
from pydantic import BaseModel
import yaml

# 3. Local application
from nova.config.models import NovaConfig
from nova.utils.functools.models import Result
```

## Summary

**Golden Rules:**
1. All imports at the top of the file
2. Import from module's `__init__.py` (public API)
3. Use relative imports within the same module
4. Submodules import from parents, not the reverse
5. Never bypass a module's `__init__.py` from outside
