# General Python Guidelines

These are guidelines for LLMs when writing Python code in this codebase.

## Import Conventions

### **CRITICAL: All imports must be at the top of the file**

**Never use inline imports inside functions, methods, or any code blocks.**

```python
# WRONG - Never do this
def some_function():
    from modules.patients.domain.models import Patient  # BAD!
    from datetime import date  # BAD!
    # ... rest of function

# CORRECT - All imports at the top
from datetime import date
from modules.patients.domain.models import Patient

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

**The only acceptable exceptions are:**

- Avoiding circular imports (but should be fixed architecturally)
- Conditional imports for optional dependencies
- Dynamic imports for plugins (very rare)

### Module Imports

When importing from modules, always use the public API exposed through the `__init__.py` file:

```python
# Good - importing from the module's public API
from modules.instrument_registry import Instrument
from modules.core.models import Id, NonEmptyString

# Bad - importing directly from internal files
from modules.instrument_registry.models.instrument import Instrument
from modules.core.models.aliases import Id
```

### Relative Imports Within Modules

When importing from the same module, use relative imports with the `.module` convention:

```python
# Inside src/modules/instrument_registry/services/registry.py
from ..models import Instrument  # Good - relative import from same module
from .utils import validate_symbol  # Good - from sibling file

# Bad - absolute import within same module
from modules.instrument_registry.models import Instrument
```

### Exposing Public APIs

Any new public code in a module must be exposed through the module's `__init__.py` file:

```python
# modules/instrument_registry/models/__init__.py
from .instrument import Instrument, InstrumentType
from .exchange import Exchange

__all__ = ["Instrument", "InstrumentType", "Exchange"]
```

This ensures:

- Clear module boundaries
- Controlled public APIs
- Easier refactoring of internal structure
- Better IDE support and autocomplete

## Modern Python Features

### Type Aliases and Generic Types

Use the modern `type` statement for type aliases and generic types (Python 3.12+):

```python
# Good - using modern type alias syntax
type NonEmptySequence[T] = Annotated[Sequence[T], Field(min_length=1)]

# For complex types, prefer clarity
type InstrumentResult[T] = Result[T, InstrumentNotFoundError]
```

### Union Types

Use the modern union syntax with `|` instead of `Union`:

```python
# Good - modern union syntax
def get_instrument(ticker: str) -> Instrument | None:
    pass

# Bad - old Union syntax
from typing import Union
def get_instrument(ticker: str) -> Union[Instrument, None]:
    pass
```

### Protocol Usage

Use Protocol for structural typing when you need interface-like behavior:

```python
from typing import Protocol

class RepositoryProtocol(Protocol):
    def get_by_id(self, id: str) -> Entity | None:
        ...

    def save(self, entity: Entity) -> None:
        ...
```

## Design Principles

### Simplicity First

Follow the principle: **"Make simple things simple, and complex things possible."**

- Start with the simplest solution that works
- Add complexity only when requirements demand it
- Avoid over-engineering for hypothetical future needs
- Document when and why complexity is necessary
