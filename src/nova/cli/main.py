from __future__ import annotations

import os
from typing import Annotated

import typer

from .commands import config as config_commands
from .commands import marketplace as marketplace_commands

app = typer.Typer(help="Nova command-line interface.")
app.add_typer(config_commands.app, name="config")
app.add_typer(marketplace_commands.app, name="marketplace")


@app.callback(invoke_without_command=True)
def _root_callback(
    ctx: typer.Context,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colored output")] = False,
) -> None:
    # Respect NO_COLOR environment variable and --no-color flag
    if no_color or os.getenv("NO_COLOR"):
        ctx.color = False

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def main() -> None:
    """Entrypoint for the nova CLI."""
    app()
