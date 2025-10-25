from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

from nova.common import AppDirectories, AppInfo, AppPaths
from nova.config.file import ConfigFileNames, ConfigStoreSettings


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

    def to_app_directories(self) -> AppDirectories:
        return AppDirectories(
            app_name=self.paths.config_dir_name,
            project_marker=self.paths.project_subdir_name,
        )

    def to_config_store_settings(self) -> ConfigStoreSettings:
        return ConfigStoreSettings(
            directories=self.to_app_directories(),
            filenames=ConfigFileNames(
                global_file=self.paths.global_config_filename,
                project_file=self.paths.project_config_filename,
                user_file=self.paths.user_config_filename,
            ),
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
