# Feature 2, Story 4: Git-Based Bundle Distribution - Implementation Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Updated:** 2025-10-20
**Author:** AI Architecture Team (zen-architect)

## Overview

This specification defines the implementation for git-based bundle distribution (Feature 2, Story 4, P0 priority). It follows the "bricks and studs" modular design philosophy - each module is a self-contained brick with clear contracts (studs) that can be independently generated and regenerated.

This story implements the TRANSPORT layer for bundle distribution - getting bundle bytes from source location to local disk. It does not understand or validate bundle contents - that's Nova Core's job.

**Story Scope:**
- Git operations (clone, pull, checkout)
- GitHub shortcuts (user/repo format)
- Local path installations (for development)
- Installation tracking (registry of installed bundles)
- Installation location management (project vs global)
- Reinstall/update bundles

**Out of Scope:**
- Bundle validation after download (Nova Core)
- Bundle activation/loading (Nova Core)
- Bundle type-specific setup (Features 3, 5)
- Dependency resolution (Story 5)
- Bundle content understanding (just transport bytes)

## Architecture Summary

**Approach:** Simple git wrapper with installation registry

**Key Decisions:**
- Use subprocess for git operations (simple, no complex library dependencies)
- Track installations in JSON registry file
- Support multiple source types (git URLs, GitHub shortcuts, local paths, marketplace bundles)
- Installation locations: `.nova/bundles/` (project) or `~/.config/nova/bundles/` (global)
- Simple registry schema with source tracking
- Clear separation: distribution = transport only, validation = Nova Core

**Source Types Supported:**
```bash
# Marketplace bundles (references git URL from manifest)
nova bundle install fintech-advisor@official

# GitHub shortcuts
nova bundle install github:nova-bundles/fintech-advisor
nova bundle install nova-bundles/fintech-advisor  # Inferred github:

# Direct git URLs
nova bundle install https://github.com/nova-bundles/fintech-advisor.git
nova bundle install git@github.com:nova-bundles/fintech-advisor.git

# Local paths (development)
nova bundle install ~/dev/my-bundle
nova bundle install /absolute/path/to/bundle
```

**Registry Schema:**
```json
{
  "bundles": [
    {
      "name": "fintech-advisor",
      "source": {
        "type": "git",
        "url": "https://github.com/nova-bundles/fintech-advisor",
        "ref": "main"
      },
      "marketplace": "official",
      "installed_at": "2025-10-19T10:30:00Z",
      "version": "1.0.0",
      "location": ".nova/bundles/fintech-advisor"
    }
  ]
}
```

## Module Structure

```
src/nova/
├── bundles/
│   ├── __init__.py          # Public API exports
│   ├── installer.py         # Bundle installation logic
│   ├── git_client.py        # Git operations wrapper
│   ├── registry.py          # Installation tracking
│   └── paths.py             # Bundle installation paths
└── cli/
    └── commands/
        └── bundle.py        # CLI bundle commands
```

---

## Module Specifications

### Module: bundles.paths

**Purpose:** Manage bundle installation paths and locations

**Location:** `src/nova/bundles/paths.py`

**Contract:**
- **Inputs:** None (uses environment and filesystem)
- **Outputs:** Path objects for bundle locations
- **Side Effects:**
  - Reads filesystem to find project root
  - May create bundle directories if needed
- **Dependencies:** pathlib, os, nova.config.paths

**Public Interface:**

```python
from pathlib import Path
from typing import Literal

def get_global_bundles_dir(create: bool = True) -> Path:
    """Get path to global bundles directory.

    Args:
        create: If True, create directory if it doesn't exist

    Returns:
        Path to ~/.config/nova/bundles/

    Side Effects:
        May create bundles directory

    Algorithm:
        1. Get global config dir from XDG_CONFIG_HOME or ~/.config
        2. Append nova/bundles
        3. Create directory if create=True
    """
    pass


def get_project_bundles_dir(create: bool = True) -> Path | None:
    """Get path to project bundles directory.

    Args:
        create: If True, create directory if it doesn't exist

    Returns:
        Path to .nova/bundles/ if in project, None otherwise

    Side Effects:
        May create bundles directory

    Algorithm:
        1. Find project root (.nova/ directory)
        2. If found: return .nova/bundles/
        3. If not found: return None
        4. Create directory if create=True
    """
    pass


def get_bundle_install_path(
    bundle_name: str,
    scope: Literal["project", "global"] = "project"
) -> Path:
    """Get installation path for a bundle.

    Args:
        bundle_name: Name of bundle to install
        scope: Installation scope (project or global)

    Returns:
        Path where bundle should be installed

    Raises:
        ValueError: If scope is project but not in a project

    Example:
        >>> path = get_bundle_install_path("fintech-advisor", "project")
        >>> # Returns: /path/to/project/.nova/bundles/fintech-advisor
    """
    pass


def discover_bundle_dirs() -> dict[str, Path]:
    """Discover all bundle directories.

    Returns:
        Dict with 'project' and 'global' keys mapping to bundle dirs
        Values may be None if not applicable

    Example:
        >>> dirs = discover_bundle_dirs()
        >>> # {'project': Path('.nova/bundles'), 'global': Path('~/.config/nova/bundles')}
    """
    pass
```

**Implementation Notes:**
- Use same XDG logic as config.paths for global directory
- Project bundles dir is always `.nova/bundles/` relative to project root
- Bundle name becomes subdirectory name (e.g., `fintech-advisor/`)
- Create parent directories as needed
- Validate bundle names (alphanumeric, hyphens, underscores only)

