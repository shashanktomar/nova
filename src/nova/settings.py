from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from nova.config.file.config import FileConfigPaths
from nova.utils.paths import PathsConfig


class AppInfo(BaseModel):
    """Application metadata.

    Attributes:
        project_name: The name of the project
        version: The current version of the application
        environment: The environment the app is running in (test/dev/prod)
    """

    project_name: str = "nova"
    version: str = "0.1.0"
    environment: Literal["test", "dev", "prod"] = "dev"


class AppPaths(BaseModel):
    """Path configuration for Nova following XDG Base Directory standard.

    Attributes:
        config_dir_name: Directory name for config (e.g., ~/.config/nova)
        data_dir_name: Directory name for data (e.g., ~/.local/share/nova)
        project_subdir_name: Subdirectory name for project configs
        global_config_filename: Filename for global config file
        project_config_filename: Filename for project-level config file (in .nova subdir)
        user_config_filename: Filename for user-specific config file (in .nova subdir)
        marketplaces_dir_name: Directory name for marketplace clones (in data dir)
        marketplaces_metadata_filename: Filename for marketplace metadata
    """

    # XDG Base Directory paths
    config_dir_name: str = "nova"
    data_dir_name: str = "nova"

    # Project paths
    project_subdir_name: str = ".nova"

    # Config filenames
    global_config_filename: str = "config.yaml"
    project_config_filename: str = "config.yaml"
    user_config_filename: str = "config.local.yaml"

    # Marketplace data paths
    marketplaces_dir_name: str = "marketplaces"
    marketplaces_metadata_filename: str = "data.json"


class Settings(BaseSettings):
    app: AppInfo = AppInfo()
    paths: AppPaths = AppPaths()

    model_config = SettingsConfigDict(
        env_prefix="NOVA_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        nested_model_default_partial_update=True,
    )

    def to_file_config_paths(self) -> FileConfigPaths:
        return FileConfigPaths(
            global_config_filename=self.paths.global_config_filename,
            project_config_filename=self.paths.project_config_filename,
            user_config_filename=self.paths.user_config_filename,
            project_subdir_name=self.paths.project_subdir_name,
            config_dir_name=self.paths.config_dir_name,
        )

    def to_paths_config(self) -> PathsConfig:
        return PathsConfig(
            config_dir_name=self.paths.config_dir_name,
            project_subdir_name=self.paths.project_subdir_name,
        )


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Private singleton instance
_settings: Settings | None = None

# Convenience access - pre-initialized singleton
settings = get_settings()


__all__ = [
    "AppInfo",
    "AppPaths",
    "Settings",
    "get_settings",
    "settings",
]
