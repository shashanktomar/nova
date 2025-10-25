"""Common models used across Nova."""

from typing import Literal

from pydantic import BaseModel

from nova.constants import APP_NAME


class AppInfo(BaseModel):
    project_name: str = APP_NAME
    version: str = "0.1.0"
    environment: Literal["test", "dev", "prod"] = "dev"


class AppPaths(BaseModel):
    config_dir_name: str = APP_NAME
    data_dir_name: str = APP_NAME
    project_subdir_name: str = f".{APP_NAME}"
    global_config_filename: str = "config.yaml"
    project_config_filename: str = "config.yaml"
    user_config_filename: str = "config.local.yaml"
    marketplaces_dir_name: str = "marketplaces"
    marketplaces_metadata_filename: str = "data.json"