**Testing Requirements:**
- Test get_global_bundles_dir() with XDG_CONFIG_HOME set/unset
- Test get_global_bundles_dir() creates directory
- Test get_project_bundles_dir() in project (found)
- Test get_project_bundles_dir() outside project (None)
- Test get_bundle_install_path() for both scopes
- Test get_bundle_install_path() error when not in project
- Test discover_bundle_dirs() returns both paths

---

### Module: bundles.git_client

**Purpose:** Simple wrapper for git operations

**Location:** `src/nova/bundles/git_client.py`

**Contract:**
- **Inputs:** Git URLs, local paths, git refs
- **Outputs:** Success/failure status
- **Side Effects:**
  - Executes git commands via subprocess
  - Clones/pulls repositories
  - Modifies local filesystem
- **Dependencies:** subprocess, pathlib, shutil

**Public Interface:**

```python
from pathlib import Path
from typing import Literal

class GitError(Exception):
    """Error executing git operation."""
    pass


class GitClient:
    """Simple git client for bundle operations.

    Uses subprocess to execute git commands. Minimal wrapper around git CLI.

    Attributes:
        git_executable: Path to git executable (default: "git")

    Example:
        >>> client = GitClient()
        >>> client.clone("https://github.com/user/repo", Path("/dest"))
    """

    def __init__(self, git_executable: str = "git"):
        """Initialize git client.

        Args:
            git_executable: Path to git executable

        Raises:
            GitError: If git is not available
        """
        pass

    def is_git_available(self) -> bool:
        """Check if git is available.

        Returns:
            True if git executable exists and works

        Algorithm:
            1. Run `git --version`
            2. Return True if successful, False otherwise
        """
        pass

    def clone(
        self,
        url: str,
        destination: Path,
        ref: str | None = None,
        depth: int | None = 1
    ) -> None:
        """Clone a git repository.

        Args:
            url: Git repository URL
            destination: Local path to clone into
            ref: Git ref to checkout (branch, tag, commit)
            depth: Clone depth (1 for shallow, None for full)

        Raises:
            GitError: If clone fails

        Algorithm:
            1. Build git clone command with depth
            2. Execute clone
            3. If ref specified: checkout ref
            4. Remove .git directory (bundle doesn't need git history)

        Example:
            >>> client = GitClient()
            >>> client.clone(
            ...     "https://github.com/user/repo",
            ...     Path("/bundles/repo"),
            ...     ref="v1.0.0"
            ... )
        """
        pass

    def pull(self, repository_path: Path, ref: str | None = None) -> None:
        """Pull latest changes for a repository.

        Args:
            repository_path: Path to local git repository
            ref: Git ref to checkout/pull (if None, use current branch)

        Raises:
            GitError: If pull fails

        Algorithm:
            1. Check if path is a git repository
            2. If ref specified: checkout ref
            3. Pull latest changes

        Example:
            >>> client = GitClient()
            >>> client.pull(Path("/bundles/repo"), ref="main")
        """
        pass

    def get_current_commit(self, repository_path: Path) -> str:
        """Get current commit hash.

        Args:
            repository_path: Path to local git repository

        Returns:
            Current commit hash (short form)

        Raises:
            GitError: If not a git repository or git fails

        Example:
            >>> client = GitClient()
            >>> commit = client.get_current_commit(Path("/bundles/repo"))
            >>> print(commit)  # "a1b2c3d"
        """
        pass

    def normalize_git_url(self, url: str) -> str:
        """Normalize git URL to canonical form.

        Args:
            url: Git URL in any format

        Returns:
            Normalized git URL

        Algorithm:
            1. If starts with "github:": convert to https URL
            2. If contains "/" but no scheme: assume github shortcut
            3. If ends with ".git": keep as-is
            4. Otherwise: add .git extension

        Examples:
            >>> client = GitClient()
            >>> client.normalize_git_url("github:user/repo")
            'https://github.com/user/repo'
            >>> client.normalize_git_url("user/repo")
            'https://github.com/user/repo'
            >>> client.normalize_git_url("https://example.com/repo")
            'https://example.com/repo.git'
        """
        pass
```

