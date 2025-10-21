import sys
from functools import lru_cache
from typing import Literal

import loguru
from loguru import logger
from pydantic import Field
from pydantic.dataclasses import dataclass

from nova.settings import AppInfo

type Logger = "loguru.Logger"


@dataclass(kw_only=True)
class LoggingConfig:
    app_info: AppInfo
    log_level: Literal["DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")


@lru_cache
def get_color_from_name(name: str | None) -> str:
    """
    Map a name to a predefined color in a deterministic way.
    """
    colors = [
        "blue",
        "magenta",
        "yellow",
        "white",
        "light-blue",
        "light-green",
        "light-magenta",
        "light-yellow",
    ]

    if not name:
        return colors[0]  # Default color for empty string

    # Create a deterministic index based on the name
    # Use a simple hash function that sums character values
    name_hash = sum(ord(c) for c in name)
    color_index = name_hash % len(colors)

    return colors[color_index]


def get_dev_logs_format(record: "loguru.Record") -> str:
    """Format with colors for development environment with service at beginning."""
    scope = record["extra"].get("scope", None)
    color_name = get_color_from_name(scope)
    module_color = f"<{color_name}>"

    # Get all extra fields except 'scope' and 'env' which we handle separately
    extra_fields = {k: v for k, v in record["extra"].items() if k not in ["scope", "env"]}
    extra_str = ""
    if extra_fields:
        extra_str = " | " + " ".join(f"{k}={v}" for k, v in extra_fields.items())

    return (
        f"{module_color}[{{extra[scope]}}]</> | "
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}:{function}:{line}</cyan> - "
        "<level>{message}</level>"
        f"{extra_str}\n{{exception}}"
    )


def setup_logging(config: LoggingConfig) -> None:
    """
    Setup the default logger
    Configure Loguru for all environments (container/serverless/local).
    Logs are directed to stdout/stderr with format depending on environment.
    """
    # Remove default handler
    logger.remove()
    logger.configure(extra={"scope": "global", "env": config.app_info.environment})

    # Set minimum level based on environment
    if config.app_info.environment == "dev":
        # Use pretty, colorized output for local development
        logger.add(sys.stderr, level=config.log_level, format=get_dev_logs_format, colorize=True)
    else:
        # Use JSON output for production/containerized environments
        logger.add(sys.stdout, level=config.log_level, serialize=True, format="{message}")

        # Add a separate handler for errors that will go to stderr
        logger.add(sys.stderr, level="ERROR", serialize=True, format="{message}", diagnose=False)

    # Log initial message
    logger.info(
        f"Logging initialized: "
        f"{config.app_info.project_name} v{config.app_info.version} ({config.app_info.environment})"
    )


def create_logger(scope: str) -> Logger:
    return logger.bind(scope=scope)
