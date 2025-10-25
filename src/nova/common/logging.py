"""Logging utilities for Nova using Loguru.

This module provides logging configuration for both CLI and library usage:
- CLI usage: File-based logging with rotation and retention
- Library usage: Logging disabled by default, can be enabled by library users
"""

import sys
from pathlib import Path
from typing import Literal

import loguru
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from nova.constants import APP_NAME
from nova.utils import PathsConfig, get_data_directory

from .models import AppInfo


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(default=True)
    log_level: Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    log_file: str | None = Field(default=None)
    rotation: str = Field(default="1 MB")
    retention: str = Field(default="7 days")
    format: Literal["json", "text"] = Field(default="text")


def setup_cli_logging(app_info: AppInfo, config: LoggingConfig, paths: PathsConfig) -> int:
    logger.enable(APP_NAME)
    logger.remove()
    logger.configure(extra={"scope": "cli", "env": app_info.environment})

    log_file = Path(config.log_file).expanduser() if config.log_file else _get_default_log_file_path(paths)

    log_file.parent.mkdir(parents=True, exist_ok=True)

    if config.format == "json":
        handler_id = logger.add(
            log_file,
            level=config.log_level,
            rotation=config.rotation,
            retention=config.retention,
            serialize=True,
            diagnose=(app_info.environment == "dev"),
        )
    else:
        handler_id = logger.add(
            log_file,
            level=config.log_level,
            rotation=config.rotation,
            retention=config.retention,
            format=_get_text_format(),
            diagnose=(app_info.environment == "dev"),
        )

    logger.debug(
        "CLI logging initialized",
        log_file=str(log_file),
        level=config.log_level,
        format=config.format,
    )

    return handler_id


def disable_library_logging() -> None:
    logger.disable(APP_NAME)


def enable_library_logging(level: str = "INFO") -> int:
    logger.enable(APP_NAME)
    logger.remove()

    handler_id = logger.add(
        sys.stderr,
        level=level,
        format=_get_text_format(),
        colorize=False,
    )

    return handler_id


def create_logger(scope: str) -> "loguru.Logger":
    return logger.bind(scope=scope)


def _get_text_format() -> str:
    return "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message} | {extra}\n{exception}"


def _get_default_log_file_path(paths: PathsConfig) -> Path:
    data_dir = get_data_directory(paths)
    logs_dir = data_dir / "logs"
    return logs_dir / "nova.log"
