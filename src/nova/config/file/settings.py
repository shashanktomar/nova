"""File-based config store settings."""

from __future__ import annotations

from dataclasses import dataclass

from nova.utils.directories import AppDirectories


@dataclass(frozen=True)
class ConfigFileNames:
    """Config file naming convention.

    Attributes:
        global_file: Filename for global config (~/.config/nova/)
        project_file: Filename for project config (.nova/)
        user_file: Filename for user-specific config (.nova/)
    """

    global_file: str = "config.yaml"
    project_file: str = "config.yaml"
    user_file: str = "config.local.yaml"


@dataclass(frozen=True)
class ConfigStoreSettings:
    """Complete settings for file-based config store."""

    directories: AppDirectories
    filenames: ConfigFileNames

    @property
    def app_name(self) -> str:
        return self.directories.app_name

    @property
    def project_marker(self) -> str:
        return self.directories.project_marker

    @property
    def global_file(self) -> str:
        return self.filenames.global_file

    @property
    def project_file(self) -> str:
        return self.filenames.project_file

    @property
    def user_file(self) -> str:
        return self.filenames.user_file
