from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nova.utils.paths import (
    PathsConfig,
    get_global_config_root,
    get_project_root,
    resolve_project_dir,
    resolve_working_directory,
)

from .config import FileConfigPaths


@dataclass(frozen=True, slots=True)
class ResolvedConfigPaths:
    global_path: Path | None
    project_path: Path | None
    user_path: Path | None


def discover_config_paths(working_dir: Path, config: FileConfigPaths) -> ResolvedConfigPaths:
    start_dir = resolve_working_directory(working_dir)

    paths_config = PathsConfig(
        config_dir_name=config.config_dir_name,
        project_subdir_name=config.project_subdir_name,
    )

    global_path = _resolve_global_config(config, paths_config)
    project_root = get_project_root(start_dir, paths_config)
    project_path, user_path = _resolve_project_configs(project_root, config, paths_config)

    return ResolvedConfigPaths(
        global_path=global_path,
        project_path=project_path,
        user_path=user_path,
    )


def _resolve_global_config(config: FileConfigPaths, paths_config: PathsConfig) -> Path | None:
    candidate = get_global_config_root(paths_config) / config.global_config_filename
    return candidate if candidate.is_file() else None


def _resolve_project_configs(
    project_root: Path | None,
    config: FileConfigPaths,
    paths_config: PathsConfig,
) -> tuple[Path | None, Path | None]:
    if project_root is None:
        return None, None

    project_dir = resolve_project_dir(project_root, paths_config)
    if project_dir is None:
        return None, None

    project_candidate = project_dir / config.project_config_filename
    user_candidate = project_dir / config.user_config_filename

    project_path = project_candidate if project_candidate.is_file() else None
    user_path = user_candidate if user_candidate.is_file() else None

    return project_path, user_path
