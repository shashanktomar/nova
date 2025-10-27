from __future__ import annotations

from pathlib import Path

import pytest

from nova.marketplace.models import (
    GitHubMarketplaceSource,
    GitMarketplaceSource,
    LocalMarketplaceSource,
    MarketplaceSourceParseError,
)
from nova.marketplace.sources import (
    GitHubSourceProvider,
    GitSourceProvider,
    LocalSourceProvider,
    create_source_provider,
    parse_source,
)
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


def test_create_source_provider_returns_github_provider() -> None:
    source = GitHubMarketplaceSource(repo="owner/repo")

    provider = create_source_provider(source)

    assert isinstance(provider, GitHubSourceProvider)


def test_create_source_provider_returns_git_provider() -> None:
    source = GitMarketplaceSource(url="https://example.com/repo.git")

    provider = create_source_provider(source)

    assert isinstance(provider, GitSourceProvider)


def test_create_source_provider_returns_local_provider(tmp_path: Path) -> None:
    marketplace_dir = tmp_path / "marketplace"
    marketplace_dir.mkdir()
    source = LocalMarketplaceSource(path=marketplace_dir)

    provider = create_source_provider(source)

    assert isinstance(provider, LocalSourceProvider)


def test_github_provider_display_name() -> None:
    source = GitHubMarketplaceSource(repo="owner/repo")
    provider = GitHubSourceProvider(source)

    assert provider.display_name() == "owner/repo"


def test_git_provider_display_name() -> None:
    source = GitMarketplaceSource(url="https://example.com/repo.git")
    provider = GitSourceProvider(source)

    assert provider.display_name() == "https://example.com/repo.git"


def test_local_provider_display_name(tmp_path: Path) -> None:
    marketplace_dir = tmp_path / "marketplace"
    marketplace_dir.mkdir()
    source = LocalMarketplaceSource(path=marketplace_dir)
    provider = LocalSourceProvider(source)

    assert provider.display_name() == str(marketplace_dir)


def test_local_provider_move_to_storage_returns_temp_path(tmp_path: Path) -> None:
    marketplace_dir = tmp_path / "marketplace"
    marketplace_dir.mkdir()
    source = LocalMarketplaceSource(path=marketplace_dir)
    provider = LocalSourceProvider(source)

    temp_path = tmp_path / "temp"
    final_path = tmp_path / "final"

    result = provider.move_to_storage(temp_path, final_path)

    assert result == temp_path


def test_local_provider_cleanup_does_nothing(tmp_path: Path) -> None:
    marketplace_dir = tmp_path / "marketplace"
    marketplace_dir.mkdir()
    source = LocalMarketplaceSource(path=marketplace_dir)
    provider = LocalSourceProvider(source)

    install_dir = tmp_path / "install"
    install_dir.mkdir()

    provider.cleanup_on_removal(install_dir)

    assert install_dir.exists()


def test_github_provider_move_to_storage_moves_directory(tmp_path: Path) -> None:
    source = GitHubMarketplaceSource(repo="owner/repo")
    provider = GitHubSourceProvider(source)

    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    (temp_dir / "file.txt").write_text("content")

    final_dir = tmp_path / "final" / "marketplace"

    result = provider.move_to_storage(temp_dir, final_dir)

    assert result == final_dir
    assert final_dir.exists()
    assert (final_dir / "file.txt").read_text() == "content"
    assert not temp_dir.exists()


def test_github_provider_move_to_storage_replaces_existing(tmp_path: Path) -> None:
    source = GitHubMarketplaceSource(repo="owner/repo")
    provider = GitHubSourceProvider(source)

    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    (temp_dir / "new.txt").write_text("new")

    final_dir = tmp_path / "final"
    final_dir.mkdir()
    (final_dir / "old.txt").write_text("old")

    result = provider.move_to_storage(temp_dir, final_dir)

    assert result == final_dir
    assert (final_dir / "new.txt").exists()
    assert not (final_dir / "old.txt").exists()


def test_github_provider_cleanup_removes_directory(tmp_path: Path) -> None:
    source = GitHubMarketplaceSource(repo="owner/repo")
    provider = GitHubSourceProvider(source)

    install_dir = tmp_path / "marketplace"
    install_dir.mkdir()
    (install_dir / "file.txt").write_text("content")

    provider.cleanup_on_removal(install_dir)

    assert not install_dir.exists()


def test_git_provider_move_to_storage_moves_directory(tmp_path: Path) -> None:
    source = GitMarketplaceSource(url="https://example.com/repo.git")
    provider = GitSourceProvider(source)

    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    (temp_dir / "file.txt").write_text("content")

    final_dir = tmp_path / "final" / "marketplace"

    result = provider.move_to_storage(temp_dir, final_dir)

    assert result == final_dir
    assert final_dir.exists()
    assert (final_dir / "file.txt").read_text() == "content"


def test_git_provider_cleanup_removes_directory(tmp_path: Path) -> None:
    source = GitMarketplaceSource(url="https://example.com/repo.git")
    provider = GitSourceProvider(source)

    install_dir = tmp_path / "marketplace"
    install_dir.mkdir()

    provider.cleanup_on_removal(install_dir)

    assert not install_dir.exists()
