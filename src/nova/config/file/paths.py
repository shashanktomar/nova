"""Configuration path discovery utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nova.settings import settings
from nova.utils.paths import get_global_config_root, get_project_root, resolve_project_dir


@dataclass(frozen=True, slots=True)
class ConfigPaths:
    """Container for discovered configuration file paths."""

    global_path: Path | None
    project_path: Path | None
    user_path: Path | None


def discover_config_paths(working_dir: Path | None = None) -> ConfigPaths:
    """Discover all configuration file paths from working directory."""
    start_dir = _normalize_start_dir(working_dir)

    global_path = _resolve_global_config()
    project_root = get_project_root(start_dir)
    project_path, user_path = _resolve_project_configs(project_root)

    return ConfigPaths(
        global_path=global_path,
        project_path=project_path,
        user_path=user_path,
    )


def _normalize_start_dir(working_dir: Path | None) -> Path:
    base = working_dir or Path.cwd()
    if base.is_file():
        base = base.parent
    try:
        return base.resolve(strict=False)
    except OSError:
        return base


def _resolve_global_config() -> Path | None:
    config_filename = settings.paths.global_config_filename
    candidate = get_global_config_root() / config_filename
    return candidate if candidate.is_file() else None


def _resolve_project_configs(project_root: Path | None) -> tuple[Path | None, Path | None]:
    if project_root is None:
        return None, None

    project_dir = resolve_project_dir(project_root)
    if project_dir is None:
        return None, None
    project_candidate = project_dir / settings.paths.project_config_filename
    user_candidate = project_dir / settings.paths.user_config_filename

    project_path = project_candidate if project_candidate.is_file() else None
    user_path = user_candidate if user_candidate.is_file() else None

    return project_path, user_path
