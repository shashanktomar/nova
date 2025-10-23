"""Data and error models for Nova marketplace management."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, DirectoryPath, EmailStr
from pydantic_extra_types.semantic_version import SemanticVersion

from nova.utils.types import DirectUrl, GitHubRepo, GitUrl, NonEmptyString


class MarketplaceSourceType(str, Enum):
    """Marketplace source types."""

    GITHUB = "github"
    GIT = "git"
    LOCAL = "local"
    URL = "url"


class MarketplaceScope(str, Enum):
    """Marketplace configuration scope."""

    GLOBAL = "global"
    PROJECT = "project"


class BundleCategory(str, Enum):
    """Bundle category types."""

    DEVELOPMENT = "development"


class Contact(BaseModel):
    """Contact information for marketplace owners or bundle authors."""

    model_config = ConfigDict(extra="ignore")

    name: NonEmptyString
    email: EmailStr | None = None


class GitHubMarketplaceSource(BaseModel):
    """GitHub marketplace source (stored in config.yaml)."""

    model_config = ConfigDict(extra="ignore")

    type: Literal["github"] = "github"
    repo: GitHubRepo


class GitMarketplaceSource(BaseModel):
    """Generic git repository marketplace source (stored in config.yaml)."""

    model_config = ConfigDict(extra="ignore")

    type: Literal["git"] = "git"
    url: GitUrl


class LocalMarketplaceSource(BaseModel):
    """Local filesystem marketplace source (stored in config.yaml)."""

    model_config = ConfigDict(extra="ignore")

    type: Literal["local"] = "local"
    path: DirectoryPath


class URLMarketplaceSource(BaseModel):
    """Direct URL marketplace source (stored in config.yaml)."""

    model_config = ConfigDict(extra="ignore")

    type: Literal["url"] = "url"
    url: DirectUrl


MarketplaceSource = (
    GitHubMarketplaceSource
    | GitMarketplaceSource
    | LocalMarketplaceSource
    | URLMarketplaceSource
)


class BundleEntry(BaseModel):
    """Bundle entry in marketplace manifest."""

    model_config = ConfigDict(extra="ignore")

    name: NonEmptyString
    description: NonEmptyString
    source: NonEmptyString
    category: BundleCategory | None = None
    version: SemanticVersion | None = None
    author: Contact | None = None


class MarketplaceInfo(BaseModel):
    """Marketplace information for listing."""

    model_config = ConfigDict(extra="ignore")

    name: str
    description: str
    source: MarketplaceSource
    bundle_count: int


class MarketplaceManifest(BaseModel):
    """Marketplace manifest (from marketplace.json)."""

    model_config = ConfigDict(extra="ignore")

    name: NonEmptyString
    version: NonEmptyString
    description: str
    owner: Contact
    bundles: list[BundleEntry]


class MarketplaceState(BaseModel):
    """Marketplace cloned state metadata stored in data.json."""

    model_config = ConfigDict(extra="ignore")

    name: NonEmptyString
    source: MarketplaceSource
    install_location: Path
    last_updated: str

class MarketplaceError(BaseModel):
    """Base marketplace error model."""

    model_config = ConfigDict(extra="forbid")

    message: str


class MarketplaceNotFoundError(MarketplaceError):
    """Marketplace not found."""

    name_or_source: str


class MarketplaceAddError(MarketplaceError):
    """Error adding marketplace (clone, fetch, or validation failed)."""

    source: str


class MarketplaceAlreadyExistsError(MarketplaceError):
    """Marketplace with this name already exists."""

    name: str
    existing_source: str


class MarketplaceInvalidManifestError(MarketplaceError):
    """Invalid or missing marketplace.json."""

    source: str


MarketplaceErrorType = (
    MarketplaceNotFoundError
    | MarketplaceAddError
    | MarketplaceAlreadyExistsError
    | MarketplaceInvalidManifestError
)


__all__ = [
    "BundleCategory",
    "BundleEntry",
    "Contact",
    "GitHubMarketplaceSource",
    "GitMarketplaceSource",
    "LocalMarketplaceSource",
    "MarketplaceAddError",
    "MarketplaceAlreadyExistsError",
    "MarketplaceError",
    "MarketplaceErrorType",
    "MarketplaceInfo",
    "MarketplaceInvalidManifestError",
    "MarketplaceManifest",
    "MarketplaceNotFoundError",
    "MarketplaceScope",
    "MarketplaceSource",
    "MarketplaceSourceType",
    "MarketplaceState",
    "URLMarketplaceSource",
]
