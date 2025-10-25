"""Application directory structure settings."""

from __future__ import annotations

from dataclasses import dataclass

from nova.constants import APP_NAME


@dataclass(frozen=True)
class AppDirectories:
    app_name: str = APP_NAME
    project_marker: str = f".{APP_NAME}"
