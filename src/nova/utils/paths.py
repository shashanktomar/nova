"""Shared path discovery utilities."""

from __future__ import annotations

import os
from pathlib import Path

from nova.settings import settings


def get_global_config_root() -> Path:
    """Return the root directory for global Nova configuration."""
    xdg_base = os.getenv("XDG_CONFIG_HOME")
    base_dir = Path(xdg_base).expanduser() if xdg_base else Path.home() / ".config"
    return base_dir / settings.paths.config_dir_name


def get_project_root(start_dir: Path | None = None) -> Path | None:
    """Find the project root containing the Nova project subdirectory."""
    if start_dir is None:
        start_dir = Path.cwd()
    if start_dir.is_file():
        start_dir = start_dir.parent

    marker = settings.paths.project_subdir_name
    for path in [start_dir, *start_dir.parents]:
        candidate = path / marker
        if candidate.is_dir():
            return path
    return None


def resolve_project_dir(project_root: Path | None) -> Path | None:
    """Return the project configuration directory (.nova) if it exists."""
    if project_root is None:
        return None
    candidate = project_root / settings.paths.project_subdir_name
    return candidate if candidate.is_dir() else None
