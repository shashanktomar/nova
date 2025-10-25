from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nova.utils.paths import (
    get_global_config_root_from_dirs,
    get_project_root_from_dirs,
    resolve_project_dir_from_dirs,
    resolve_working_directory,
)

from .settings import ConfigStoreSettings


@dataclass(frozen=True, slots=True)
class ResolvedConfigPaths:
    global_path: Path | None
    project_path: Path | None
    user_path: Path | None


def discover_config_paths(working_dir: Path, settings: ConfigStoreSettings) -> ResolvedConfigPaths:
    start_dir = resolve_working_directory(working_dir)

    global_path = _resolve_global_config(settings)
    project_root = get_project_root_from_dirs(start_dir, settings.directories)
    project_path, user_path = _resolve_project_configs(project_root, settings)

    return ResolvedConfigPaths(
        global_path=global_path,
        project_path=project_path,
        user_path=user_path,
    )


def _resolve_global_config(settings: ConfigStoreSettings) -> Path | None:
    candidate = get_global_config_root_from_dirs(settings.directories) / settings.global_file
    return candidate if candidate.is_file() else None


def _resolve_project_configs(
    project_root: Path | None,
    settings: ConfigStoreSettings,
) -> tuple[Path | None, Path | None]:
    if project_root is None:
        return None, None

    project_dir = resolve_project_dir_from_dirs(project_root, settings.directories)
    if project_dir is None:
        return None, None

    project_candidate = project_dir / settings.project_file
    user_candidate = project_dir / settings.user_file

    project_path = project_candidate if project_candidate.is_file() else None
    user_path = user_candidate if user_candidate.is_file() else None

    return project_path, user_path
