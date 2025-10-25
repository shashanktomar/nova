"""Application directory structure settings."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppDirectories:
    """Application directory structure settings.

    Defines where Nova stores files relative to standard locations:
    - ~/.config/{app_name}/
    - ~/.local/share/{app_name}/
    - ./{project_marker}/

    Attributes:
        app_name: Name used in XDG directories (config and data)
        project_marker: Directory name that marks a Nova project root
    """

    app_name: str = "nova"
    project_marker: str = ".nova"
