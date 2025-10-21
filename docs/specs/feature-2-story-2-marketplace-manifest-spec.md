# Feature 2, Story 2: Marketplace Manifest System - Implementation Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Updated:** 2025-10-20
**Author:** AI Architecture Team (zen-architect)

## Overview

This specification defines the implementation for the marketplace manifest system (Feature 2, Story 2, P0 priority). It follows the "bricks and studs" modular design philosophy - each module is a self-contained brick with clear contracts (studs) that can be independently generated and regenerated.

This story implements the manifest-based catalog system. It defines the manifest schema, implements fetching and parsing of marketplace manifests from configured sources, and provides simple file-based caching for performance.

**Story Scope:**
- Marketplace-level manifest format (YAML preferred for Nova)
- Bundle metadata in manifest (name, version, description, source, type, author)
- Generic bundle type field (not validated, just a tag)
- Manifest fetching (HTTP URLs, local paths, git repos)
- Manifest parsing and validation
- Manifest caching (simple file-based cache)

**Out of Scope:**
- Bundle-specific manifests (Features 3, 5 define their own)
- Bundle type validation (Nova Core handles that)
- Bundle content structure (Features 3, 5)
- Installation logic (Story 4)
- Bundle downloading/extraction (Story 4)

## Architecture Summary

**Approach:** Simple YAML-based manifest with file caching

