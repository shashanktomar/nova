# Nova Project Tools

## justfile

- Run `just` to see all available recipes
- Use `just <recipe>` for project tasks instead of manual commands
- Common recipes: `just test`, `just lint`, `just format`, `just check`

## uv

- Use `uv sync` to install/sync dependencies (not `pip install`)
- Use `uv run <command>` to run scripts in the project environment
- Use `uv tool run <tool>` for one-off tool execution
- Use `uv add <package>` to add dependencies
- Never use `pip` directly in this project
