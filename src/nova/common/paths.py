"""Path discovery utilities for Nova."""

from __future__ import annotations

import os
from pathlib import Path

from .models import AppDirectories


def resolve_working_directory(working_dir: Path | None) -> Path:
    base = working_dir or Path.cwd()
    if base.is_file():
        base = base.parent
    try:
        return base.resolve(strict=False)
    except OSError:
        return base


def get_global_config_root(directories: AppDirectories) -> Path:
    """Get global config root directory.

    Returns ~/.config/{app_name} (or XDG_CONFIG_HOME/{app_name} if set).
    """
    xdg_base = os.getenv("XDG_CONFIG_HOME")
    base_dir = Path(xdg_base).expanduser() if xdg_base else Path.home() / ".config"
    return base_dir / directories.app_name


def get_project_root(start_dir: Path | None, directories: AppDirectories) -> Path | None:
    """Find project root by searching for project marker directory.

    Args:
        start_dir: Directory to start searching from
        directories: Application directory settings

    Returns:
        Path to project root, or None if not found
    """
    if start_dir is None:
        start_dir = Path.cwd()
    if start_dir.is_file():
        start_dir = start_dir.parent

    marker = directories.project_marker
    for path in [start_dir, *start_dir.parents]:
        candidate = path / marker
        if candidate.is_dir():
            return path
    return None


def resolve_project_dir(project_root: Path | None, directories: AppDirectories) -> Path | None:
    """Resolve project configuration directory.

    Args:
        project_root: Root directory of the project
        directories: Application directory settings

    Returns:
        Path to project config directory, or None if it doesn't exist
    """
    if project_root is None:
        return None
    candidate = project_root / directories.project_marker
    return candidate if candidate.is_dir() else None


def get_data_directory_from_dirs(directories: AppDirectories) -> Path:
    """Get XDG data directory using AppDirectories.

    Returns ~/.local/share/{app_name} (or XDG_DATA_HOME/{app_name} if set).
    """
    xdg_data = os.getenv("XDG_DATA_HOME")
    base_dir = Path(xdg_data).expanduser() if xdg_data else Path.home() / ".local" / "share"
    return base_dir / directories.app_name
