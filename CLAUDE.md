# Nova Project Tools

## justfile

- Run `just` to see all available recipes
- Use `just <recipe>` for project tasks instead of manual commands
- Common recipes: `just test`, `just lint`, `just format`, `just check`
- **IMPORTANT**: Always use `just check` to run tests (NOT `uv run pytest`)
- `just check` runs the full test suite with linting and formatting checks

## uv

- Use `uv sync` to install/sync dependencies (not `pip install`)
- Use `uv run <command>` to run scripts in the project environment
- Use `uv tool run <tool>` for one-off tool execution
- Use `uv add <package>` to add dependencies
- Never use `pip` directly in this project

## Code Style

- **CRITICAL**: ALL imports at the top of the file - NEVER use inline imports inside functions
- **IMPORTANT**: Do NOT add docstrings to simple helper functions - only add docstrings to public API functions that need documentation
- Keep code simple and readable - the code should be self-documenting
