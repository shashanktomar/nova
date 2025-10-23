"""Git utility functions."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from nova.utils.functools.models import Err, Ok, Result


def is_git_installed() -> bool:
    """Check if git command is available."""
    try:
        subprocess.run(
            ["git", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_git_version() -> Result[str, str]:
    """Get installed git version.

    Returns:
        Ok(version): Git version string (e.g., "2.39.0")
        Err(message): Git not installed or version check failed
    """
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )

        match = re.search(r"git version (\d+\.\d+\.\d+)", result.stdout)
        if match:
            return Ok(match.group(1))

        return Err(f"Could not parse git version from: {result.stdout}")

    except FileNotFoundError:
        return Err("git command not found")
    except subprocess.CalledProcessError as e:
        return Err(f"Failed to get git version: {e.stderr}")


def clone_repository(
    url: str,
    destination: Path,
    *,
    depth: int = 1,
) -> Result[Path, str]:
    """Clone a git repository to destination.

    Args:
        url: Git repository URL
        destination: Local directory to clone to
        depth: Clone depth (default: 1 for shallow clone)

    Returns:
        Ok(Path): Path to cloned repository
        Err(message): Clone failed with error message
    """
    if destination.exists():
        return Err(f"Destination already exists: {destination}")

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            ["git", "clone", "--depth", str(depth), url, str(destination)],
            capture_output=True,
            text=True,
            check=True,
        )

        return Ok(destination)

    except FileNotFoundError:
        return Err("git command not found. Please install git.")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else "Unknown error"
        return Err(f"Failed to clone repository: {stderr}")
    except Exception as e:
        return Err(f"Unexpected error cloning repository: {e}")