**Implementation Notes:**
- Use `subprocess.run()` with capture_output=True
- Set timeout for git operations (default: 300 seconds)
- Parse git errors and provide clear messages
- Remove `.git` directory after clone (bundles don't need git history)
- Use shallow clone (depth=1) by default for efficiency
- Support both HTTPS and SSH git URLs
- GitHub shortcuts: `user/repo` → `https://github.com/user/repo`

**Error Handling:**
- Git not installed: Clear error message with installation hint
- Clone failures: Include URL and git error output
- Authentication failures: Detect and provide helpful message
- Network errors: Clear message about connectivity
- Invalid refs: Include ref name in error

**Testing Requirements:**
- Test is_git_available() when git is installed/not installed
- Test clone() with valid URL (mock subprocess)
- Test clone() with ref specified
- Test clone() with invalid URL
- Test pull() with valid repository
- Test pull() with ref
- Test get_current_commit()
- Test normalize_git_url() for various formats
- Test error handling (network, auth, invalid ref)

---

### Module: bundles.registry

**Purpose:** Track installed bundles in JSON registry

**Location:** `src/nova/bundles/registry.py`

**Contract:**
- **Inputs:** Bundle installation info
- **Outputs:** Registry data structures
- **Side Effects:** Reads/writes registry.json file
- **Dependencies:** pathlib, json, datetime, pydantic

**Public Interface:**

```python
from pathlib import Path
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class BundleSourceInfo(BaseModel):
    """Bundle source information.

    Attributes:
        type: Source type (git, local, marketplace)
        url: Source URL or path
        ref: Git ref (for git sources)
    """
    type: Literal["git", "local", "marketplace"]
    url: str
    ref: str | None = None


class BundleRegistryEntry(BaseModel):
    """Single bundle entry in registry.

    Attributes:
        name: Bundle name (unique identifier)
        source: Source information
        marketplace: Marketplace name (if installed from marketplace)
        installed_at: Installation timestamp (ISO format)
        version: Bundle version (from manifest)
        location: Local installation path

    Example:
        >>> entry = BundleRegistryEntry(
        ...     name="fintech-advisor",
        ...     source=BundleSourceInfo(
        ...         type="git",
        ...         url="https://github.com/nova-bundles/fintech-advisor"
        ...     ),
        ...     marketplace="official",
        ...     installed_at="2025-10-19T10:30:00Z",
        ...     version="1.0.0",
        ...     location=".nova/bundles/fintech-advisor"
        ... )
    """
    name: str = Field(min_length=1, max_length=100)
    source: BundleSourceInfo
    marketplace: str | None = None
    installed_at: str  # ISO format timestamp
    version: str | None = None
    location: str  # Relative or absolute path


class BundleRegistry:
    """Manage bundle installation registry.

    Tracks which bundles are installed, from where, and when.
    Uses simple JSON file for storage.

    Attributes:
        registry_path: Path to registry.json file

    Example:
        >>> registry = BundleRegistry(Path(".nova/bundles/registry.json"))
        >>> registry.add_bundle(entry)
        >>> bundles = registry.list_bundles()
    """

    def __init__(self, registry_path: Path):
        """Initialize bundle registry.

        Args:
            registry_path: Path to registry.json file
        """
        pass

    def load(self) -> list[BundleRegistryEntry]:
        """Load registry from file.

        Returns:
            List of bundle entries (empty if file doesn't exist)

        Raises:
            ValueError: If registry file is invalid

        Algorithm:
            1. If file doesn't exist: return []
            2. Read JSON file
            3. Parse as list of BundleRegistryEntry
            4. Return entries
        """
        pass

    def save(self, entries: list[BundleRegistryEntry]) -> None:
        """Save registry to file.

        Args:
            entries: List of bundle entries to save

        Side Effects:
            Creates parent directories if needed
            Writes registry.json file

        Algorithm:
            1. Create parent directories
            2. Serialize entries to JSON
            3. Write to file with formatting
        """
        pass

    def get_bundle(self, name: str) -> BundleRegistryEntry | None:
        """Get bundle entry by name.

        Args:
            name: Bundle name to find

        Returns:
            BundleRegistryEntry if found, None otherwise
        """
        pass

    def add_bundle(self, entry: BundleRegistryEntry) -> None:
        """Add or update bundle entry.

        Args:
            entry: Bundle entry to add

        Side Effects:
            Updates registry file

        Algorithm:
            1. Load current registry
            2. Remove existing entry with same name
            3. Add new entry
            4. Save registry
        """
        pass

    def remove_bundle(self, name: str) -> bool:
        """Remove bundle entry.

        Args:
            name: Bundle name to remove

        Returns:
            True if bundle was removed, False if not found

        Side Effects:
            Updates registry file
        """
        pass

    def list_bundles(
        self,
        source_type: str | None = None,
        marketplace: str | None = None
    ) -> list[BundleRegistryEntry]:
        """List installed bundles with optional filters.

        Args:
            source_type: Filter by source type (git, local, marketplace)
            marketplace: Filter by marketplace name

        Returns:
            List of bundle entries matching filters

        Example:
            >>> registry = BundleRegistry(path)
            >>> git_bundles = registry.list_bundles(source_type="git")
            >>> official_bundles = registry.list_bundles(marketplace="official")
        """
        pass

    def is_installed(self, name: str) -> bool:
        """Check if bundle is installed.

        Args:
            name: Bundle name to check

        Returns:
            True if bundle is installed, False otherwise
        """
        pass
```

**Registry File Location:**
- Project: `.nova/bundles/registry.json`
- Global: `~/.config/nova/bundles/registry.json`

**Registry Format:**
```json
{
  "bundles": [
    {
      "name": "fintech-advisor",
      "source": {
        "type": "git",
        "url": "https://github.com/nova-bundles/fintech-advisor",
        "ref": "main"
      },
      "marketplace": "official",
      "installed_at": "2025-10-19T10:30:00Z",
      "version": "1.0.0",
      "location": ".nova/bundles/fintech-advisor"
    }
  ]
}
```

**Testing Requirements:**
- Test load() with existing registry
- Test load() with non-existent registry (returns [])
- Test load() with invalid JSON
- Test save() creates file
- Test get_bundle() finds bundle
- Test get_bundle() returns None for non-existent
- Test add_bundle() adds new entry
- Test add_bundle() updates existing entry
- Test remove_bundle() removes entry
- Test remove_bundle() returns False for non-existent
- Test list_bundles() with no filters
- Test list_bundles() with source_type filter
- Test list_bundles() with marketplace filter
- Test is_installed()

---

### Module: bundles.installer

**Purpose:** Bundle installation orchestration

**Location:** `src/nova/bundles/installer.py`

**Contract:**
- **Inputs:** Bundle specifier (name@marketplace, git URL, local path)
- **Outputs:** Installation success/failure
- **Side Effects:**
  - Clones git repositories
  - Copies local directories
  - Updates registry
  - Creates bundle directories
- **Dependencies:** All other bundles modules, marketplace modules

**Public Interface:**

```python
from pathlib import Path
from typing import Literal
from nova.bundles.paths import get_bundle_install_path
from nova.bundles.registry import BundleRegistry, BundleRegistryEntry, BundleSourceInfo
from nova.bundles.git_client import GitClient, GitError
from nova.marketplace.config import get_marketplace_config
from nova.marketplace.fetcher import ManifestFetcher


class BundleInstallError(Exception):
    """Error installing bundle."""
    pass


class BundleInstaller:
    """Install bundles from various sources.

    Handles installation from:
    - Marketplace (name@marketplace)
    - Git URLs (https://, git@, github:)
    - Local paths (file paths)

    Attributes:
        git_client: GitClient for git operations
        scope: Installation scope (project or global)

    Example:
        >>> installer = BundleInstaller(scope="project")
        >>> installer.install("fintech-advisor@official")
        >>> installer.install("github:user/repo")
        >>> installer.install("~/dev/my-bundle")
    """

    def __init__(
        self,
        scope: Literal["project", "global"] = "project",
        git_client: GitClient | None = None
    ):
        """Initialize bundle installer.

        Args:
            scope: Installation scope (project or global)
            git_client: GitClient instance (creates default if None)
        """
        pass

    def install(
        self,
        bundle_spec: str,
        force: bool = False
    ) -> BundleRegistryEntry:
        """Install a bundle.

        Args:
            bundle_spec: Bundle specifier (formats below)
            force: If True, reinstall even if already installed

        Returns:
            BundleRegistryEntry for installed bundle

        Raises:
            BundleInstallError: If installation fails

        Bundle Spec Formats:
            - name@marketplace: "fintech-advisor@official"
            - github shortcut: "github:user/repo" or "user/repo"
            - git URL: "https://github.com/user/repo.git"
            - git SSH: "git@github.com:user/repo.git"
            - local path: "/path/to/bundle" or "~/dev/bundle"

        Algorithm:
            1. Parse bundle spec to determine source type
            2. If marketplace: resolve to git URL
            3. Check if already installed (skip unless force=True)
            4. Determine installation path
            5. Install bundle (git clone or local copy)
            6. Update registry
            7. Return registry entry

        Example:
            >>> installer = BundleInstaller()
            >>> entry = installer.install("fintech-advisor@official")
            >>> print(f"Installed to {entry.location}")
        """
        pass

    def uninstall(self, bundle_name: str) -> bool:
        """Uninstall a bundle.

        Args:
            bundle_name: Name of bundle to uninstall

        Returns:
            True if bundle was uninstalled, False if not found

        Side Effects:
            Removes bundle directory
            Updates registry

        Algorithm:
            1. Check if bundle is installed
            2. Get installation path from registry
            3. Remove bundle directory
            4. Remove from registry

        Example:
            >>> installer = BundleInstaller()
            >>> if installer.uninstall("fintech-advisor"):
            ...     print("Uninstalled successfully")
        """
        pass

    def update(self, bundle_name: str) -> BundleRegistryEntry:
        """Update an installed bundle.

        Args:
            bundle_name: Name of bundle to update

        Returns:
            Updated BundleRegistryEntry

        Raises:
            BundleInstallError: If bundle not installed or update fails

        Algorithm:
            1. Check if bundle is installed
            2. Get source info from registry
            3. If git source: pull latest changes
            4. If local source: error (local bundles can't be updated)
            5. Update registry with new timestamp

        Example:
            >>> installer = BundleInstaller()
            >>> entry = installer.update("fintech-advisor")
            >>> print(f"Updated to latest version")
        """
        pass

    def list_installed(self) -> list[BundleRegistryEntry]:
        """List installed bundles.

        Returns:
            List of installed bundle entries

        Example:
            >>> installer = BundleInstaller()
            >>> bundles = installer.list_installed()
            >>> for bundle in bundles:
            ...     print(f"{bundle.name}: {bundle.location}")
        """
        pass

    def _parse_bundle_spec(self, bundle_spec: str) -> dict:
        """Parse bundle specifier into source info.

        Args:
            bundle_spec: Bundle specifier string

        Returns:
            Dict with keys: type, url, marketplace, name

        Algorithm:
            1. If contains "@": marketplace format (name@marketplace)
            2. If starts with "github:" or contains "/" with no scheme: GitHub
            3. If starts with git URL scheme: git URL
            4. If looks like path (/ or ~): local path
            5. Otherwise: error

        Example:
            >>> installer = BundleInstaller()
            >>> info = installer._parse_bundle_spec("fintech-advisor@official")
            >>> # {'type': 'marketplace', 'name': 'fintech-advisor', 'marketplace': 'official'}
        """
        pass

    def _install_from_git(
        self,
        url: str,
        destination: Path,
        ref: str | None = None
    ) -> None:
        """Install bundle from git repository.

        Args:
            url: Git repository URL
            destination: Local installation path
            ref: Git ref to checkout

        Raises:
            BundleInstallError: If git clone fails
        """
        pass

    def _install_from_local(self, source_path: Path, destination: Path) -> None:
        """Install bundle from local path.

        Args:
            source_path: Source directory path
            destination: Destination installation path

        Raises:
            BundleInstallError: If copy fails

        Algorithm:
            1. Check source path exists and is directory
            2. Copy directory to destination (use shutil.copytree)
            3. Handle errors
        """
        pass

    def _install_from_marketplace(
        self,
        bundle_name: str,
        marketplace_name: str,
        destination: Path
    ) -> dict:
        """Install bundle from marketplace.

        Args:
            bundle_name: Bundle name in marketplace
            marketplace_name: Marketplace source name
            destination: Local installation path

        Returns:
            Dict with bundle metadata (version, etc.)

        Raises:
            BundleInstallError: If bundle not found or installation fails

        Algorithm:
            1. Get marketplace config
            2. Find marketplace source
            3. Fetch manifest
            4. Find bundle in manifest
            5. Extract git URL from bundle source
            6. Install from git
            7. Return bundle metadata
        """
        pass
```

**Installation Flow:**

1. **Parse Spec**: Determine source type (marketplace, git, local)
2. **Check Installed**: Skip if already installed (unless force=True)
3. **Resolve Source**:
   - Marketplace → fetch manifest → extract git URL
   - GitHub shortcut → convert to full URL
   - Git URL → use as-is
   - Local path → resolve and validate
4. **Install**:
   - Git: Clone to destination (shallow, remove .git)
   - Local: Copy directory to destination
5. **Update Registry**: Add entry with metadata
6. **Return**: Installation info

**Error Handling:**
- Bundle already installed: Skip with message (unless force)
- Marketplace not found: List available marketplaces
- Bundle not in marketplace: List available bundles
- Git clone failure: Include git error message
- Local path not found: Check path and suggest corrections
- Disk space errors: Clear message about space needed
- Permission errors: Explain which directory needs permissions

**Testing Requirements:**
- Test install() with marketplace bundle
- Test install() with GitHub shortcut
- Test install() with git URL
- Test install() with local path
- Test install() with force=True (reinstall)
- Test install() error when already installed
- Test uninstall() removes bundle and registry entry
- Test update() pulls latest changes
- Test update() error for non-git sources
- Test list_installed() returns all bundles
- Test _parse_bundle_spec() for all formats
- Test _install_from_git() (mock GitClient)
- Test _install_from_local() (mock filesystem)
- Test _install_from_marketplace() (mock MarketplaceFetcher)
- Test error handling for all failure modes

---

### Module: cli.commands.bundle

**Purpose:** CLI commands for bundle management

**Location:** `src/nova/cli/commands/bundle.py`

**Contract:**
- **Inputs:** Command-line arguments
- **Outputs:** Terminal output, installed bundles
- **Side Effects:**
  - Installs/uninstalls bundles
  - Updates registry
  - Displays formatted output
- **Dependencies:** typer, rich, bundles modules

**Public Interface:**

```python
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from nova.bundles.installer import BundleInstaller, BundleInstallError

app = typer.Typer(help="Manage Nova bundles")
console = Console()


@app.command("install")
def bundle_install(
    bundle_spec: str = typer.Argument(..., help="Bundle to install (formats: name@marketplace, github:user/repo, git-url, /local/path)"),
    scope: str = typer.Option("project", "--scope", help="Installation scope (project|global)"),
    force: bool = typer.Option(False, "--force", "-f", help="Reinstall if already installed"),
) -> None:
    """Install a bundle.

    Installs bundles from various sources:
    - Marketplace: fintech-advisor@official
    - GitHub: github:user/repo or user/repo
    - Git URL: https://github.com/user/repo.git
    - Local: /path/to/bundle or ~/dev/bundle

    Examples:
        nova bundle install fintech-advisor@official
        nova bundle install github:nova-bundles/tax-helper
        nova bundle install user/repo  # Assumes github:
        nova bundle install https://git.example.com/bundle.git
        nova bundle install ~/dev/my-bundle
        nova bundle install fintech-advisor@official --scope global
        nova bundle install user/repo --force  # Reinstall
    """
    # Validate scope
    if scope not in ["project", "global"]:
        console.print(f"[red]Error: Invalid scope '{scope}'. Must be 'project' or 'global'[/red]")
        raise typer.Exit(1)

    installer = BundleInstaller(scope=scope)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description=f"Installing {bundle_spec}...", total=None)

            entry = installer.install(bundle_spec, force=force)

        # Success message
        console.print(f"[green]✓[/green] Installed '{entry.name}'")
        console.print(f"  Location: {entry.location}")
        if entry.version:
            console.print(f"  Version: {entry.version}")
        if entry.marketplace:
            console.print(f"  From: {entry.marketplace} marketplace")

    except BundleInstallError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("uninstall")
def bundle_uninstall(
    bundle_name: str = typer.Argument(..., help="Bundle name to uninstall"),
    scope: str = typer.Option("project", "--scope", help="Installation scope (project|global)"),
) -> None:
    """Uninstall a bundle.

    Removes bundle directory and registry entry.

    Examples:
        nova bundle uninstall fintech-advisor
        nova bundle uninstall tax-helper --scope global
    """
    if scope not in ["project", "global"]:
        console.print(f"[red]Error: Invalid scope '{scope}'. Must be 'project' or 'global'[/red]")
        raise typer.Exit(1)

    installer = BundleInstaller(scope=scope)

    if installer.uninstall(bundle_name):
        console.print(f"[green]✓[/green] Uninstalled '{bundle_name}'")
    else:
        console.print(f"[yellow]Bundle '{bundle_name}' not found in {scope} scope[/yellow]")
        raise typer.Exit(1)


@app.command("update")
def bundle_update(
    bundle_name: str = typer.Argument(..., help="Bundle name to update"),
    scope: str = typer.Option("project", "--scope", help="Installation scope (project|global)"),
) -> None:
    """Update an installed bundle.

    Pulls latest changes for git-based bundles.
    Local bundles cannot be updated.

    Examples:
        nova bundle update fintech-advisor
        nova bundle update tax-helper --scope global
    """
    if scope not in ["project", "global"]:
        console.print(f"[red]Error: Invalid scope '{scope}'. Must be 'project' or 'global'[/red]")
        raise typer.Exit(1)

    installer = BundleInstaller(scope=scope)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description=f"Updating {bundle_name}...", total=None)

            entry = installer.update(bundle_name)

        console.print(f"[green]✓[/green] Updated '{entry.name}'")
        console.print(f"  Location: {entry.location}")

    except BundleInstallError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def bundle_list(
    scope: str = typer.Option("all", "--scope", help="Scope to list (project|global|all)"),
    installed: bool = typer.Option(True, "--installed", help="Show only installed bundles"),
) -> None:
    """List installed bundles.

    Shows bundles installed in project and/or global scope.

    Examples:
        nova bundle list                    # All installed bundles
        nova bundle list --scope project    # Project bundles only
        nova bundle list --scope global     # Global bundles only
    """
    if scope not in ["project", "global", "all"]:
        console.print(f"[red]Error: Invalid scope '{scope}'. Must be 'project', 'global', or 'all'[/red]")
        raise typer.Exit(1)

    # Collect bundles from requested scopes
    bundles = []

    if scope in ["project", "all"]:
        try:
            installer = BundleInstaller(scope="project")
            project_bundles = installer.list_installed()
            bundles.extend([(b, "project") for b in project_bundles])
        except ValueError:
            # Not in a project
            if scope == "project":
                console.print("[yellow]Not in a Nova project[/yellow]")
                raise typer.Exit(1)

    if scope in ["global", "all"]:
        installer = BundleInstaller(scope="global")
        global_bundles = installer.list_installed()
        bundles.extend([(b, "global") for b in global_bundles])

    if not bundles:
        console.print("[yellow]No bundles installed[/yellow]")
        console.print("\nTip: Install a bundle:")
        console.print("  nova bundle install <bundle-spec>")
        return

    # Display bundles in table
    table = Table(title="Installed Bundles")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Version", style="yellow")
    table.add_column("Source", style="green")
    table.add_column("Scope", style="blue")
    table.add_column("Location", style="white")

    for bundle, bundle_scope in bundles:
        source_display = bundle.source.type
        if bundle.marketplace:
            source_display = f"{bundle.marketplace} ({bundle.source.type})"

        table.add_row(
            bundle.name,
            bundle.version or "unknown",
            source_display,
            bundle_scope,
            bundle.location
        )

    console.print(table)
    console.print(f"\nTotal bundles: {len(bundles)}")
```

**CLI Commands:**

1. **`nova bundle install <spec> [--scope] [--force]`**
   - Install bundle from various sources
   - Scope: project (default) or global
   - Force: Reinstall if already installed
   - Progress indicator during installation

2. **`nova bundle uninstall <name> [--scope]`**
   - Remove bundle and registry entry
   - Scope: project (default) or global

3. **`nova bundle update <name> [--scope]`**
   - Update git-based bundle to latest
   - Error for local bundles (can't update)
   - Progress indicator during update

4. **`nova bundle list [--scope]`**
   - Show installed bundles
   - Scope: all (default), project, or global
   - Displays in formatted table

**CLI Output Examples:**

```bash
# Install from marketplace
$ nova bundle install fintech-advisor@official
⠋ Installing fintech-advisor@official...
✓ Installed 'fintech-advisor'
  Location: .nova/bundles/fintech-advisor
  Version: 1.0.0
  From: official marketplace

# Install from GitHub
$ nova bundle install github:user/repo
⠋ Installing github:user/repo...
✓ Installed 'repo'
  Location: .nova/bundles/repo

# List bundles
$ nova bundle list
Installed Bundles
┌─────────────────┬─────────┬────────────────┬─────────┬──────────────────────────┐
│ Name            │ Version │ Source         │ Scope   │ Location                 │
├─────────────────┼─────────┼────────────────┼─────────┼──────────────────────────┤
│ fintech-advisor │ 1.0.0   │ official (git) │ project │ .nova/bundles/fintech... │
│ tax-helper      │ 2.1.0   │ official (git) │ project │ .nova/bundles/tax-helper │
└─────────────────┴─────────┴────────────────┴─────────┴──────────────────────────┘

Total bundles: 2

# Update bundle
$ nova bundle update fintech-advisor
⠋ Updating fintech-advisor...
✓ Updated 'fintech-advisor'
  Location: .nova/bundles/fintech-advisor

# Uninstall bundle
$ nova bundle uninstall tax-helper
✓ Uninstalled 'tax-helper'
```

**Error Messages:**

```
❌ Error: Bundle 'fintech-advisor' already installed
   Use --force to reinstall

❌ Error: Marketplace 'unknown' not found
   Configured marketplaces:
     • official
     • company

❌ Error: Bundle 'unknown-bundle' not found in marketplace 'official'
   Available bundles:
     • fintech-advisor
     • tax-helper

❌ Error: Git is not installed
   Install git to use git-based bundles
   See: https://git-scm.com/downloads

❌ Error: Failed to clone repository
   URL: https://github.com/user/invalid-repo
   Git error: Repository not found

❌ Error: Local path not found
   Path: ~/dev/my-bundle
   Check that the path exists and is a directory

❌ Error: Cannot update local bundle 'my-bundle'
   Local bundles cannot be updated automatically
   Reinstall with: nova bundle install <path> --force
```

**Testing Requirements:**
- Test install command with all source types
- Test install with --scope global
- Test install with --force
- Test install error when already installed
- Test uninstall command
- Test uninstall error when not found
- Test update command
- Test update error for local bundles
- Test list command with different scopes
- Test list when no bundles installed
- Test CLI output formatting
- Test error message clarity
- Mock BundleInstaller for testing

---

## Example Registry Files

### Project Registry (`.nova/bundles/registry.json`)

```json
{
  "bundles": [
    {
      "name": "fintech-advisor",
      "source": {
        "type": "git",
        "url": "https://github.com/nova-bundles/fintech-advisor",
        "ref": "main"
      },
      "marketplace": "official",
      "installed_at": "2025-10-19T10:30:00Z",
      "version": "1.0.0",
      "location": ".nova/bundles/fintech-advisor"
    },
    {
      "name": "custom-tools",
      "source": {
        "type": "local",
        "url": "/Users/dev/nova-bundles/custom-tools",
        "ref": null
      },
      "marketplace": null,
      "installed_at": "2025-10-19T11:15:00Z",
      "version": null,
      "location": ".nova/bundles/custom-tools"
    }
  ]
}
```

### Global Registry (`~/.config/nova/bundles/registry.json`)

```json
{
  "bundles": [
    {
      "name": "tax-helper",
      "source": {
        "type": "git",
        "url": "https://github.com/nova-bundles/tax-helper",
        "ref": "v2.1.0"
      },
      "marketplace": "official",
      "installed_at": "2025-10-18T14:20:00Z",
      "version": "2.1.0",
      "location": "/Users/user/.config/nova/bundles/tax-helper"
    }
  ]
}
```

---

## Installation Flow Diagrams

### Marketplace Bundle Installation

```
User: nova bundle install fintech-advisor@official
  ↓
Parse spec → type=marketplace, name=fintech-advisor, marketplace=official
  ↓
Check if installed → Not installed, proceed
  ↓
Get marketplace config → Find "official" source
  ↓
Fetch manifest → Parse YAML
  ↓
Find bundle in manifest → Get git URL
  ↓
Clone git repository → .nova/bundles/fintech-advisor
  ↓
Read bundle manifest (if exists) → Extract version
  ↓
Update registry → Add entry
  ↓
Success: Installed 'fintech-advisor' v1.0.0
```

### GitHub Bundle Installation

```
User: nova bundle install github:user/repo
  ↓
Parse spec → type=git, url=github:user/repo
  ↓
Normalize URL → https://github.com/user/repo
  ↓
Check if installed → Not installed, proceed
  ↓
Clone git repository → .nova/bundles/repo
  ↓
Update registry → Add entry
  ↓
Success: Installed 'repo'
```

### Local Bundle Installation

```
User: nova bundle install ~/dev/my-bundle
  ↓
Parse spec → type=local, url=~/dev/my-bundle
  ↓
Resolve path → /Users/dev/my-bundle
  ↓
Check if exists → Directory exists, proceed
  ↓
Copy directory → .nova/bundles/my-bundle
  ↓
Update registry → Add entry
  ↓
Success: Installed 'my-bundle'
```

---

## Testing Strategy

### Unit Tests

**Test each module independently:**

- `test_bundles_paths.py` - Path management
  - Test get_global_bundles_dir()
  - Test get_project_bundles_dir()
  - Test get_bundle_install_path()
  - Test discover_bundle_dirs()

- `test_bundles_git_client.py` - Git operations
  - Test is_git_available()
  - Test clone() (mock subprocess)
  - Test pull() (mock subprocess)
  - Test get_current_commit()
  - Test normalize_git_url()
  - Test error handling

- `test_bundles_registry.py` - Registry operations
  - Test load() with existing/non-existent registry
  - Test save() creates file
  - Test get_bundle()
  - Test add_bundle()
  - Test remove_bundle()
  - Test list_bundles() with filters
  - Test is_installed()

- `test_bundles_installer.py` - Installation logic
  - Test install() for all source types
  - Test uninstall()
  - Test update()
  - Test list_installed()
  - Test _parse_bundle_spec()
  - Test error handling
  - Mock GitClient, ManifestFetcher

### Integration Tests

**Test complete bundle system:**

- `test_bundle_installation.py` - End-to-end
  - Test install from marketplace (real manifest)
  - Test install from GitHub (mock git)
  - Test install from local path
  - Test update bundle
  - Test uninstall bundle
  - Test registry persistence

- `test_bundle_cli.py` - CLI commands
  - Test install command
  - Test uninstall command
  - Test update command
  - Test list command
  - Test error cases
  - Mock BundleInstaller

### Test Fixtures

```python
@pytest.fixture
def temp_bundles_dir(tmp_path):
    """Temporary bundles directory."""
    bundles_dir = tmp_path / "bundles"
    bundles_dir.mkdir()
    return bundles_dir


@pytest.fixture
def mock_git_client(monkeypatch):
    """Mock GitClient for testing."""
    class MockGitClient:
        def clone(self, url, destination, ref=None, depth=None):
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "README.md").write_text("Mock bundle")

        def pull(self, repository_path, ref=None):
            pass

        def normalize_git_url(self, url):
            if url.startswith("github:"):
                return f"https://github.com/{url[7:]}"
            return url

    return MockGitClient()


@pytest.fixture
def sample_registry():
    """Sample bundle registry for testing."""
    return [
        BundleRegistryEntry(
            name="test-bundle",
            source=BundleSourceInfo(
                type="git",
                url="https://github.com/test/bundle"
            ),
            installed_at="2025-10-19T10:00:00Z",
            version="1.0.0",
            location=".nova/bundles/test-bundle"
        )
    ]
```

---

## Success Criteria

- [ ] Git operations work (clone, pull, normalize URLs)
- [ ] GitHub shortcuts resolve correctly (user/repo → full URL)
- [ ] Local path installations work
- [ ] Marketplace bundle resolution works
- [ ] Registry tracks installations correctly
- [ ] Registry persists across operations
- [ ] Install command works for all source types
- [ ] Uninstall removes bundle and registry entry
- [ ] Update pulls latest changes (git bundles)
- [ ] List shows installed bundles correctly
- [ ] Scope parameter works (project vs global)
- [ ] Force reinstall works
- [ ] Error messages are clear and actionable
- [ ] Progress indicators show during operations
- [ ] Code follows ruthless simplicity principles
- [ ] All modules have clear, single responsibilities
- [ ] Comprehensive test coverage (unit + integration)
- [ ] Git is optional (clear error if not installed)

---

## Dependencies

**This Story Depends On:**
- Feature 1: Config Management - MUST be complete
- Feature 2, Story 1: Marketplace Configuration - MUST be complete
- Feature 2, Story 2: Marketplace Manifest System - MUST be complete
  - Uses MarketplaceConfig
  - Uses ManifestFetcher to resolve marketplace bundles
  - Uses BundleManifestEntry to get git URLs

**This Story Enables:**
- Feature 2, Story 5: Bundle dependency resolution
- Feature 3: Domain bundles (can be installed)
- Feature 5: Extension bundles (can be installed)
- Nova Core: Bundle loading and activation

**Required Packages:**
- pydantic >= 2.12.3 (already in project)
- typer >= 0.19.2 (already in project)
- rich (already in project from Story 1)

**External Dependencies:**
- git (must be installed on system)
  - Check with `git --version`
  - Provide clear error if not available

---

## Implementation Phases

### Phase 1: Paths and Git Client (Modules: paths, git_client)
**Estimated Time:** 1 hour
**Deliverables:**
- Bundle path utilities
- Git client wrapper
- Git URL normalization
- Unit tests

### Phase 2: Registry (Module: registry)
**Estimated Time:** 1 hour
**Deliverables:**
- Registry models (Pydantic)
- Registry operations (load, save, query)
- Unit tests

### Phase 3: Installer (Module: installer)
**Estimated Time:** 2 hours
**Deliverables:**
- Installation orchestration
- Source type parsing
- Marketplace resolution
- Install/uninstall/update logic
- Unit tests

### Phase 4: CLI Commands (Module: cli/commands/bundle.py)
**Estimated Time:** 1 hour
**Deliverables:**
- Install, uninstall, update, list commands
- Progress indicators
- Error handling and messages
- CLI integration tests

### Phase 5: Polish and Documentation
**Estimated Time:** 0.5 hours
**Deliverables:**
- Example registry files
- Error message improvements
- CLI help text
- Usage documentation

**Total Estimated Time:** 5.5 hours (buffer beyond 4-5 hour estimate)

---

## What Stories 1-3 Provide

### Story 1: Marketplace Configuration
- MarketplaceConfig: List of marketplace sources
- MarketplaceSource: URL and metadata for each marketplace
- CLI commands to manage marketplace sources

### Story 2: Marketplace Manifest System
- MarketplaceManifest: Catalog of bundles
- BundleManifestEntry: Bundle metadata including git URL
- ManifestFetcher: Retrieves manifests from configured sources
- Bundle metadata: name, version, description, source URL

### Story 3: Bundle Discovery (Future)
- Would provide search/discovery features
- This story (4) doesn't depend on it

**What This Story (4) Adds:**
- Actual bundle installation (bytes on disk)
- Git operations for cloning bundles
- Registry to track installations
- Support for multiple install sources
- CLI to install/uninstall/update bundles

---

## What This Enables for Story 5 and Features 3-5

### For Story 5: Dependency Resolution
- Bundle installation mechanism (install dependencies)
- Registry to check what's installed
- Update mechanism for dependency updates

### For Feature 3: Domain Bundles
- Can install domain bundles from marketplace or git
- Domain bundles can be distributed via any supported source
- Registry tracks installed domain bundles

### For Feature 5: Extension Bundles
- Can install extension bundles from marketplace or git
- Extension bundles can be distributed via any supported source
- Registry tracks installed extension bundles

### For Nova Core
- Bundles are on disk and ready to load
- Registry provides metadata for validation
- Clear separation: distribution gets bytes, Core validates and loads

---

## Future Considerations (Not in Scope)

These are explicitly **not** included in this story:

- Bundle dependency resolution (Story 5)
- Bundle validation after download (Nova Core)
- Bundle activation/loading (Nova Core)
- Bundle versioning constraints (Story 5)
- Bundle signing/verification
- Incremental bundle updates
- Bundle caching strategies
- Bundle publishing workflow
- Bundle templates/scaffolding
- Bundle testing framework

Keep the implementation focused on TRANSPORT - getting bundle bytes from source to destination. Nova Core handles everything after that.

---

## Appendix: Design Rationale

### Why Simple Git Wrapper Over GitPython?

1. Minimal dependencies - git is already required
2. Simple subprocess calls are easy to debug
3. No complex library API to learn
4. Works with any git version
5. Clear error messages from git itself
6. Can add GitPython later if needed

### Why Remove .git Directory After Clone?

1. Bundles don't need git history
2. Saves disk space significantly
3. Users can't accidentally commit to bundle
4. Simpler bundle structure
5. Can re-clone to update

### Why Support Multiple Source Types?

1. **Marketplace**: Primary use case, discoverable bundles
2. **Git URLs**: Direct installation for custom/private bundles
3. **GitHub shortcuts**: Convenience for common case
4. **Local paths**: Essential for bundle development

### Why Separate Project and Global Scopes?

1. **Project**: Team-shared bundles, version controlled
2. **Global**: Personal bundles, available everywhere
3. Matches pattern from other tools (npm, pip, etc.)
4. Clear separation of concerns
5. Flexibility for different use cases

### Why Simple JSON Registry?

1. Human-readable and debuggable
2. No database dependency
3. Easy to version control (project registry)
4. Sufficient for expected bundle counts
5. Can migrate to SQLite later if needed

### Why Track Installation Source?

1. Know where bundle came from
2. Enable updates for git bundles
3. Support uninstall/reinstall
4. Debugging and troubleshooting
5. Marketplace attribution

### Why Shallow Clones (depth=1)?

1. Faster downloads
2. Less disk space
3. Bundles don't need history
4. Can always do full clone if needed
5. Matches bundle use case

This specification provides everything needed to implement Feature 2, Story 4 following the modular design philosophy and ruthless simplicity principles.
