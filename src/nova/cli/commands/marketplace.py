"""CLI commands for marketplace management."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from nova.config import FileConfigStore
from nova.datastore import FileDataStore
from nova.marketplace import Marketplace, MarketplaceError, MarketplaceScope
from nova.marketplace.models import (
    MarketplaceAddError,
    MarketplaceAlreadyExistsError,
    MarketplaceConfigError,
    MarketplaceFetchError,
    MarketplaceInvalidManifestError,
    MarketplaceNotFoundError,
    MarketplaceSourceParseError,
    MarketplaceStateError,
)
from nova.marketplace.store import MarketplaceStore
from nova.settings import settings
from nova.utils.functools.models import Err, Ok

ScopeOption = Annotated[
    MarketplaceScope,
    typer.Option(
        "--scope",
        "-s",
        help="Configuration scope: global (~/.config/nova) or project (.nova/)",
        case_sensitive=False,
    ),
]

OptionalScopeOption = Annotated[
    MarketplaceScope | None,
    typer.Option(
        "--scope",
        "-s",
        help="Configuration scope: global or project (automatically detects scope if not specified)",
        case_sensitive=False,
    ),
]

WorkingDirOption = Annotated[
    Path | None,
    typer.Option(
        "--working-dir",
        hidden=True,
        help="Override working directory used when resolving project config.",
    ),
]

app = typer.Typer(
    help="Manage Nova marketplace sources.",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback(invoke_without_command=True)
def _marketplace_root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command("add")
def add(
    source: Annotated[str, typer.Argument(help="Marketplace source (owner/repo, git URL, or local path)")],
    scope: ScopeOption = MarketplaceScope.GLOBAL,
    working_dir: WorkingDirOption = None,
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
    config_store = FileConfigStore(
        working_dir=working_dir,
        settings=settings.to_config_store_settings(),
    )

    directories = settings.to_app_directories()
    datastore = FileDataStore(namespace="marketplaces", directories=directories)
    store = MarketplaceStore(datastore)
    marketplace = Marketplace(config_store, store, directories)

    match marketplace.add(source, scope=scope, working_dir=working_dir):
        case Ok(info):
            bundle_text = "bundle" if info.bundle_count == 1 else "bundles"
            typer.secho(
                f"✓ Added '{info.name}' with {info.bundle_count} {bundle_text} ({scope.value})", fg=typer.colors.GREEN
            )
        case Err(error):
            _handle_error(error)
            raise typer.Exit(code=1)


@app.command("remove")
def remove(
    name_or_source: Annotated[str, typer.Argument(help="Marketplace name or source to remove")],
    scope: OptionalScopeOption = None,
    working_dir: WorkingDirOption = None,
) -> None:
    """Remove a marketplace by name or source.

    Examples:

        # Remove by name (auto-detects scope)
        nova marketplace remove official-bundles

        # Remove from specific scope
        nova marketplace remove official-bundles --scope global

        # Remove by source
        nova marketplace remove anthropics/nova-bundles
    """
    config_store = FileConfigStore(
        working_dir=working_dir,
        settings=settings.to_config_store_settings(),
    )

    directories = settings.to_app_directories()
    datastore = FileDataStore(namespace="marketplaces", directories=directories)
    store = MarketplaceStore(datastore)
    marketplace = Marketplace(config_store, store, directories)

    match marketplace.remove(name_or_source, scope=scope, working_dir=working_dir):
        case Ok(name):
            typer.secho(f"✓ Removed '{name}'", fg=typer.colors.GREEN)
        case Err(error):
            _handle_error(error)
            raise typer.Exit(code=1)


@app.command("list")
def list_marketplaces(
    working_dir: WorkingDirOption = None,
) -> None:
    """List all configured marketplaces.

    Examples:

        # List all marketplaces
        nova marketplace list
    """
    config_store = FileConfigStore(
        working_dir=working_dir,
        settings=settings.to_config_store_settings(),
    )

    directories = settings.to_app_directories()
    datastore = FileDataStore(namespace="marketplaces", directories=directories)
    store = MarketplaceStore(datastore)
    marketplace = Marketplace(config_store, store, directories)

    match marketplace.list():
        case Ok(infos):
            if not infos:
                typer.echo("No marketplaces configured.")
                return

            for info in infos:
                bundle_text = "bundle" if info.bundle_count == 1 else "bundles"
                typer.secho(f"• {info.name}", fg=typer.colors.CYAN, bold=True)
                typer.echo(f"  {info.description}")
                typer.echo(f"  {info.bundle_count} {bundle_text} • {info.source}")
        case Err(error):
            _handle_error(error)
            raise typer.Exit(code=1)


@app.command("show")
def show(
    name: Annotated[str, typer.Argument(help="Marketplace name")],
) -> None:
    """Show details for a specific marketplace.

    Examples:

        # Show marketplace details
        nova marketplace show official-bundles
    """
    config_store = FileConfigStore(
        settings=settings.to_config_store_settings(),
    )

    directories = settings.to_app_directories()
    datastore = FileDataStore(namespace="marketplaces", directories=directories)
    store = MarketplaceStore(datastore)
    marketplace = Marketplace(config_store, store, directories)

    match marketplace.get(name):
        case Ok(info):
            bundle_text = "bundle" if info.bundle_count == 1 else "bundles"
            typer.secho(f"{info.name}", fg=typer.colors.CYAN, bold=True)
            typer.echo(f"Description: {info.description}")
            typer.echo(f"Source: {info.source}")
            typer.echo(f"Bundles: {info.bundle_count} {bundle_text}")
        case Err(error):
            _handle_error(error)
            raise typer.Exit(code=1)


def _handle_error(error: MarketplaceError) -> None:
    """Handle marketplace errors with user-friendly messages."""
    match error:
        case MarketplaceNotFoundError(name_or_source=name_or_source):
            typer.secho(f"error: marketplace '{name_or_source}' not found", err=True, fg=typer.colors.RED)
            hint = "hint: use 'nova marketplace list' to see available marketplaces"
            typer.secho(hint, err=True, fg=typer.colors.CYAN)
        case MarketplaceAlreadyExistsError(name=name):
            typer.secho(f"error: marketplace '{name}' already exists", err=True, fg=typer.colors.RED)
            hint = f"hint: use 'nova marketplace remove {name}' to replace it"
            typer.secho(hint, err=True, fg=typer.colors.CYAN)
        case MarketplaceSourceParseError():
            typer.secho("error: invalid marketplace source", err=True, fg=typer.colors.RED)
            typer.secho("hint: valid formats are:", err=True, fg=typer.colors.CYAN)
            typer.secho("  - owner/repo (GitHub)", err=True)
            typer.secho("  - https://github.com/owner/repo.git (Git URL)", err=True)
            typer.secho("  - ./path/to/marketplace (local directory)", err=True)
        case MarketplaceStateError(name=name, message=message):
            typer.secho(f"error: marketplace '{name}' state is corrupted", err=True, fg=typer.colors.RED)
            typer.secho(f"  {message}", err=True, fg=typer.colors.RED)
            typer.secho("hint: this may be a bug, please report it", err=True, fg=typer.colors.CYAN)
        case MarketplaceInvalidManifestError(message=message):
            typer.secho(f"error: {message}", err=True, fg=typer.colors.RED)
            if "not found" in message.lower():
                typer.secho(
                    "hint: ensure marketplace.json exists at the repository root",
                    err=True,
                    fg=typer.colors.CYAN,
                )
        case MarketplaceFetchError(message=message):
            typer.secho("error: failed to fetch marketplace", err=True, fg=typer.colors.RED)
            typer.secho(f"  {message}", err=True)
            typer.secho(
                "hint: verify the source is accessible and contains a valid marketplace",
                err=True,
                fg=typer.colors.CYAN,
            )
        case MarketplaceAddError(message=message):
            typer.secho("error: failed to add marketplace", err=True, fg=typer.colors.RED)
            typer.secho(f"  {message}", err=True)
        case MarketplaceConfigError(scope=scope, message=message):
            typer.secho(f"error: configuration {scope} failed", err=True, fg=typer.colors.RED)
            typer.secho(f"  {message}", err=True)
        case _:  # pragma: no cover - fallback for unexpected subclasses
            typer.secho(f"error: {error.message}", err=True, fg=typer.colors.RED)
