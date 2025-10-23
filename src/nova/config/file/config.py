from dataclasses import dataclass


@dataclass(frozen=True)
class FileConfigPaths:
    global_config_filename: str
    project_config_filename: str
    user_config_filename: str
    project_subdir_name: str
    config_dir_name: str
