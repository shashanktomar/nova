from __future__ import annotations

from pathlib import Path

import pytest

from nova.marketplace.models import (
    GitHubMarketplaceSource,
    GitMarketplaceSource,
    LocalMarketplaceSource,
    MarketplaceSourceParseError,
)
from nova.marketplace.sources import parse_source
from nova.utils.functools.models import is_err, is_ok


def test_parse_source_rejects_empty_string() -> None:
    result = parse_source("")

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, MarketplaceSourceParseError)
    assert "empty" in error.message.lower()


def test_parse_source_rejects_whitespace_only() -> None:
    result = parse_source("   ")

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, MarketplaceSourceParseError)


@pytest.mark.parametrize(
    "repo",
    [
        "owner/repo",
        "anthropics/nova-bundles",
        "user-name/repo_name",
        "Org123/MyRepo",
    ],
)
def test_parse_source_detects_github_repo(repo: str) -> None:
    result = parse_source(repo)

    assert is_ok(result)
    source = result.unwrap()
    assert isinstance(source, GitHubMarketplaceSource)
    assert source.repo == repo


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/owner/repo.git",
        "git@github.com:owner/repo.git",
        "git://github.com/owner/repo",
        "https://gitlab.com/group/project",
        "https://example.com/repo",
    ],
)
def test_parse_source_detects_git_url(url: str) -> None:
    result = parse_source(url)

    assert is_ok(result)
    source = result.unwrap()
    assert isinstance(source, GitMarketplaceSource)
    assert source.url == url


def test_parse_source_detects_local_absolute_path(tmp_path: Path) -> None:
    marketplace_dir = tmp_path / "marketplace"
    marketplace_dir.mkdir()

    result = parse_source(str(marketplace_dir))

    assert is_ok(result)
    source = result.unwrap()
    assert isinstance(source, LocalMarketplaceSource)
    assert source.path == marketplace_dir


def test_parse_source_detects_local_relative_path(tmp_path: Path) -> None:
    marketplace_dir = tmp_path / "marketplace"
    marketplace_dir.mkdir()

    result = parse_source("./marketplace", working_dir=tmp_path)

    assert is_ok(result)
    source = result.unwrap()
    assert isinstance(source, LocalMarketplaceSource)
    assert source.path == marketplace_dir


def test_parse_source_expands_tilde(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    marketplace_dir = tmp_path / "marketplace"
    marketplace_dir.mkdir()

    result = parse_source("~/marketplace")

    assert is_ok(result)
    source = result.unwrap()
    assert isinstance(source, LocalMarketplaceSource)
    assert source.path == marketplace_dir


def test_parse_source_rejects_nonexistent_local_path() -> None:
    result = parse_source("/nonexistent/path")

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, MarketplaceSourceParseError)


def test_parse_source_rejects_local_file(tmp_path: Path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text("data")

    result = parse_source(str(file_path))

    assert is_err(result)
    error = result.unwrap_err()
    assert isinstance(error, MarketplaceSourceParseError)


def test_parse_source_prioritizes_github_over_git() -> None:
    result = parse_source("owner/repo")

    assert is_ok(result)
    source = result.unwrap()
    assert isinstance(source, GitHubMarketplaceSource)


def test_parse_source_prioritizes_git_over_local() -> None:
    result = parse_source("https://github.com/owner/repo")

    assert is_ok(result)
    source = result.unwrap()
    assert isinstance(source, GitMarketplaceSource)


def test_parse_source_strips_whitespace() -> None:
    result = parse_source("  owner/repo  ")

    assert is_ok(result)
    source = result.unwrap()
    assert isinstance(source, GitHubMarketplaceSource)
    assert source.repo == "owner/repo"


def test_parse_source_preserves_original_in_error() -> None:
    original_input = "  invalid input  "
    result = parse_source(original_input)

    assert is_err(result)
    error = result.unwrap_err()
    assert error.source == original_input


def test_parse_source_relative_path_uses_working_dir(tmp_path: Path) -> None:
    working_dir = tmp_path / "project"
    working_dir.mkdir()
    marketplace_dir = working_dir / "local-marketplace"
    marketplace_dir.mkdir()

    result = parse_source("./local-marketplace", working_dir=working_dir)

    assert is_ok(result)
    source = result.unwrap()
    assert isinstance(source, LocalMarketplaceSource)
    assert source.path == marketplace_dir


def test_parse_source_relative_path_defaults_to_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    marketplace_dir = tmp_path / "marketplace"
    marketplace_dir.mkdir()

    result = parse_source("./marketplace")

    assert is_ok(result)
    source = result.unwrap()
    assert isinstance(source, LocalMarketplaceSource)
    assert source.path == marketplace_dir
