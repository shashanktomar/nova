from __future__ import annotations

import pytest
from pydantic import ValidationError

from nova.marketplace.models import (
    BundleCategory,
    BundleEntry,
    Contact,
    GitHubMarketplaceSource,
    GitMarketplaceSource,
    LocalMarketplaceSource,
    MarketplaceManifest,
    MarketplaceState,
)

VALID_NAME = "Ada Lovelace"
VALID_REPO = "owner/repo"
VALID_GIT_URL = "https://github.com/owner/repo.git"
VALID_VERSION = "1.2.3"


@pytest.mark.parametrize("name", [VALID_NAME, "Grace Hopper"])
def test_contact_accepts_non_empty_name(name: str) -> None:
    assert Contact(name=name).name == name


@pytest.mark.parametrize("name", [""])
def test_contact_rejects_empty_name(name: str) -> None:
    with pytest.raises(ValidationError):
        Contact(name=name)


@pytest.mark.parametrize(
    "email",
    [
        "ada@example.com",
        "user.name+tag@example.co.uk",
        None,
    ],
)
def test_contact_accepts_valid_email(email: str | None) -> None:
    contact = Contact(name=VALID_NAME, email=email)
    assert contact.email == email


@pytest.mark.parametrize(
    "email",
    [
        "not-an-email",
        "@example.com",
        "user@",
    ],
)
def test_contact_rejects_invalid_email(email: str) -> None:
    with pytest.raises(ValidationError):
        Contact(name=VALID_NAME, email=email)


@pytest.mark.parametrize("repo", [VALID_REPO, "Org-123/repo_name"])
def test_github_source_accepts_valid_repo(repo: str) -> None:
    assert GitHubMarketplaceSource(repo=repo).repo == repo


@pytest.mark.parametrize("repo", ["invalid repo", "owner", "owner/repo/extra"])
def test_github_source_rejects_invalid_repo(repo: str) -> None:
    with pytest.raises(ValidationError):
        GitHubMarketplaceSource(repo=repo)


@pytest.mark.parametrize(
    "url",
    [
        VALID_GIT_URL,
        "git@github.com:owner/repo.git",
        "git://github.com/owner/repo",
    ],
)
def test_git_source_accepts_valid_urls(url: str) -> None:
    assert GitMarketplaceSource(url=url).url == url


@pytest.mark.parametrize("url", ["ftp://example.com/repo.git", "owner/repo"])
def test_git_source_rejects_invalid_urls(url: str) -> None:
    with pytest.raises(ValidationError):
        GitMarketplaceSource(url=url)


def test_local_source_accepts_directory(tmp_path) -> None:
    assert LocalMarketplaceSource(path=tmp_path).path == tmp_path


def test_local_source_rejects_file(tmp_path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text("data")
    with pytest.raises(ValidationError):
        LocalMarketplaceSource(path=file_path)


@pytest.mark.parametrize(
    "version",
    [
        VALID_VERSION,
        "1.0.0-alpha",
        "2.0.0-rc.1+build.123",
    ],
)
def test_bundle_entry_accepts_semver(version: str) -> None:
    entry = BundleEntry(
        name="bundle",
        description="Bundle description",
        source="./bundles/bundle",
        category=BundleCategory.DEVELOPMENT,
        version=version,
    )
    assert str(entry.version) == version


@pytest.mark.parametrize("version", ["not-a-version", "", "1.0"])
def test_bundle_entry_rejects_invalid_semver(version: str) -> None:
    with pytest.raises(ValidationError):
        BundleEntry(
            name="bundle",
            description="desc",
            source="./bundles/bundle",
            version=version,
        )


@pytest.mark.parametrize(
    "field_name",
    ["description", "source"],
)
def test_bundle_entry_requires_non_empty_fields(field_name: str) -> None:
    kwargs = {
        "name": "bundle",
        "description": "A useful bundle",
        "source": "./bundles/bundle",
    }
    kwargs[field_name] = ""

    with pytest.raises(ValidationError):
        BundleEntry(**kwargs)


def test_marketplace_manifest_validates_entries() -> None:
    manifest = MarketplaceManifest(
        name="market",
        version="1.0.0",
        description="A marketplace",
        owner=Contact(name="Owner"),
        bundles=[
            BundleEntry(
                name="bundle",
                description="desc",
                source="./bundles/bundle",
            )
        ],
    )
    assert manifest.name == "market"
    assert len(manifest.bundles) == 1


@pytest.mark.parametrize("name", ["market", "another-market"])
def test_marketplace_state_accepts_name(name: str, tmp_path) -> None:
    state = MarketplaceState(
        name=name,
        source=GitHubMarketplaceSource(repo=VALID_REPO),
        install_location=tmp_path,
        last_updated="2025-10-21T12:00:00Z",
    )
    assert state.name == name


@pytest.mark.parametrize("name", [""])
def test_marketplace_state_rejects_empty_name(name: str, tmp_path) -> None:
    with pytest.raises(ValidationError):
        MarketplaceState(
            name=name,
            source=GitHubMarketplaceSource(repo=VALID_REPO),
            install_location=tmp_path,
            last_updated="2025-10-21T12:00:00Z",
        )
