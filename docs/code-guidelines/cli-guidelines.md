# CLI Code Guidelines

## Philosophy

Nova's CLI follows established conventions from best-in-class tools (git, npm, gh) while maintaining consistency with the project's architectural patterns.

### Core Principles

1. **Concise and Scannable**: One-line outputs when possible, essential information only
2. **Helpful and Actionable**: Error messages include hints with exact commands to run
3. **Semantic Colors**: Colors enhance but don't replace information
4. **Separation of Concerns**: CLI layer handles formatting only, business logic in core modules (ADR-001)

## Output Formatting

### Success Messages

**Pattern:**
```
✓ [Action] '[resource]' [with context] ([scope/location])
```

**Examples:**
```bash
✓ Added 'marketplace-name' with 5 bundles (global)
✓ Removed 'marketplace-name' (project)
✓ Updated 'marketplace-name' (global)
```

**Rules:**
- Single line for simple operations
- Show essential info: resource name, count/status, scope
- Omit obvious info (e.g., source URL user just typed)
- Use proper grammar: "1 bundle" vs "5 bundles"
- Green color for success indicator

**Example Implementation:**
```python
bundle_text = "bundle" if count == 1 else "bundles"
typer.secho(f"✓ Added '{name}' with {count} {bundle_text} ({scope.value})", fg=typer.colors.GREEN)
```

### Error Messages

**Pattern: Git-style with error + hint**
```
error: [brief description]
hint: [actionable guidance]
```

**Colors:**
- `error:` → Red
- `hint:` → Cyan
- Additional details → No color (plain text)

**Examples:**
```bash
error: marketplace 'name' already exists
hint: use 'nova marketplace remove name' to replace it

error: invalid marketplace source
hint: valid formats are:
  - owner/repo (GitHub)
  - https://... (Git URL)
  - ./path (local)

error: marketplace.json not found in repository
hint: ensure marketplace.json exists at the repository root
```

**Rules:**
- Always use `error:` prefix (lowercase, like git)
- Provide actionable `hint:` when possible
- Include exact commands in hints
- Multi-line hints use indented bullets
- Keep error messages concise and user-focused

**Example Implementation:**
```python
def _handle_error(error: MarketplaceError) -> None:
    match type(error).__name__:
        case "MarketplaceAlreadyExistsError":
            typer.secho(f"error: marketplace '{error.name}' already exists", err=True, fg=typer.colors.RED)
            typer.secho(f"hint: use 'nova marketplace remove {error.name}' to replace it", err=True, fg=typer.colors.CYAN)
```

### Informational Output

For list/show commands, use structured output:

```bash
$ nova marketplace list
official-bundles    20 bundles    global
company-internal     8 bundles    project
local-dev            3 bundles    global
```

**Rules:**
- Columnar output when listing multiple items
- Include key info: name, count, scope
- Sort alphabetically or by relevance
- No extra decoration unless it aids scanning

## Color Usage

### When to Use Colors

Colors are **semantic only** - they enhance but don't replace information:

- ✅ Green: Success, completion
- ✅ Red: Errors, failures
- ✅ Cyan: Hints, helpful information
- ✅ Yellow: Warnings, cautions
- ❌ Don't use colors for decoration

### Color Accessibility

**Always pair colors with symbols or text:**
- ❌ Bad: Only color indicates success
- ✅ Good: `✓ Added` (symbol + text + color)

### Color Control

Users can disable colors via:
1. `--no-color` flag: `nova --no-color marketplace add ...`
2. `NO_COLOR` environment variable: `NO_COLOR=1 nova ...`
3. Auto-detection: Colors disabled when piped/redirected

**Implementation:**
```python
# In main CLI app callback
@app.callback()
def _root_callback(
    ctx: typer.Context,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colored output")] = False,
) -> None:
    if no_color or os.getenv("NO_COLOR"):
        ctx.color = False
```

## Help System

### Support Both `-h` and `--help`

Configure typer apps to accept both:

```python
app = typer.Typer(
    help="Command description",
    context_settings={"help_option_names": ["-h", "--help"]},
)
```

### Help Text Guidelines

- Keep descriptions concise (one line)
- Include examples in docstring
- Show common use cases first
- Document all options

