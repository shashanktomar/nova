"""Git utility functions."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from pydantic import BaseModel

from nova.utils.functools.models import Err, Ok, Result


class GitError(BaseModel):
    """Base error for git operations."""

    message: str


class GitNotInstalledError(GitError):
    """Git command not found."""

    pass


class GitCloneError(GitError):
    """Failed to clone repository."""

    url: str


class GitVersionError(GitError):
    """Failed to get git version."""

    pass


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


def get_git_version() -> Result[str, GitError]:
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )

        if (match := re.search(r"git version (\d+\.\d+\.\d+)", result.stdout)):
            return Ok(match.group(1))

        return Err(GitVersionError(message=f"Could not parse git version from: {result.stdout}"))

    except FileNotFoundError:
        return Err(GitNotInstalledError(message="git command not found"))
    except subprocess.CalledProcessError as e:
        return Err(GitVersionError(message=f"Failed to get git version: {e.stderr}"))


def clone_repository(
    url: str,
    destination: Path,
    *,
    depth: int = 1,
) -> Result[Path, GitError]:
    if destination.exists():
        return Err(GitCloneError(url=url, message=f"Destination already exists: {destination}"))

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
        return Err(GitNotInstalledError(message="git command not found. Please install git."))
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else "Unknown error"
        return Err(GitCloneError(url=url, message=f"Failed to clone repository: {stderr}"))
    except Exception as e:
        return Err(GitCloneError(url=url, message=f"Unexpected error cloning repository: {e}"))
