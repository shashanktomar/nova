from __future__ import annotations

import re
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nova.utils.functools.models import is_err, is_ok
from nova.utils.git import (
    GitCloneError,
    GitNotInstalledError,
    GitVersionError,
    clone_repository,
    get_git_version,
    is_git_installed,
)


class TestIsGitInstalled:
    """Tests for is_git_installed() function."""

    def test_returns_true_when_git_is_available(self) -> None:
        """Test that is_git_installed returns True when git command succeeds."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = is_git_installed()

            assert result is True
            mock_run.assert_called_once_with(
                ["git", "--version"],
                capture_output=True,
                check=True,
            )

    def test_returns_false_when_git_not_found(self) -> None:
        """Test that is_git_installed returns False when git is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = is_git_installed()

            assert result is False

    def test_returns_false_when_git_command_fails(self) -> None:
        """Test that is_git_installed returns False when git command fails."""
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
            result = is_git_installed()

            assert result is False


class TestGetGitVersion:
    """Tests for get_git_version() function."""

    def test_returns_version_string_when_successful(self) -> None:
        """Test that get_git_version returns Ok with version string."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="git version 2.39.2\n",
                returncode=0,
            )

            result = get_git_version()

            assert is_ok(result)
            assert result.unwrap() == "2.39.2"

    @pytest.mark.parametrize(
        "stdout",
        [
            "git version 2.39.2\n",
            "git version 2.45.1 (Apple Git-138)\n",
            "git version 1.8.3\n",
        ],
    )
    def test_parses_various_git_version_formats(self, stdout: str) -> None:
        """Test parsing different git version output formats."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=stdout, returncode=0)

            result = get_git_version()

            assert is_ok(result)
            # Extract expected version from stdout
            match = re.search(r"(\d+\.\d+\.\d+)", stdout)
            assert match is not None
            assert result.unwrap() == match.group(1)

    def test_returns_err_when_git_not_installed(self) -> None:
        """Test that get_git_version returns GitNotInstalledError when git not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = get_git_version()

            assert is_err(result)
            error = result.unwrap_err()
            assert isinstance(error, GitNotInstalledError)
            assert "not found" in error.message

    def test_returns_err_when_command_fails(self) -> None:
        """Test that get_git_version returns GitVersionError when command fails."""
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git", stderr="error")):
            result = get_git_version()

            assert is_err(result)
            error = result.unwrap_err()
            assert isinstance(error, GitVersionError)

    def test_returns_err_when_version_cannot_be_parsed(self) -> None:
        """Test that get_git_version returns error when version format is unexpected."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="unexpected output\n",
                returncode=0,
            )

            result = get_git_version()

            assert is_err(result)
            error = result.unwrap_err()
            assert isinstance(error, GitVersionError)
            assert "Could not parse" in error.message


class TestCloneRepository:
    """Tests for clone_repository() function."""

    def test_clones_repository_successfully(self, tmp_path: Path) -> None:
        """Test successful repository cloning."""
        destination = tmp_path / "repo"
        url = "https://github.com/example/repo.git"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = clone_repository(url, destination)

            assert is_ok(result)
            assert result.unwrap() == destination
            mock_run.assert_called_once_with(
                ["git", "clone", "--depth", "1", url, str(destination)],
                capture_output=True,
                text=True,
                check=True,
            )

    def test_respects_custom_depth_parameter(self, tmp_path: Path) -> None:
        """Test that custom depth parameter is respected."""
        destination = tmp_path / "repo"
        url = "https://github.com/example/repo.git"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = clone_repository(url, destination, depth=5)

            assert is_ok(result)
            mock_run.assert_called_once_with(
                ["git", "clone", "--depth", "5", url, str(destination)],
                capture_output=True,
                text=True,
                check=True,
            )

    def test_creates_parent_directories_if_needed(self, tmp_path: Path) -> None:
        """Test that parent directories are created if they don't exist."""
        destination = tmp_path / "nested" / "path" / "repo"
        url = "https://github.com/example/repo.git"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = clone_repository(url, destination)

            assert is_ok(result)
            assert destination.parent.exists()

    def test_returns_err_when_destination_exists(self, tmp_path: Path) -> None:
        """Test that cloning fails when destination already exists."""
        destination = tmp_path / "existing"
        destination.mkdir()
        url = "https://github.com/example/repo.git"

        result = clone_repository(url, destination)

        assert is_err(result)
        error = result.unwrap_err()
        assert isinstance(error, GitCloneError)
        assert "already exists" in error.message
        assert error.url == url

    def test_returns_err_when_git_not_installed(self, tmp_path: Path) -> None:
        """Test that cloning fails when git is not installed."""
        destination = tmp_path / "repo"
        url = "https://github.com/example/repo.git"

        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = clone_repository(url, destination)

            assert is_err(result)
            error = result.unwrap_err()
            assert isinstance(error, GitNotInstalledError)
            assert "not found" in error.message

    def test_returns_err_when_clone_fails(self, tmp_path: Path) -> None:
        """Test that cloning fails when git clone command fails."""
        destination = tmp_path / "repo"
        url = "https://github.com/example/nonexistent.git"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                128,
                "git",
                stderr="fatal: repository not found",
            )

            result = clone_repository(url, destination)

            assert is_err(result)
            error = result.unwrap_err()
            assert isinstance(error, GitCloneError)
            assert "Failed to clone" in error.message
            assert error.url == url

    def test_returns_err_on_unexpected_exception(self, tmp_path: Path) -> None:
        """Test that unexpected exceptions are handled gracefully."""
        destination = tmp_path / "repo"
        url = "https://github.com/example/repo.git"

        with patch("subprocess.run", side_effect=RuntimeError("Unexpected error")):
            result = clone_repository(url, destination)

            assert is_err(result)
            error = result.unwrap_err()
            assert isinstance(error, GitCloneError)
            assert "Unexpected error" in error.message
