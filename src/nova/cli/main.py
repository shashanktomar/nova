from __future__ import annotations

import typer

from .commands import config as config_commands

app = typer.Typer(help="Nova command-line interface.")
app.add_typer(config_commands.app, name="config")


@app.callback(invoke_without_command=True)
def _root_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def main() -> None:
    """Entrypoint for the nova CLI."""
    app()


