from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal

import typer
import yaml

from nova.config import ConfigError, FileConfigStore
from nova.settings import settings
from nova.utils.functools.models import is_err

FormatOption = Annotated[
    Literal["yaml", "json"],
    typer.Option("--format", "-f", show_default=True, case_sensitive=False, help="Output format (yaml or json)."),
]
WorkingDirOption = Annotated[
    Path | None,
    typer.Option(
        "--working-dir",
        hidden=True,
        help="Override working directory used when resolving project config.",
    ),
]

app = typer.Typer(help="Inspect Nova configuration.")


@app.callback(invoke_without_command=True)
def _config_root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command("show")
def show(
    format: FormatOption = "yaml",
    working_dir: WorkingDirOption = None,
) -> None:
    selected_format = format.lower()
    store = FileConfigStore(
        working_dir=working_dir,
        settings=settings.to_config_store_settings(),
    )
    result = store.load().map(lambda r: r.model_dump(mode="json"))
    if is_err(result):
        _handle_error(result.err())
        raise typer.Exit(code=1)

    typer.echo(_format_payload(result.unwrap(), selected_format))


def _format_payload(payload: dict[str, object], format: str) -> str:
    if format == "json":
        return json.dumps(payload, indent=2, sort_keys=True)
    return yaml.safe_dump(payload, sort_keys=True)


def _handle_error(error: ConfigError) -> None:
    message = f"[{error.scope.value}] {error.message}"
    expected_path = getattr(error, "expected_path", None)
    error_path = getattr(error, "path", None)
    if expected_path is not None:
        message = f"{message} (expected at {expected_path})"
    elif error_path is not None:
        message = f"{message} ({error_path})"

    typer.secho(message, err=True, fg=typer.colors.RED)