**Key Decisions:**
- YAML for manifest format (human-friendly, readable)
- Simple file-based caching (no database, just files in cache dir)
- Generic "type" field without semantic validation (marketplace doesn't care about bundle types)
- Support HTTP URLs and local paths (git support via URL cloning)
- Graceful degradation on network failures (use cache if available)
- Clear error messages for common failure modes

**Manifest Schema (YAML):**
```yaml
version: "1.0"
bundles:
  - name: "fintech-advisor"
    type: "domain"  # Generic tag - no validation
    version: "1.0.0"
    description: "Financial advisory domain knowledge"
    source:
      type: "git"
      url: "https://github.com/nova-bundles/fintech-advisor"
    author:
      name: "Nova Team"
      email: "team@nova.dev"
    homepage: "https://docs.nova.dev/bundles/fintech-advisor"
```

**Caching Strategy:**
- Cache manifests in `~/.cache/nova/manifests/` (XDG Base Directory)
- Cache key: Hash of marketplace source URL
- Cache TTL: 1 hour (configurable)
- Invalidate on demand via CLI command
- Fall back to cache on network errors

## Module Structure

```
src/nova/
├── marketplace/
│   ├── __init__.py          # Public API exports (already exists from Story 1)
│   ├── models.py            # Already exists from Story 1
│   ├── config.py            # Already exists from Story 1
│   ├── manifest.py          # Manifest models and schema
│   ├── fetcher.py           # Fetch manifests from sources
│   ├── parser.py            # Parse and validate manifests
│   └── cache.py             # Simple manifest caching
└── cli/
    └── commands/
        └── marketplace.py   # Update with manifest commands
```

---

## Module Specifications

### Module: marketplace.manifest

**Purpose:** Define manifest schema and data models

**Location:** `src/nova/marketplace/manifest.py`

**Contract:**
- **Inputs:** Dictionary data from YAML files
- **Outputs:** Validated Pydantic model instances
- **Side Effects:** None (pure data models)
- **Dependencies:** pydantic, typing

**Public Interface:**

```python
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Literal

class BundleAuthor(BaseModel):
    """Bundle author information.

    Attributes:
        name: Author name
        email: Author email (optional)

    Example:
        >>> author = BundleAuthor(name="Nova Team", email="team@nova.dev")
    """
    name: str = Field(
        min_length=1,
        max_length=200,
        description="Author name"
    )
    email: str | None = Field(
        default=None,
        description="Author email address"
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Basic email format validation.

        Args:
            v: Email to validate

        Returns:
            Validated email or None

        Raises:
            ValueError: If email format is invalid
        """
        if v is None:
            return v

        # Basic email validation (contains @ and .)
        if "@" not in v or "." not in v.split("@")[1]:
            raise ValueError("Invalid email format")

        return v


class BundleSource(BaseModel):
    """Bundle source location information.

    Describes where the bundle can be downloaded from.

    Attributes:
        type: Source type (git, http, local)
        url: URL or path to bundle source

    Example:
        >>> source = BundleSource(
        ...     type="git",
        ...     url="https://github.com/nova-bundles/fintech-advisor"
        ... )
    """
    type: Literal["git", "http", "local"] = Field(
        description="Source type"
    )
    url: str = Field(
        description="URL or path to bundle source"
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str, info) -> str:
        """Validate URL based on source type.

        Args:
            v: URL to validate
            info: Validation context with source type

        Returns:
            Validated URL

        Raises:
            ValueError: If URL is invalid for the source type
        """
        source_type = info.data.get("type")

        if source_type in ["git", "http"]:
            # Must be a valid URL
            if not v.startswith(("http://", "https://", "git://")):
                raise ValueError(
                    f"URL for {source_type} source must start with http://, https://, or git://"
                )
        elif source_type == "local":
            # Can be any path (will be validated when accessed)
            pass

        return v


class BundleManifestEntry(BaseModel):
    """Single bundle entry in marketplace manifest.

    Represents one bundle available in the marketplace.

    Attributes:
        name: Unique bundle identifier (within marketplace)
        type: Generic bundle type tag (not validated)
        version: Bundle version (semver recommended)
        description: Human-readable bundle description
        source: Bundle source location
        author: Bundle author information (optional)
        homepage: Bundle documentation/homepage URL (optional)

    Example:
        >>> entry = BundleManifestEntry(
        ...     name="fintech-advisor",
        ...     type="domain",
        ...     version="1.0.0",
        ...     description="Financial advisory domain knowledge",
        ...     source=BundleSource(type="git", url="https://github.com/..."),
        ...     author=BundleAuthor(name="Nova Team")
        ... )
    """
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Bundle name (unique identifier)"
    )
    type: str = Field(
        min_length=1,
        max_length=50,
        description="Bundle type (generic tag, not validated)"
    )
    version: str = Field(
        min_length=1,
        max_length=50,
        description="Bundle version"
    )
    description: str = Field(
        min_length=1,
        max_length=500,
        description="Bundle description"
    )
    source: BundleSource = Field(
        description="Bundle source location"
    )
    author: BundleAuthor | None = Field(
        default=None,
        description="Bundle author information"
    )
    homepage: HttpUrl | None = Field(
        default=None,
        description="Bundle homepage/documentation URL"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate bundle name format.

        Args:
            v: Name to validate

        Returns:
            Validated name

        Raises:
            ValueError: If name contains invalid characters
        """
        # Name must be alphanumeric with hyphens/underscores only
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Bundle name must contain only letters, numbers, hyphens, and underscores"
            )
        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version format (basic check).

        Args:
            v: Version to validate

        Returns:
            Validated version

        Note:
            This is a basic validation. Semver is recommended but not enforced.
        """
        # Basic validation: version should not be empty or just whitespace
        if not v.strip():
            raise ValueError("Version cannot be empty")
        return v.strip()


class MarketplaceManifest(BaseModel):
    """Marketplace manifest containing bundle catalog.

    The top-level manifest structure for a marketplace source.

    Attributes:
        version: Manifest format version
        bundles: List of available bundles

    Example:
        >>> manifest = MarketplaceManifest(
        ...     version="1.0",
        ...     bundles=[
        ...         BundleManifestEntry(
        ...             name="fintech-advisor",
        ...             type="domain",
        ...             version="1.0.0",
        ...             description="Financial advisory knowledge",
        ...             source=BundleSource(type="git", url="https://...")
        ...         )
        ...     ]
        ... )
    """
    version: str = Field(
        default="1.0",
        description="Manifest format version"
    )
    bundles: list[BundleManifestEntry] = Field(
        default_factory=list,
        description="List of bundles in this marketplace"
    )

    @field_validator("bundles")
    @classmethod
    def validate_bundles(cls, v: list[BundleManifestEntry]) -> list[BundleManifestEntry]:
        """Validate bundles list.

        Args:
            v: Bundles to validate

        Returns:
            Validated bundles list

        Raises:
            ValueError: If bundle names are not unique
        """
        # Check for duplicate bundle names
        names = [bundle.name for bundle in v]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(
                f"Bundle names must be unique within manifest. "
                f"Duplicates found: {set(duplicates)}"
            )

        return v

    def get_bundle(self, name: str) -> BundleManifestEntry | None:
        """Get bundle entry by name.

        Args:
            name: Bundle name to find

        Returns:
            BundleManifestEntry if found, None otherwise
        """
        for bundle in self.bundles:
            if bundle.name == name:
                return bundle
        return None

    def has_bundle(self, name: str) -> bool:
        """Check if bundle exists in manifest.

        Args:
            name: Bundle name to check

        Returns:
            True if bundle exists, False otherwise
        """
        return self.get_bundle(name) is not None

    def filter_by_type(self, bundle_type: str) -> list[BundleManifestEntry]:
        """Filter bundles by type.

        Args:
            bundle_type: Bundle type to filter by

        Returns:
            List of bundles matching the type
        """
        return [bundle for bundle in self.bundles if bundle.type == bundle_type]
```

**Validation Rules:**
- Bundle names: Alphanumeric with hyphens/underscores, 1-100 chars
- Bundle type: Any string 1-50 chars (not validated semantically)
- Version: Any non-empty string (semver recommended but not enforced)
- Description: 1-500 chars
- Author email: Basic format validation (@, .)
- Source URL: Must match source type (http/https for http/git, any for local)
- Bundle names must be unique within manifest
- Empty bundles list is valid

**Testing Requirements:**
- Test BundleAuthor validation (valid, invalid email)
- Test BundleSource validation for each type (git, http, local)
- Test BundleManifestEntry validation (valid, invalid names, versions)
- Test MarketplaceManifest validation
- Test duplicate bundle name detection
- Test get_bundle(), has_bundle(), filter_by_type() methods
- Test empty bundles list

---

### Module: marketplace.parser

**Purpose:** Parse and validate YAML manifests

**Location:** `src/nova/marketplace/parser.py`

**Contract:**
- **Inputs:** YAML string or file path
- **Outputs:** Validated MarketplaceManifest instance
- **Side Effects:** Reads files if path provided
- **Dependencies:** yaml, pathlib, marketplace.manifest

**Public Interface:**

```python
from pathlib import Path
from typing import Any
import yaml

from nova.marketplace.manifest import MarketplaceManifest


class ManifestParseError(Exception):
    """Error parsing marketplace manifest."""
    pass


def parse_manifest_yaml(yaml_content: str) -> MarketplaceManifest:
    """Parse YAML string into MarketplaceManifest.

    Args:
        yaml_content: YAML string to parse

    Returns:
        Validated MarketplaceManifest instance

    Raises:
        ManifestParseError: If YAML is invalid or validation fails

    Example:
        >>> yaml_str = '''
        ... version: "1.0"
        ... bundles:
        ...   - name: test-bundle
        ...     type: domain
        ...     version: 1.0.0
        ...     description: Test bundle
        ...     source:
        ...       type: git
        ...       url: https://github.com/test/bundle
        ... '''
        >>> manifest = parse_manifest_yaml(yaml_str)
        >>> assert len(manifest.bundles) == 1
    """
    try:
        # Parse YAML
        data = yaml.safe_load(yaml_content)

        if data is None:
            # Empty YAML file
            data = {}

        if not isinstance(data, dict):
            raise ManifestParseError(
                f"Manifest must be a YAML dictionary, got {type(data).__name__}"
            )

        # Validate with Pydantic
        manifest = MarketplaceManifest(**data)
        return manifest

    except yaml.YAMLError as e:
        raise ManifestParseError(
            f"Invalid YAML syntax: {str(e)}"
        ) from e
    except Exception as e:
        raise ManifestParseError(
            f"Failed to parse manifest: {str(e)}"
        ) from e


def parse_manifest_file(path: Path) -> MarketplaceManifest:
    """Parse manifest from file.

    Args:
        path: Path to YAML manifest file

    Returns:
        Validated MarketplaceManifest instance

    Raises:
        ManifestParseError: If file cannot be read or parsed
        FileNotFoundError: If file does not exist

    Example:
        >>> manifest = parse_manifest_file(Path("/path/to/manifest.yaml"))
        >>> print(f"Found {len(manifest.bundles)} bundles")
    """
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")

    try:
        content = path.read_text(encoding="utf-8")
        return parse_manifest_yaml(content)
    except Exception as e:
        raise ManifestParseError(
            f"Failed to parse manifest file {path}: {str(e)}"
        ) from e


def validate_manifest_dict(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate manifest dictionary without raising exceptions.

    Useful for checking manifest validity before parsing.

    Args:
        data: Dictionary to validate as manifest

    Returns:
        Tuple of (is_valid, error_messages)
        If valid: (True, [])
        If invalid: (False, ["error1", "error2", ...])

    Example:
        >>> data = {"version": "1.0", "bundles": []}
        >>> is_valid, errors = validate_manifest_dict(data)
        >>> assert is_valid
    """
    errors = []

    try:
        MarketplaceManifest(**data)
        return (True, [])
    except Exception as e:
        errors.append(str(e))
        return (False, errors)
```

**Error Handling:**
- YAML syntax errors: Wrap with context about line/column
- Missing required fields: List all missing fields
- Invalid field values: Explain what was expected
- Duplicate bundle names: List the duplicates
- Invalid source URLs: Explain URL format requirements

**Error Message Examples:**

```
❌ Manifest Parse Error

  File: /path/to/manifest.yaml
  Error: Invalid YAML syntax: mapping values are not allowed here
  Line: 5, Column: 15

  Suggestion: Check YAML indentation and syntax
```

```
❌ Manifest Validation Error

  File: /path/to/manifest.yaml
  Error: Bundle names must be unique within manifest
  Duplicates found: {'fintech-advisor', 'tax-helper'}

  Suggestion: Each bundle must have a unique name
```

**Testing Requirements:**
- Test parsing valid YAML
- Test parsing invalid YAML syntax
- Test parsing empty YAML
- Test parsing non-dict YAML (list, string, etc.)
- Test validation errors (missing fields, invalid values)
- Test duplicate bundle name detection
- Test parse_manifest_file() with existing file
- Test parse_manifest_file() with non-existent file
- Test validate_manifest_dict() for valid/invalid manifests

---

### Module: marketplace.cache

**Purpose:** Simple file-based manifest caching

**Location:** `src/nova/marketplace/cache.py`

**Contract:**
- **Inputs:** Marketplace source URL, manifest content
- **Outputs:** Cached manifest or None
- **Side Effects:** Reads/writes cache files in `~/.cache/nova/manifests/`
- **Dependencies:** pathlib, hashlib, datetime, json

**Public Interface:**

```python
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import json
from typing import Any


class ManifestCache:
    """Simple file-based cache for marketplace manifests.

    Caches manifests in ~/.cache/nova/manifests/ using URL hash as key.

    Attributes:
        cache_dir: Directory where cache files are stored
        ttl_seconds: Cache TTL in seconds (default: 3600 = 1 hour)

    Example:
        >>> cache = ManifestCache()
        >>> cache.set("https://example.com/manifest.yaml", manifest_data)
        >>> cached = cache.get("https://example.com/manifest.yaml")
    """

    def __init__(self, cache_dir: Path | None = None, ttl_seconds: int = 3600):
        """Initialize manifest cache.

        Args:
            cache_dir: Cache directory (uses XDG default if None)
            ttl_seconds: Cache TTL in seconds (default: 1 hour)
        """
        if cache_dir is None:
            # Use XDG Base Directory for cache
            xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
            if xdg_cache_home:
                base_cache = Path(xdg_cache_home)
            else:
                base_cache = Path.home() / ".cache"

            cache_dir = base_cache / "nova" / "manifests"

        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds

        # Create cache directory if needed
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL.

        Args:
            url: Marketplace source URL

        Returns:
            Hash string to use as cache filename

        Algorithm:
            1. SHA256 hash of URL
            2. Use first 32 chars of hex digest
            3. Ensures unique, filesystem-safe keys
        """
        return hashlib.sha256(url.encode()).hexdigest()[:32]

    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for URL.

        Args:
            url: Marketplace source URL

        Returns:
            Path to cache file
        """
        cache_key = self._get_cache_key(url)
        return self.cache_dir / f"{cache_key}.json"

    def get(self, url: str) -> dict[str, Any] | None:
        """Get cached manifest for URL.

        Args:
            url: Marketplace source URL

        Returns:
            Cached manifest data if valid, None if not cached or expired

        Example:
            >>> cache = ManifestCache()
            >>> data = cache.get("https://marketplace.nova.dev/manifest.yaml")
            >>> if data is None:
            ...     print("Cache miss or expired")
        """
        cache_path = self._get_cache_path(url)

        if not cache_path.exists():
            return None

        try:
            # Read cache file
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_entry = json.load(f)

            # Check expiration
            cached_at = datetime.fromisoformat(cache_entry["cached_at"])
            age_seconds = (datetime.now() - cached_at).total_seconds()

            if age_seconds > self.ttl_seconds:
                # Expired - remove cache file
                cache_path.unlink()
                return None

            # Return cached manifest data
            return cache_entry["manifest"]

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Invalid cache file - remove it
            cache_path.unlink()
            return None

    def set(self, url: str, manifest_data: dict[str, Any]) -> None:
        """Cache manifest for URL.

        Args:
            url: Marketplace source URL
            manifest_data: Manifest data to cache (as dict)

        Side Effects:
            Writes cache file to disk

        Example:
            >>> cache = ManifestCache()
            >>> manifest_data = {"version": "1.0", "bundles": [...]}
            >>> cache.set("https://marketplace.nova.dev/manifest.yaml", manifest_data)
        """
        cache_path = self._get_cache_path(url)

        cache_entry = {
            "url": url,
            "cached_at": datetime.now().isoformat(),
            "manifest": manifest_data
        }

        # Write cache file
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_entry, f, indent=2)

    def invalidate(self, url: str) -> bool:
        """Invalidate (delete) cached manifest for URL.

        Args:
            url: Marketplace source URL

        Returns:
            True if cache was deleted, False if not cached

        Example:
            >>> cache = ManifestCache()
            >>> if cache.invalidate("https://marketplace.nova.dev/manifest.yaml"):
            ...     print("Cache cleared")
        """
        cache_path = self._get_cache_path(url)

        if cache_path.exists():
            cache_path.unlink()
            return True

        return False

    def clear_all(self) -> int:
        """Clear all cached manifests.

        Returns:
            Number of cache files deleted

        Example:
            >>> cache = ManifestCache()
            >>> count = cache.clear_all()
            >>> print(f"Cleared {count} cached manifests")
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        return count

    def get_cache_info(self, url: str) -> dict[str, Any] | None:
        """Get cache metadata for URL.

        Args:
            url: Marketplace source URL

        Returns:
            Dict with cache metadata if cached, None otherwise
            Keys: url, cached_at, age_seconds, expired

        Example:
            >>> cache = ManifestCache()
            >>> info = cache.get_cache_info("https://marketplace.nova.dev/manifest.yaml")
            >>> if info:
            ...     print(f"Cached {info['age_seconds']} seconds ago")
        """
        cache_path = self._get_cache_path(url)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_entry = json.load(f)

            cached_at = datetime.fromisoformat(cache_entry["cached_at"])
            age_seconds = (datetime.now() - cached_at).total_seconds()
            expired = age_seconds > self.ttl_seconds

            return {
                "url": cache_entry["url"],
                "cached_at": cache_entry["cached_at"],
                "age_seconds": int(age_seconds),
                "expired": expired
            }

        except (json.JSONDecodeError, KeyError, ValueError):
            return None
```

**Cache Strategy:**
- Cache key: SHA256 hash of source URL (first 32 chars)
- Cache location: `~/.cache/nova/manifests/{hash}.json`
- Cache format: JSON with metadata (url, cached_at, manifest)
- TTL: 1 hour (configurable)
- Expired cache: Automatically deleted on access
- Invalid cache: Automatically deleted on read error

**Testing Requirements:**
- Test cache_key generation (same URL = same key)
- Test cache_path generation
- Test get() with cached data (valid TTL)
- Test get() with expired cache
- Test get() with non-existent cache
- Test get() with invalid cache file (corrupted JSON)
- Test set() creates cache file
- Test invalidate() removes cache
- Test clear_all() removes all caches
- Test get_cache_info() returns correct metadata

---

### Module: marketplace.fetcher

**Purpose:** Fetch manifests from various sources

**Location:** `src/nova/marketplace/fetcher.py`

**Contract:**
- **Inputs:** MarketplaceSource instance
- **Outputs:** Manifest YAML content as string
- **Side Effects:**
  - Makes HTTP requests for remote URLs
  - Reads local files
  - May clone git repos to temp directory
  - Uses cache (reads/writes)
- **Dependencies:** requests, pathlib, marketplace.models, marketplace.cache

**Public Interface:**

```python
from pathlib import Path
from typing import Any
import requests

from nova.marketplace.models import MarketplaceSource
from nova.marketplace.cache import ManifestCache
from nova.marketplace.parser import parse_manifest_yaml, ManifestParseError
from nova.marketplace.manifest import MarketplaceManifest


class ManifestFetchError(Exception):
    """Error fetching marketplace manifest."""
    pass


class ManifestFetcher:
    """Fetch marketplace manifests from various sources.

    Supports HTTP URLs and local file paths. Uses caching for performance.

    Attributes:
        cache: ManifestCache instance for caching
        timeout_seconds: HTTP request timeout (default: 30)

    Example:
        >>> fetcher = ManifestFetcher()
        >>> source = MarketplaceSource(
        ...     name="official",
        ...     url="https://marketplace.nova.dev/manifest.yaml",
        ...     type="manifest"
        ... )
        >>> manifest = fetcher.fetch(source)
    """

    def __init__(
        self,
        cache: ManifestCache | None = None,
        timeout_seconds: int = 30
    ):
        """Initialize manifest fetcher.

        Args:
            cache: ManifestCache instance (creates default if None)
            timeout_seconds: HTTP request timeout in seconds
        """
        self.cache = cache if cache is not None else ManifestCache()
        self.timeout_seconds = timeout_seconds

    def fetch(
        self,
        source: MarketplaceSource,
        use_cache: bool = True
    ) -> MarketplaceManifest:
        """Fetch manifest from marketplace source.

        Args:
            source: MarketplaceSource to fetch from
            use_cache: Whether to use cached manifest (default: True)

        Returns:
            Parsed MarketplaceManifest

        Raises:
            ManifestFetchError: If fetching or parsing fails

        Example:
            >>> fetcher = ManifestFetcher()
            >>> source = MarketplaceSource(...)
            >>> manifest = fetcher.fetch(source)
            >>> print(f"Found {len(manifest.bundles)} bundles")
        """
        url = str(source.url)

        # Try cache first if enabled
        if use_cache:
            cached_data = self.cache.get(url)
            if cached_data is not None:
                try:
                    return MarketplaceManifest(**cached_data)
                except Exception:
                    # Invalid cache - continue to fetch fresh
                    pass

        # Fetch fresh manifest
        try:
            if url.startswith(("http://", "https://")):
                yaml_content = self._fetch_http(url)
            elif url.startswith("file://"):
                yaml_content = self._fetch_local(url[7:])  # Remove file:// prefix
            else:
                # Assume local path
                yaml_content = self._fetch_local(url)

            # Parse manifest
            manifest = parse_manifest_yaml(yaml_content)

            # Cache the parsed data
            self.cache.set(url, manifest.model_dump())

            return manifest

        except ManifestParseError:
            # Re-raise parse errors as-is
            raise
        except Exception as e:
            # Try to use stale cache as fallback
            cached_data = self.cache.get(url)
            if cached_data is not None:
                try:
                    return MarketplaceManifest(**cached_data)
                except Exception:
                    pass

            # No cache available - raise error
            raise ManifestFetchError(
                f"Failed to fetch manifest from {url}: {str(e)}"
            ) from e

    def _fetch_http(self, url: str) -> str:
        """Fetch manifest from HTTP(S) URL.

        Args:
            url: HTTP(S) URL to manifest file

        Returns:
            YAML content as string

        Raises:
            ManifestFetchError: If HTTP request fails
        """
        try:
            response = requests.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            return response.text

        except requests.exceptions.Timeout:
            raise ManifestFetchError(
                f"Request timeout after {self.timeout_seconds}s: {url}"
            )
        except requests.exceptions.ConnectionError as e:
            raise ManifestFetchError(
                f"Connection error fetching {url}: {str(e)}"
            )
        except requests.exceptions.HTTPError as e:
            raise ManifestFetchError(
                f"HTTP error fetching {url}: {e.response.status_code} {e.response.reason}"
            )
        except Exception as e:
            raise ManifestFetchError(
                f"Failed to fetch {url}: {str(e)}"
            ) from e

    def _fetch_local(self, path_str: str) -> str:
        """Fetch manifest from local file path.

        Args:
            path_str: Local file path

        Returns:
            YAML content as string

        Raises:
            ManifestFetchError: If file cannot be read
        """
        try:
            path = Path(path_str).expanduser().resolve()

            if not path.exists():
                raise ManifestFetchError(f"Manifest file not found: {path}")

            if not path.is_file():
                raise ManifestFetchError(f"Path is not a file: {path}")

            return path.read_text(encoding="utf-8")

        except ManifestFetchError:
            raise
        except Exception as e:
            raise ManifestFetchError(
                f"Failed to read local manifest {path_str}: {str(e)}"
            ) from e

    def invalidate_cache(self, source: MarketplaceSource) -> bool:
        """Invalidate cached manifest for source.

        Args:
            source: MarketplaceSource to invalidate

        Returns:
            True if cache was cleared, False if not cached
        """
        return self.cache.invalidate(str(source.url))
```

**Fetch Strategy:**
1. Check cache first (if enabled)
2. If cache hit and valid: Return cached manifest
3. If cache miss or disabled: Fetch fresh
4. Parse and validate fetched content
5. Cache successful result
6. On fetch error: Fall back to stale cache if available

**Error Handling:**
- Network errors: Provide clear message, try cache fallback
- HTTP errors: Include status code and reason
- Timeout errors: Mention timeout duration
- File not found: Clear message about path
- Parse errors: Re-raise with context

**Error Message Examples:**

```
❌ Manifest Fetch Error

  Source: https://marketplace.nova.dev/manifest.yaml
  Error: Connection error - Failed to establish connection

  Using cached version from 45 minutes ago
```

```
❌ Manifest Fetch Error

  Source: /path/to/local/manifest.yaml
  Error: Manifest file not found

  Suggestion: Check that the file path is correct
```

**Testing Requirements:**
- Test fetch() with HTTP URL (successful)
- Test fetch() with local file path (successful)
- Test fetch() with file:// URL
- Test cache usage (hit, miss)
- Test cache fallback on network error
- Test HTTP errors (404, 500, timeout)
- Test file not found error
- Test invalid manifest parsing
- Test invalidate_cache()
- Mock HTTP requests for isolation

---

### Module: cli.commands.marketplace (Update)

**Purpose:** Add manifest-related CLI commands

**Location:** `src/nova/cli/commands/marketplace.py`

**Contract:**
- **Inputs:** Command-line arguments
- **Outputs:** Terminal output showing manifest info
- **Side Effects:**
  - Fetches manifests from sources
  - Reads/writes cache
  - Displays formatted output
- **Dependencies:** typer, rich, marketplace modules

**Public Interface (New Commands):**

```python
# Add to existing marketplace CLI commands from Story 1

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from nova.marketplace.config import get_marketplace_config, list_marketplace_sources
from nova.marketplace.fetcher import ManifestFetcher, ManifestFetchError
from nova.marketplace.cache import ManifestCache

app = typer.Typer(help="Manage marketplace sources")
console = Console()


@app.command("refresh")
def marketplace_refresh(
    marketplace: str | None = typer.Argument(
        None,
        help="Marketplace name to refresh (all if not specified)"
    ),
) -> None:
    """Refresh manifest cache from marketplace source(s).

    Fetches fresh manifests from configured marketplace sources,
    bypassing the cache and updating cached versions.

    Example:
        nova marketplace refresh              # Refresh all marketplaces
        nova marketplace refresh official     # Refresh specific marketplace
    """
    marketplace_config = get_marketplace_config()
    sources = list_marketplace_sources(marketplace_config)

    if not sources:
        console.print("[yellow]No marketplace sources configured[/yellow]")
        console.print("\nTip: Add a marketplace source:")
        console.print("  nova marketplace add <name> <url>")
        raise typer.Exit(1)

    # Filter to specific marketplace if specified
    if marketplace:
        sources = [s for s in sources if s.name == marketplace]
        if not sources:
            console.print(f"[red]Error: Marketplace '{marketplace}' not found[/red]")
            raise typer.Exit(1)

    fetcher = ManifestFetcher()

    # Refresh each source
    success_count = 0
    fail_count = 0

    with console.status("[bold green]Refreshing manifests..."):
        for source in sources:
            try:
                # Fetch without cache
                manifest = fetcher.fetch(source, use_cache=False)

                console.print(
                    f"[green]✓[/green] Refreshed '{source.name}' "
                    f"({len(manifest.bundles)} bundles)"
                )
                success_count += 1

            except ManifestFetchError as e:
                console.print(f"[red]✗[/red] Failed to refresh '{source.name}': {e}")
                fail_count += 1

    # Summary
    console.print(f"\nRefreshed {success_count} marketplace(s)")
    if fail_count > 0:
        console.print(f"[yellow]Failed to refresh {fail_count} marketplace(s)[/yellow]")


@app.command("show")
def marketplace_show(
    marketplace: str = typer.Argument(..., help="Marketplace name to show"),
) -> None:
    """Show bundles available in a marketplace.

    Displays the manifest contents for a configured marketplace source,
    including all available bundles and their metadata.

    Example:
        nova marketplace show official
    """
    marketplace_config = get_marketplace_config()
    source = marketplace_config.get_source(marketplace)

    if source is None:
        console.print(f"[red]Error: Marketplace '{marketplace}' not found[/red]")
        console.print("\nConfigured marketplaces:")
        for s in list_marketplace_sources(marketplace_config):
            console.print(f"  • {s.name}")
        raise typer.Exit(1)

    # Fetch manifest
    fetcher = ManifestFetcher()

    try:
        with console.status(f"[bold green]Fetching manifest from '{marketplace}'..."):
            manifest = fetcher.fetch(source)

    except ManifestFetchError as e:
        console.print(f"[red]Error fetching manifest: {e}[/red]")
        raise typer.Exit(1)

    # Display header
    console.print(Panel(
        f"[bold cyan]{marketplace}[/bold cyan]\n"
        f"URL: {source.url}\n"
        f"Bundles: {len(manifest.bundles)}",
        title="Marketplace Info"
    ))

    if not manifest.bundles:
        console.print("\n[yellow]No bundles available in this marketplace[/yellow]")
        return

    # Display bundles table
    table = Table(title=f"\nAvailable Bundles in '{marketplace}'")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Version", style="yellow")
    table.add_column("Description", style="white")

    for bundle in manifest.bundles:
        table.add_row(
            bundle.name,
            bundle.type,
            bundle.version,
            bundle.description[:60] + "..." if len(bundle.description) > 60 else bundle.description
        )

    console.print(table)


@app.command("search")
def marketplace_search(
    query: str = typer.Argument(..., help="Search query (bundle name or type)"),
    marketplace: str | None = typer.Option(
        None,
        "--marketplace",
        "-m",
        help="Search in specific marketplace only"
    ),
    bundle_type: str | None = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by bundle type"
    ),
) -> None:
    """Search for bundles across marketplaces.

    Searches bundle names and descriptions for the query string.
    Can filter by marketplace and/or bundle type.

    Example:
        nova marketplace search finance
        nova marketplace search tax --type domain
        nova marketplace search advisor --marketplace official
    """
    marketplace_config = get_marketplace_config()
    sources = list_marketplace_sources(marketplace_config)

    if not sources:
        console.print("[yellow]No marketplace sources configured[/yellow]")
        raise typer.Exit(1)

    # Filter to specific marketplace if requested
    if marketplace:
        sources = [s for s in sources if s.name == marketplace]
        if not sources:
            console.print(f"[red]Error: Marketplace '{marketplace}' not found[/red]")
            raise typer.Exit(1)

    fetcher = ManifestFetcher()
    matches = []

    # Search each marketplace
    with console.status("[bold green]Searching marketplaces..."):
        for source in sources:
            try:
                manifest = fetcher.fetch(source)

                for bundle in manifest.bundles:
                    # Filter by type if specified
                    if bundle_type and bundle.type != bundle_type:
                        continue

                    # Search in name and description
                    query_lower = query.lower()
                    if (query_lower in bundle.name.lower() or
                        query_lower in bundle.description.lower()):
                        matches.append((source.name, bundle))

            except ManifestFetchError as e:
                console.print(f"[yellow]Warning: Failed to search '{source.name}': {e}[/yellow]")

    # Display results
    if not matches:
        console.print(f"\n[yellow]No bundles found matching '{query}'[/yellow]")
        return

    console.print(f"\n[green]Found {len(matches)} bundle(s) matching '{query}'[/green]\n")

    # Group by marketplace
    for source_name in sorted(set(m[0] for m in matches)):
        source_matches = [m[1] for m in matches if m[0] == source_name]

        console.print(f"[bold cyan]From '{source_name}':[/bold cyan]")
        for bundle in source_matches:
            console.print(f"  • [bold]{bundle.name}[/bold] ({bundle.type}) - v{bundle.version}")
            console.print(f"    {bundle.description}")
        console.print()


@app.command("cache-clear")
def marketplace_cache_clear(
    marketplace: str | None = typer.Argument(
        None,
        help="Marketplace name to clear (all if not specified)"
    ),
) -> None:
    """Clear cached manifests.

    Removes cached manifest files. Next fetch will download fresh manifests.

    Example:
        nova marketplace cache-clear           # Clear all cached manifests
        nova marketplace cache-clear official  # Clear specific marketplace cache
    """
    cache = ManifestCache()

    if marketplace:
        # Clear specific marketplace
        marketplace_config = get_marketplace_config()
        source = marketplace_config.get_source(marketplace)

        if source is None:
            console.print(f"[red]Error: Marketplace '{marketplace}' not found[/red]")
            raise typer.Exit(1)

        if cache.invalidate(str(source.url)):
            console.print(f"[green]✓[/green] Cleared cache for '{marketplace}'")
        else:
            console.print(f"[yellow]No cache found for '{marketplace}'[/yellow]")

    else:
        # Clear all caches
        count = cache.clear_all()
        console.print(f"[green]✓[/green] Cleared {count} cached manifest(s)")


@app.command("cache-info")
def marketplace_cache_info() -> None:
    """Show cache status for configured marketplaces.

    Displays cache age and size for each marketplace source.

    Example:
        nova marketplace cache-info
    """
    marketplace_config = get_marketplace_config()
    sources = list_marketplace_sources(marketplace_config)

    if not sources:
        console.print("[yellow]No marketplace sources configured[/yellow]")
        raise typer.Exit(1)

    cache = ManifestCache()

    table = Table(title="Marketplace Cache Status")
    table.add_column("Marketplace", style="cyan")
    table.add_column("Cached", style="green")
    table.add_column("Age", style="yellow")
    table.add_column("Status", style="white")

    for source in sources:
        info = cache.get_cache_info(str(source.url))

        if info is None:
            table.add_row(source.name, "No", "-", "Not cached")
        else:
            age_minutes = info["age_seconds"] // 60
            age_str = f"{age_minutes}m ago"
            status = "Expired" if info["expired"] else "Valid"
            status_color = "red" if info["expired"] else "green"

            table.add_row(
                source.name,
                "Yes",
                age_str,
                f"[{status_color}]{status}[/{status_color}]"
            )

    console.print(table)
```

**New CLI Commands:**

1. **`nova marketplace refresh [marketplace]`**
   - Fetch fresh manifests, bypassing cache
   - Updates cached versions
   - Can refresh all or specific marketplace

2. **`nova marketplace show <marketplace>`**
   - Display bundles in marketplace
   - Shows bundle metadata in table
   - Fetches from cache if available

3. **`nova marketplace search <query> [--marketplace] [--type]`**
   - Search bundles across marketplaces
   - Filter by marketplace or type
   - Searches names and descriptions

4. **`nova marketplace cache-clear [marketplace]`**
   - Clear cached manifests
   - Can clear all or specific marketplace

5. **`nova marketplace cache-info`**
   - Show cache status
   - Displays age and validity

**Testing Requirements:**
- Test refresh command (all, specific marketplace)
- Test show command with valid marketplace
- Test show command with invalid marketplace
- Test search command (various queries)
- Test search with --type filter
- Test search with --marketplace filter
- Test cache-clear (all, specific)
- Test cache-info display
- Mock ManifestFetcher for testing

---

## Example Manifest Files

### Minimal Valid Manifest

```yaml
version: "1.0"
bundles: []  # Empty bundles list is valid
```

### Single Bundle Manifest

```yaml
version: "1.0"
bundles:
  - name: "fintech-advisor"
    type: "domain"
    version: "1.0.0"
    description: "Financial advisory domain knowledge"
    source:
      type: "git"
      url: "https://github.com/nova-bundles/fintech-advisor"
```

### Complete Manifest with Multiple Bundles

```yaml
version: "1.0"
bundles:
  - name: "fintech-advisor"
    type: "domain"
    version: "1.0.0"
    description: "Financial advisory domain knowledge"
    source:
      type: "git"
      url: "https://github.com/nova-bundles/fintech-advisor"
    author:
      name: "Nova Team"
      email: "team@nova.dev"
    homepage: "https://docs.nova.dev/bundles/fintech-advisor"

  - name: "tax-helper"
    type: "domain"
    version: "2.1.0"
    description: "Tax calculation and compliance domain knowledge"
    source:
      type: "http"
      url: "https://bundles.nova.dev/tax-helper-2.1.0.tar.gz"
    author:
      name: "Tax Domain Experts"
      email: "tax@example.com"

  - name: "local-test-bundle"
    type: "test"
    version: "0.1.0"
    description: "Local test bundle for development"
    source:
      type: "local"
      url: "/path/to/local/bundle"
```

---

## CLI Usage Examples

### Refresh Marketplace Manifests

```bash
# Refresh all marketplaces
nova marketplace refresh

# Output:
# ✓ Refreshed 'official' (12 bundles)
# ✓ Refreshed 'company' (5 bundles)
#
# Refreshed 2 marketplace(s)

# Refresh specific marketplace
nova marketplace refresh official

# Output:
# ✓ Refreshed 'official' (12 bundles)
#
# Refreshed 1 marketplace(s)
```

### Show Marketplace Contents

```bash
nova marketplace show official

# Output:
# ╭──────────────── Marketplace Info ────────────────╮
# │ official                                         │
# │ URL: https://marketplace.nova.dev/manifest.yaml  │
# │ Bundles: 12                                      │
# ╰──────────────────────────────────────────────────╯
#
# Available Bundles in 'official'
# ┌────────────────┬────────┬─────────┬──────────────────────┐
# │ Name           │ Type   │ Version │ Description          │
# ├────────────────┼────────┼─────────┼──────────────────────┤
# │ fintech-advisor│ domain │ 1.0.0   │ Financial advisory...│
# │ tax-helper     │ domain │ 2.1.0   │ Tax calculation...   │
# └────────────────┴────────┴─────────┴──────────────────────┘
```

### Search for Bundles

```bash
# Simple search
nova marketplace search finance

# Output:
# Found 3 bundle(s) matching 'finance'
#
# From 'official':
#   • fintech-advisor (domain) - v1.0.0
#     Financial advisory domain knowledge
#   • finance-analyzer (tool) - v0.5.0
#     Financial analysis tools

# Search with type filter
nova marketplace search advisor --type domain

# Search in specific marketplace
nova marketplace search tax --marketplace official
```

### Manage Cache

```bash
# Show cache status
nova marketplace cache-info

# Output:
# Marketplace Cache Status
# ┌──────────┬────────┬─────────┬────────┐
# │ Marketplace│Cached│ Age     │ Status │
# ├──────────┼────────┼─────────┼────────┤
# │ official │ Yes    │ 15m ago │ Valid  │
# │ company  │ Yes    │ 75m ago │ Expired│
# └──────────┴────────┴─────────┴────────┘

# Clear all caches
nova marketplace cache-clear

# Output:
# ✓ Cleared 2 cached manifest(s)

# Clear specific cache
nova marketplace cache-clear official

# Output:
# ✓ Cleared cache for 'official'
```

---

## Error Handling

### Network Errors with Cache Fallback

```
⚠ Warning: Network error fetching manifest
  Using cached version from 45 minutes ago

✓ Loaded manifest from cache (12 bundles)
```

### Invalid Manifest Format

```
❌ Manifest Parse Error

  File: https://marketplace.nova.dev/manifest.yaml
  Error: Bundle names must be unique within manifest
  Duplicates found: {'tax-helper'}

  Suggestion: Each bundle must have a unique name
```

### Marketplace Not Found

```
❌ Error: Marketplace 'unknown' not found

Configured marketplaces:
  • official
  • company
```

---

## Testing Strategy

### Unit Tests

**Test each module independently:**

- `test_marketplace_manifest.py` - Manifest models
  - Test BundleAuthor, BundleSource, BundleManifestEntry validation
  - Test MarketplaceManifest validation
  - Test duplicate bundle detection
  - Test manifest methods (get_bundle, filter_by_type)

- `test_marketplace_parser.py` - YAML parsing
  - Test parse_manifest_yaml() with valid YAML
  - Test parse_manifest_yaml() with invalid YAML
  - Test parse_manifest_file() with existing/non-existent files
  - Test validate_manifest_dict()

- `test_marketplace_cache.py` - Caching
  - Test cache get/set operations
  - Test cache expiration
  - Test cache invalidation
  - Test cache_info()
  - Test clear_all()

- `test_marketplace_fetcher.py` - Fetching
  - Test fetch() with HTTP URLs (mock requests)
  - Test fetch() with local files
  - Test cache usage and fallback
  - Test error handling

### Integration Tests

**Test complete manifest system:**

- `test_manifest_integration.py` - End-to-end
  - Test fetching from configured marketplace
  - Test parsing and caching workflow
  - Test cache hit/miss scenarios
  - Test network error fallback

- `test_manifest_cli.py` - CLI commands
  - Test refresh command
  - Test show command
  - Test search command
  - Test cache-clear and cache-info commands
  - Mock fetcher for isolation

### Test Fixtures

**Test data:**

```python
@pytest.fixture
def sample_manifest_yaml():
    """Sample manifest YAML for testing."""
    return """
version: "1.0"
bundles:
  - name: test-bundle
    type: domain
    version: 1.0.0
    description: Test bundle
    source:
      type: git
      url: https://github.com/test/bundle
    author:
      name: Test Author
      email: test@example.com
"""


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir
```

---

## Success Criteria

- [ ] Manifest models defined and validated (BundleAuthor, BundleSource, BundleManifestEntry, MarketplaceManifest)
- [ ] YAML parsing works correctly with clear error messages
- [ ] File-based caching implemented with TTL
- [ ] Manifest fetching from HTTP URLs works
- [ ] Manifest fetching from local paths works
- [ ] Cache fallback on network errors works
- [ ] CLI command `nova marketplace refresh` works
- [ ] CLI command `nova marketplace show` works
- [ ] CLI command `nova marketplace search` works
- [ ] CLI command `nova marketplace cache-clear` works
- [ ] CLI command `nova marketplace cache-info` works
- [ ] Error messages are clear and actionable
- [ ] Code follows ruthless simplicity principles
- [ ] All modules have clear, single responsibilities
- [ ] Comprehensive test coverage (unit + integration)
- [ ] Generic bundle type field (no semantic validation)

---

## Dependencies

**This Story Depends On:**
- Feature 1: Config Management - MUST be complete
- Feature 2, Story 1: Marketplace Configuration - MUST be complete
  - Uses MarketplaceSource model
  - Uses marketplace config operations

**This Story Enables:**
- Feature 2, Story 3: Bundle discovery from marketplace
- Feature 2, Story 4: Bundle installation from marketplace

**Required Packages:**
- pydantic >= 2.12.3 (already in project)
- pyyaml >= 6.0 (already in project)
- requests (for HTTP fetching - should be added)
- rich (already in project from Story 1)

**New Dependencies:**
```bash
cd /path/to/nova
uv add requests
```

---

## Implementation Phases

### Phase 1: Manifest Models (Module: marketplace.manifest)
**Estimated Time:** 1 hour
**Deliverables:**
- BundleAuthor, BundleSource models
- BundleManifestEntry model
- MarketplaceManifest model
- Unit tests for all models

### Phase 2: Parsing and Caching (Modules: parser, cache)
**Estimated Time:** 1.5 hours
**Deliverables:**
- YAML parsing with error handling
- File-based cache implementation
- Unit tests for parsing and caching

### Phase 3: Fetching (Module: fetcher)
**Estimated Time:** 1 hour
**Deliverables:**
- HTTP and local file fetching
- Cache integration
- Error handling and fallback
- Unit tests for fetching

### Phase 4: CLI Commands (Update: cli/commands/marketplace.py)
**Estimated Time:** 1 hour
**Deliverables:**
- refresh, show, search commands
- cache-clear, cache-info commands
- CLI integration tests

### Phase 5: Polish and Documentation
**Estimated Time:** 0.5 hours
**Deliverables:**
- Example manifest files
- Error message improvements
- CLI help text
- Usage documentation

**Total Estimated Time:** 5 hours (buffer beyond 3-4 hour estimate)

---

## Future Considerations (Not in Scope)

These are explicitly **not** included in this story:

- Git repository cloning for git sources (Story 4)
- Bundle content validation (Features 3, 5)
- Bundle type semantic validation (Nova Core)
- Manifest signing/verification
- Incremental manifest updates
- Marketplace authentication
- Bundle versioning constraints (semver ranges)
- Bundle dependency resolution
- Multiple manifest format versions
- Manifest schema documentation generation

Keep the implementation simple and focused on the core functionality.

---

## Appendix: Design Rationale

### Why YAML for Manifests?

1. Human-friendly - easy to read and write
2. Supports comments - critical for documentation
3. Widely used in similar systems (Helm charts, Kubernetes, etc.)
4. Simple structure matches our needs
5. Good Python library support (PyYAML)

### Why Simple File-Based Caching?

1. No database dependency - keeps it simple
2. Easy to inspect and debug
3. XDG standard location - familiar to users
4. Simple TTL-based expiration
5. Can be cleared manually if needed
6. Sufficient for manifest size and update frequency

### Why Generic Bundle Type Field?

1. Marketplace doesn't need to understand bundle types
2. Bundles define their own type semantics (Features 3, 5)
3. Nova Core validates bundle types when installing
4. Keeps marketplace simple and extensible
5. Allows for custom/plugin bundle types

### Why Support HTTP and Local Paths?

1. HTTP: Standard for hosted marketplaces
2. Local: Development and testing
3. Git: Future support via cloning to local (Story 4)
4. Simple to implement with consistent interface
5. Covers 99% of use cases

### Why 1 Hour Cache TTL?

1. Balance between freshness and network traffic
2. Manifests don't change frequently
3. Can be overridden via refresh command
4. Can be configured if needed
5. Matches typical package manager behavior

### Why Cache Fallback on Network Errors?

1. Better user experience - keep working offline
2. Manifests are rarely critical-path updates
3. User can force refresh when needed
4. Prevents failures during network outages
5. Graceful degradation principle

This specification provides everything needed to implement Feature 2, Story 2 following the modular design philosophy and ruthless simplicity principles.