**Example:**
```python
@app.command("add")
def add(
    source: Annotated[str, typer.Argument(help="Marketplace source (owner/repo, git URL, or local path)")],
    scope: ScopeOption = MarketplaceScope.GLOBAL,
) -> None:
    """Add a marketplace source.

    Examples:

        # Add from GitHub
        nova marketplace add anthropics/nova-bundles --scope global

        # Add from git URL
        nova marketplace add https://git.company.com/bundles.git --scope project

        # Add from local path
        nova marketplace add ./local-marketplace --scope global
    """
```

## Architecture Patterns

### CLI/Business Logic Separation (ADR-001)

**The CLI layer ONLY handles:**
- Parsing arguments
- Formatting output
- Handling errors (presentation)

**Business logic goes in core modules:**
- Input validation
- Business rules
- File I/O
- State management

**Example:**
```python
# ✅ Good: CLI calls business logic, formats output
def add(source: str, scope: MarketplaceScope) -> None:
    marketplace = Marketplace(config_store, datastore)
    result = marketplace.add(source, scope=scope)

    if is_err(result):
        _handle_error(result.unwrap_err())
        raise typer.Exit(code=1)

    info = result.unwrap()
    typer.secho(f"✓ Added '{info.name}' ({scope.value})", fg=typer.colors.GREEN)

# ❌ Bad: Business logic in CLI
def add(source: str, scope: MarketplaceScope) -> None:
    # Parsing, validation, file I/O in CLI layer
    config = yaml.safe_load(open("config.yaml"))
    if source in config["marketplaces"]:
        print("Already exists!")
```

### Error Handling

CLI commands should:
1. Call business logic (returns `Result[T, Error]`)
2. Check for errors with `is_err()`
3. Format and display errors
4. Exit with appropriate code

```python
result = marketplace.add(source, scope=scope)

if is_err(result):
    _handle_error(result.unwrap_err())  # Format and display
    raise typer.Exit(code=1)

# Success path
info = result.unwrap()
```

### Dependency Injection

CLI commands receive dependencies (config stores, datastores) and pass them to business logic:

```python
def add(source: str, scope: MarketplaceScope, working_dir: Path | None = None) -> None:
    working_path = working_dir or Path.cwd()

    # Create dependencies
    config_store = FileConfigStore(
        working_dir=working_path,
        config=settings.to_file_config_paths(),
    )
    datastore = FileDataStore(namespace="marketplaces")

    # Inject into business logic
    marketplace = Marketplace(config_store, datastore)
    result = marketplace.add(source, scope=scope, working_dir=working_path)
```

## Testing

### Use typer.testing.CliRunner

```python
from typer.testing import CliRunner
from nova.cli.main import app

runner = CliRunner()

def test_marketplace_add():
    result = runner.invoke(app, ["marketplace", "add", "source"])
    assert result.exit_code == 0
    assert "Added" in result.stdout
```

### Isolated Filesystem for E2E Tests

```python
def test_marketplace_add_e2e():
    with runner.isolated_filesystem():
        base = Path.cwd()
        env = {
            "XDG_CONFIG_HOME": str(base / "config"),
            "XDG_DATA_HOME": str(base / "data"),
        }

        result = runner.invoke(
            app,
            ["marketplace", "add", "./fixture"],
            env=env
        )

        assert result.exit_code == 0
        # Verify file system state
```

## Common Patterns

### Type Annotations for Options

Use `Annotated` for clear option definitions:

```python
ScopeOption = Annotated[
    MarketplaceScope,
    typer.Option(
        "--scope",
        "-s",
        help="Configuration scope: global (~/.config/nova) or project (.nova/)",
        case_sensitive=False,
    ),
]

def add(scope: ScopeOption = MarketplaceScope.GLOBAL) -> None:
    ...
```

### Hidden Options

Use `hidden=True` for options not meant for general use:

```python
WorkingDirOption = Annotated[
    Path | None,
    typer.Option(
        "--working-dir",
        hidden=True,
        help="Override working directory for testing",
    ),
]
```

### Callback for Help Defaults

Show help when command called without subcommand:

```python
@app.callback(invoke_without_command=True)
def _root_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()
```

## Inspiration and References

Our CLI design draws inspiration from:

- **git**: Error/hint pattern, semantic colors, concise output
- **gh** (GitHub CLI): Clean success messages, actionable errors
- **npm/yarn**: One-line status messages, bundle counts
- **docker**: Status-focused output

When in doubt, follow git's conventions - they're widely understood by developers.
