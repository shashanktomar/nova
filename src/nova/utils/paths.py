"""Shared path discovery utilities."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathsConfig:
    config_dir_name: str
    project_subdir_name: str


def get_global_config_root(config: PathsConfig) -> Path:
    xdg_base = os.getenv("XDG_CONFIG_HOME")
    base_dir = Path(xdg_base).expanduser() if xdg_base else Path.home() / ".config"
    return base_dir / config.config_dir_name


def get_project_root(start_dir: Path | None, config: PathsConfig) -> Path | None:
    if start_dir is None:
        start_dir = Path.cwd()
    if start_dir.is_file():
        start_dir = start_dir.parent

    marker = config.project_subdir_name
    for path in [start_dir, *start_dir.parents]:
        candidate = path / marker
        if candidate.is_dir():
            return path
    return None


def resolve_project_dir(project_root: Path | None, config: PathsConfig) -> Path | None:
    if project_root is None:
        return None
    candidate = project_root / config.project_subdir_name
    return candidate if candidate.is_dir() else None


def resolve_working_directory(working_dir: Path | None) -> Path:
    base = working_dir or Path.cwd()
    if base.is_file():
        base = base.parent
    try:
        return base.resolve(strict=False)
    except OSError:
        return base
