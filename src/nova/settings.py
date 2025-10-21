"""Application settings and constants for Nova.

This module provides centralized app-level configuration including:
- Core app metadata (name, version, environment)
- Path-related constants (directory names, filenames)

Settings are loaded from environment variables and .env files using Pydantic Settings.

Environment Variables:
    NOVA_APP__PROJECT_NAME: Override project name (default: nova)
    NOVA_APP__VERSION: Override version (default: 0.1.0)
    NOVA_APP__ENVIRONMENT: Set environment - test/dev/prod (default: dev)
    NOVA_PATHS__CONFIG_DIR_NAME: Override config directory name (default: nova)
    NOVA_PATHS__GLOBAL_CONFIG_FILENAME: Override global config filename (default: config.yaml)
    NOVA_PATHS__PROJECT_CONFIG_FILENAME: Override project config filename (default: nova.yaml)
    NOVA_PATHS__PROJECT_SUBDIR_NAME: Override project subdirectory (default: .nova)

Example .env file:
    NOVA_APP__ENVIRONMENT=prod
    NOVA_APP__VERSION=1.0.0
    NOVA_PATHS__CONFIG_DIR_NAME=.config

Usage:
    from nova.settings import settings

    print(f"Running {settings.app.project_name} v{settings.app.version}")
    print(f"Config dir: {settings.paths.config_dir_name}")
"""

from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    """Path configuration for Nova.

    Attributes:
        config_dir_name: Directory name for global config (e.g., ~/.config/nova)
        project_subdir_name: Subdirectory name for project configs
        global_config_filename: Filename for global config file
        project_config_filename: Filename for project-level config file (in .nova subdir)
        user_config_filename: Filename for user-specific config file (in .nova subdir)
    """

    config_dir_name: str = "nova"
    project_subdir_name: str = ".nova"
    global_config_filename: str = "config.yaml"
    project_config_filename: str = "config.yaml"
    user_config_filename: str = "config.local.yaml"


class Settings(BaseSettings):
    """Nova application settings.

    Provides centralized configuration management with support for:
    - Environment variable overrides
    - .env file loading
    - Nested settings structure
    - Type validation

    Access settings via the pre-initialized `settings` singleton:
        from nova.settings import settings
        settings.app.version
        settings.paths.config_dir_name
    """

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


def get_settings() -> Settings:
    """Get the singleton settings instance.

    Returns:
        Settings: The application settings

    Example:
        from nova.settings import get_settings

        settings = get_settings()
        print(settings.app.version)
        print(settings.paths.config_dir_name)
    """
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
