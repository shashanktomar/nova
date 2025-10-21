---
status: accepted
date: 2025-10-20
decision: Separation of CLI and Business Logic
context: Feature 1 (Config Management)
---

# ADR-001: Separation of CLI and Business Logic

## Status

**Accepted** - 2025-10-20

## Context

During Feature 1 (Config Management) implementation, business logic was placed directly in CLI command handlers (`nova.cli.commands.config`). This includes:

- YAML file loading and parsing
- Configuration path discovery
- Validation logic and error handling
- Data merging and transformation

This violates separation of concerns and makes the code harder to test, reuse, and maintain.

## Decision

**The CLI layer must not contain business logic. All business logic must reside in core modules.**

### CLI Layer Responsibilities

The CLI layer is responsible **only** for:
- Parsing command-line arguments and options
- Calling business logic functions from core modules
- Formatting output for terminal display (colors, tables, progress bars)
- Handling exit codes and terminal-specific errors
- User-facing help text and examples

### Core Module Responsibilities

Business logic belongs in core modules (e.g., `nova.config`):
- Loading, parsing, and merging configuration files
- Validating configuration against schemas
- Resolving configuration from multiple sources
- Error handling and validation logic
- Data transformation and computation

## Rationale

### 1. Testability
- Business logic can be tested independently without CLI harness
- Fast unit tests without invoking CLI framework
- Easy to mock and inject dependencies

### 2. Reusability
- Business logic can be used by CLI, API, web interface, or library consumers
- Other tools can import and use Nova's core functionality
- Enables programmatic access without CLI overhead

### 3. Maintainability
- Clear separation of concerns
- Business logic changes don't affect CLI presentation
- CLI changes (argument parsing, formatting) don't affect logic
- Easier to understand and reason about each layer

### 4. Flexibility
- Can change CLI framework (e.g., from Typer to Click) without touching business logic
- Can add new interfaces (REST API, gRPC) that share the same logic
- Business logic is framework-agnostic

## Pattern: CLI Command Structure

### ✅ Good Example

```python
# Business logic in core module (nova/config/api.py)
def get_config_by_scope(scope: Literal["effective", "global", "project", "user"]) -> dict[str, Any]:
    """Get configuration for specific scope.

    Raises:
        ConfigNotFoundError: If config doesn't exist for scope
    """
    # All business logic here
    pass

# CLI delegates to business logic (nova/cli/commands/config.py)
@app.command()
def show(scope: str, format: str) -> None:
    """Show configuration values."""
    try:
        # Call business logic
        data = get_config_by_scope(scope)

        # CLI layer: Format and display only
        output = format_output(data, format)
        typer.echo(output)
    except ConfigNotFoundError as e:
        # CLI layer: User-friendly error messages and exit codes
        typer.echo(f"❌ {e.message}", err=True)
        typer.echo(f"Tip: {e.suggestion}", err=True)
        raise typer.Exit(1)
```

### ❌ Bad Example

```python
# Don't do: Business logic in CLI
@app.command()
def show(scope: str) -> None:
    # ❌ YAML loading in CLI
    with open(path) as f:
        data = yaml.safe_load(f)

    # ❌ Validation in CLI
    try:
        NovaConfig.model_validate(data)
    except ValidationError as e:
        # Complex error handling logic in CLI
        ...

    # ❌ Path discovery in CLI
    global_path = discover_config_paths()[0]
```

## Current Violations in Feature 1

The `nova.cli.commands.config` module currently contains:

1. **`show` command** (lines 48-121):
   - Path discovery: `discover_config_paths()`
   - File loading: `load_config_file(path)`
   - Data extraction: `config.model_dump()`
   - Complex conditional logic for scope handling

2. **`validate` command** (lines 123-177):
   - File opening and YAML parsing
   - Validation logic with Pydantic
   - Error formatting and handling

3. **`_validate_single_config` helper** (lines 19-46):
   - Business logic in CLI helper function
   - Should be in core module

## Implications

### Immediate Actions Required

1. **Create `nova.config.api` module** with business logic functions:
   - `get_config_by_scope(scope) -> dict[str, Any]`
   - `validate_config(scope) -> ValidationResult`
   - Define appropriate error types

2. **Refactor CLI commands** to delegate to core module:
   - `show` command calls `get_config_by_scope()`
   - `validate` command calls `validate_config()`
   - CLI only handles formatting and exit codes

3. **Move helper functions** from CLI to core:
   - `_validate_single_config` → `nova.config.validation`

### Future Enforcement

- All new CLI commands must follow this pattern
- Code reviews should verify separation
- Consider adding architecture tests to enforce boundaries
- Update Feature 1 spec to reflect this pattern

### Technical Debt

Track cleanup work:
- [ ] Extract business logic from `show` command
- [ ] Extract business logic from `validate` command
- [ ] Create `nova.config.api` module
- [ ] Update tests to test business logic independently
- [ ] Update CLI tests to verify formatting/exit codes only

## References

- [Python API Design Guidelines](../code-guidelines/python-api-design.md)
- [General Python Guidelines](../code-guidelines/general-python-guidelines.md)
- [Feature 1 Specification](../specs/feature-1-config-management-spec.md)
