from __future__ import annotations

import os
from typing import Annotated

import typer

from nova.common import LoggingConfig, create_logger, setup_cli_logging
from nova.config.file import FileConfigStore
from nova.config.models import ConfigScope
from nova.settings import settings

from .commands import config as config_commands
from .commands import marketplace as marketplace_commands

logger = create_logger("cli")

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

def _setup_logging() -> None:
    config_store = FileConfigStore(
        settings=settings.to_config_store_settings(),
    )
    global_config = config_store.load_scope(ConfigScope.GLOBAL).unwrap_or(None)
    logging_config = global_config.logging if global_config else LoggingConfig()

    if logging_config.enabled:
        setup_cli_logging(
            app_info=settings.app,
            config=logging_config,
            paths=settings.to_paths_config(),
        )
        logger.debug("CLI logging initialized", config=logging_config.model_dump())

def main() -> None:
    """Entrypoint for the nova CLI."""
    _setup_logging()
    app()
