# Feature 2, Story 5: Bundle Versioning - Implementation Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Updated:** 2025-10-20
**Author:** AI Architecture Team (zen-architect)

## Overview

This specification defines the implementation for bundle versioning (Feature 2, Story 5, P1 priority). It follows the "bricks and studs" modular design philosophy - each module is a self-contained brick with clear contracts (studs) that can be independently generated and regenerated.

This story implements VERSION LABELING for bundles - allowing bundles to be tagged, requested by version, and tracked with version information. It does NOT implement semantic version understanding, compatibility checking, or migration - those are bundle author responsibilities.

**Story Scope:**
- Version format specification (semver recommended)
- Git tag-based versioning (tags are source of truth)
- Install specific versions
- List available versions for a bundle
- Update to latest version or specific version
- Version tracking in registry
- Manifest version support

**Out of Scope:**
- Version compatibility checking (Nova Core responsibility)
- Bundle migration between versions (bundle authors)
- Breaking change detection (bundle authors)
- Dependency version resolution (future feature)
- Complex version constraints (>, <, ~, ^)
- Semantic understanding of version changes (just labels)

**Key Philosophy:**
- Versioning is LABELING ONLY
- Git tags are the source of truth
- No semantic understanding of version changes
- Bundle authors control versions (via git tags)
- Infrastructure just fetches requested tag/branch
- Semver recommended but not enforced initially
- Simple version comparison (string-based initially)

## Architecture Summary

**Approach:** Git tags for versions, simple version parsing and comparison

**Key Decisions:**
- Use git tags as version source (e.g., `v1.2.0`, `1.2.0`)
- Support git branches for pre-releases (e.g., `main`, `develop`)
- Default to `main` branch if no version specified
- Semver format recommended but not enforced
- Support `latest` as alias for newest tag
- Store version in registry for tracking
- Simple string-based version comparison initially
- Version information flows from git → registry → CLI display

**Version Resolution Strategy:**
```
User Request → Parse version spec → Resolve to git ref → Install
```

**Supported Version Formats:**
```bash
# Specific version (git tag)
nova bundle install fintech-advisor@official --version 1.2.0
nova bundle install fintech-advisor@official@1.2.0

# Latest version (newest tag)
nova bundle install fintech-advisor@official@latest
nova bundle install fintech-advisor@official  # Defaults to latest

# Specific branch
nova bundle install fintech-advisor@official@main
nova bundle install fintech-advisor@official@develop
```

## Module Structure

```
src/nova/
├── bundles/
│   ├── __init__.py          # Public API exports
│   ├── versioning.py        # Version parsing and comparison (NEW)
│   ├── installer.py         # Updated to support versions
│   ├── git_client.py        # Updated to support version listing
│   ├── registry.py          # Already tracks version (from Story 4)
│   └── paths.py             # No changes needed
└── cli/
    └── commands/
        └── bundle.py        # Updated with version commands
```

---

## Module Specifications

### Module: bundles.versioning

**Purpose:** Parse and compare bundle versions

**Location:** `src/nova/bundles/versioning.py`

**Contract:**
- **Inputs:** Version strings, git tags
- **Outputs:** Parsed version objects, comparison results
- **Side Effects:** None (pure functions)
- **Dependencies:** re, typing

**Public Interface:**

```python
from dataclasses import dataclass
from typing import Literal
import re


@dataclass(frozen=True)
class Version:
    """Represents a bundle version.

    Supports semver-like versions but doesn't enforce strict semver.
    Versions are treated as labels for git refs.

    Attributes:
        original: Original version string as provided
        normalized: Normalized version string (for comparison)
        major: Major version number (if parseable)
        minor: Minor version number (if parseable)
        patch: Patch version number (if parseable)
        prerelease: Pre-release identifier (if any)
        is_semver: Whether this follows semver format

    Example:
        >>> v = Version.parse("1.2.3")
        >>> v.major, v.minor, v.patch
        (1, 2, 3)

        >>> v = Version.parse("v2.0.0-beta.1")
        >>> v.major, v.prerelease
        (2, "beta.1")

        >>> v = Version.parse("main")  # Branch name
        >>> v.is_semver
        False
    """
    original: str
    normalized: str
    major: int | None = None
    minor: int | None = None
    patch: int | None = None
    prerelease: str | None = None
    is_semver: bool = False

    @staticmethod
    def parse(version_str: str) -> "Version":
        """Parse a version string.

        Args:
            version_str: Version string to parse (e.g., "1.2.3", "v2.0.0", "main")

        Returns:
            Version object

        Algorithm:
            1. Strip whitespace and 'v' prefix
            2. Try to parse as semver (major.minor.patch)
            3. If successful: extract components and mark as semver
            4. If not: treat as branch name or custom version
            5. Create normalized form for comparison

        Examples:
            >>> Version.parse("1.2.3")
            Version(original="1.2.3", normalized="1.2.3", major=1, minor=2, patch=3)

            >>> Version.parse("v2.0.0-beta")
            Version(original="v2.0.0-beta", normalized="2.0.0-beta", major=2, ...)

            >>> Version.parse("main")
            Version(original="main", normalized="main", is_semver=False)
        """
        pass

    def to_git_ref(self) -> str:
        """Convert version to git ref.

        Returns:
            Git ref string (tag or branch name)

        Algorithm:
            - If is_semver: try both "v{version}" and "{version}" tags
            - Otherwise: use as branch name

        Examples:
            >>> Version.parse("1.2.3").to_git_ref()
            "v1.2.3"  # or "1.2.3" depending on repo convention

            >>> Version.parse("main").to_git_ref()
            "main"
        """
        pass

    def __str__(self) -> str:
        """String representation."""
        return self.normalized

    def __lt__(self, other: "Version") -> bool:
        """Less than comparison.

        Algorithm (simple version):
            1. If both are semver: compare major.minor.patch
            2. If one is semver, one isn't: semver is "greater"
            3. If neither is semver: string comparison
            4. Pre-release versions are "less than" release versions

        Note: This is a simple implementation. Proper semver comparison
        would be more complex but is not needed for MVP.
        """
        pass

    def __eq__(self, other: object) -> bool:
        """Equality comparison."""
        if not isinstance(other, Version):
            return False
        return self.normalized == other.normalized

    def __le__(self, other: "Version") -> bool:
        """Less than or equal comparison."""
        return self < other or self == other

    def __gt__(self, other: "Version") -> bool:
        """Greater than comparison."""
        return not self <= other

    def __ge__(self, other: "Version") -> bool:
        """Greater than or equal comparison."""
        return not self < other


class VersionError(Exception):
    """Error parsing or comparing versions."""
    pass


def parse_version_spec(spec: str) -> tuple[str, str | None]:
    """Parse a bundle specification with optional version.

    Args:
        spec: Bundle spec (e.g., "name@marketplace", "name@marketplace@1.2.0")

    Returns:
        Tuple of (bundle_spec, version) where version may be None

    Algorithm:
        1. Split on '@' delimiter
        2. If 2 parts: (name@marketplace, None)
        3. If 3 parts: (name@marketplace, version)
        4. Otherwise: error

    Examples:
        >>> parse_version_spec("fintech-advisor@official")
        ("fintech-advisor@official", None)

        >>> parse_version_spec("fintech-advisor@official@1.2.0")
        ("fintech-advisor@official", "1.2.0")

        >>> parse_version_spec("fintech-advisor@official@latest")
        ("fintech-advisor@official", "latest")
    """
    pass


def is_valid_version(version_str: str) -> bool:
    """Check if a version string is valid.

    Args:
        version_str: Version string to validate

    Returns:
        True if valid, False otherwise

    Notes:
        - Accepts semver format (1.2.3, v1.2.3, 1.2.3-beta)
        - Accepts branch names (main, develop, feature/xyz)
        - Accepts "latest" as special version
    """
    pass


def compare_versions(v1: str, v2: str) -> Literal[-1, 0, 1]:
    """Compare two version strings.

    Args:
        v1: First version string
        v2: Second version string

    Returns:
        -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2

    Example:
        >>> compare_versions("1.2.3", "1.2.4")
        -1

        >>> compare_versions("2.0.0", "1.9.9")
        1

        >>> compare_versions("1.0.0", "1.0.0")
        0
    """
    pass


def sort_versions(versions: list[str], descending: bool = True) -> list[str]:
    """Sort version strings.

    Args:
        versions: List of version strings to sort
        descending: If True, sort newest first (default)

    Returns:
        Sorted list of version strings

    Algorithm:
        1. Parse each version string
        2. Sort using Version comparison
        3. Return sorted list (descending or ascending)

    Example:
        >>> sort_versions(["1.0.0", "2.0.0", "1.5.0"])
        ["2.0.0", "1.5.0", "1.0.0"]

        >>> sort_versions(["1.0.0", "main", "2.0.0"])
        ["2.0.0", "1.0.0", "main"]  # Semver first, then others
    """
    pass


def get_latest_version(versions: list[str]) -> str | None:
    """Get the latest version from a list.

    Args:
        versions: List of version strings

    Returns:
        Latest version string, or None if list is empty

    Algorithm:
        1. Filter to semver versions only
        2. Sort in descending order
        3. Return first (newest) version

    Example:
        >>> get_latest_version(["1.0.0", "2.0.0", "1.5.0"])
        "2.0.0"

        >>> get_latest_version(["main", "develop"])  # No semver versions
        None
    """
    pass
```

**Implementation Notes:**
- Use regex for semver parsing: `r'^v?(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?$'`
- Support both `v1.2.3` and `1.2.3` formats (normalize to without `v`)
- Pre-release versions: `1.2.3-beta`, `1.2.3-alpha.1`, etc.
- Branch names: anything that doesn't parse as semver
- "latest" is a special keyword, not a version
- Simple comparison: major → minor → patch → prerelease
- Non-semver versions sort after semver versions (string comparison)

**Testing Requirements:**
- Test Version.parse() with various formats
  - Semver: "1.2.3", "v1.2.3"
  - Pre-release: "1.2.3-beta", "2.0.0-rc.1"
  - Branch names: "main", "develop", "feature/xyz"
  - Invalid: "", "abc", "1.2"
- Test to_git_ref() conversion
- Test version comparison operators
  - Compare semver versions
  - Compare pre-release vs release
  - Compare semver vs branch name
  - Compare branch names (string comparison)
- Test parse_version_spec()
- Test is_valid_version()
- Test compare_versions()
- Test sort_versions()
- Test get_latest_version()

---

### Module: bundles.git_client (Updated)

**Purpose:** Extended to support version listing from git tags

**Location:** `src/nova/bundles/git_client.py`

**Contract:** Same as Story 4, plus version listing functionality

**New Public Interface Methods:**

```python
class GitClient:
    # ... existing methods from Story 4 ...

    def list_tags(self, repository_url: str) -> list[str]:
        """List all tags in a git repository.

        Args:
            repository_url: Git repository URL

        Returns:
            List of tag names (sorted by creation date, newest first)

        Raises:
            GitError: If listing tags fails

        Algorithm:
            1. Run `git ls-remote --tags {repository_url}`
            2. Parse output to extract tag names
            3. Filter out tag references (^{})
            4. Return sorted list

        Example:
            >>> client = GitClient()
            >>> tags = client.list_tags("https://github.com/user/repo")
            >>> print(tags)
            ["v2.0.0", "v1.5.0", "v1.0.0"]
        """
        pass

    def get_latest_tag(self, repository_url: str) -> str | None:
        """Get the latest tag from a repository.

        Args:
            repository_url: Git repository URL

        Returns:
            Latest tag name, or None if no tags

        Algorithm:
            1. List all tags
            2. Filter to semver tags only
            3. Sort and return latest
            4. Return None if no semver tags found

        Example:
            >>> client = GitClient()
            >>> latest = client.get_latest_tag("https://github.com/user/repo")
            >>> print(latest)
            "v2.0.0"
        """
        pass

    def tag_exists(self, repository_url: str, tag: str) -> bool:
        """Check if a tag exists in a repository.

        Args:
            repository_url: Git repository URL
            tag: Tag name to check

        Returns:
            True if tag exists, False otherwise

        Algorithm:
            1. Run `git ls-remote --tags {repository_url} {tag}`
            2. Check if output contains the tag
            3. Return True/False

        Example:
            >>> client = GitClient()
            >>> exists = client.tag_exists("https://github.com/user/repo", "v1.0.0")
            >>> print(exists)
            True
        """
        pass
```

**Implementation Notes:**
- Use `git ls-remote` for remote tag listing (no clone needed)
- Parse output format: `<hash>\trefs/tags/<tag>`
- Filter out annotated tag references (`^{}`)
- Cache tag lists for performance (optional, simple dict cache)
- Timeout for remote operations (default: 30 seconds)

**Testing Requirements:**
- Test list_tags() with mock subprocess output
- Test get_latest_tag() with various tag formats
- Test tag_exists() for existing and non-existing tags
- Test error handling (network, invalid URL)
- Test tag filtering (remove ^{} references)

---

### Module: bundles.installer (Updated)

**Purpose:** Extended to support version-aware installation

**Location:** `src/nova/bundles/installer.py`

**Contract:** Same as Story 4, plus version support

**Updated Public Interface Methods:**

```python
class BundleInstaller:
    # ... existing methods from Story 4 ...

    def install(
        self,
        bundle_spec: str,
        version: str | None = None,  # NEW PARAMETER
        force: bool = False
    ) -> BundleRegistryEntry:
        """Install a bundle with optional version.

        Args:
            bundle_spec: Bundle specifier (formats from Story 4)
            version: Version to install (git tag, branch, or "latest")
            force: If True, reinstall even if already installed

        Returns:
            BundleRegistryEntry for installed bundle

        Raises:
            BundleInstallError: If installation fails

        Version Formats:
            - Specific tag: "1.2.0", "v1.2.0"
            - Latest tag: "latest" (finds newest semver tag)
            - Branch: "main", "develop"
            - None: defaults to "latest" for marketplace, "main" for git

        Algorithm:
            1. Parse bundle spec (may include version: name@marketplace@1.2.0)
            2. If version in spec: extract and use that
            3. Otherwise: use version parameter (or default)
            4. Resolve "latest" to actual tag if needed
            5. Proceed with installation using resolved version as git ref
            6. Store version in registry

        Example:
            >>> installer = BundleInstaller()
            >>> entry = installer.install("fintech-advisor@official", version="1.2.0")
            >>> print(f"Installed {entry.name} v{entry.version}")
        """
        pass

    def update(
        self,
        bundle_name: str,
        to_version: str | None = None  # NEW PARAMETER
    ) -> BundleRegistryEntry:
        """Update an installed bundle to a specific version or latest.

        Args:
            bundle_name: Name of bundle to update
            to_version: Version to update to (None = latest)

        Returns:
            Updated BundleRegistryEntry

        Raises:
            BundleInstallError: If bundle not installed or update fails

        Algorithm:
            1. Check if bundle is installed
            2. Get source info from registry
            3. If to_version is None: resolve to "latest"
            4. If git source: checkout new version
            5. If local source: error (local bundles can't be updated)
            6. Update registry with new version and timestamp

        Example:
            >>> installer = BundleInstaller()
            >>> entry = installer.update("fintech-advisor", to_version="1.3.0")
            >>> print(f"Updated to {entry.version}")

            >>> entry = installer.update("fintech-advisor")  # Update to latest
            >>> print(f"Updated to latest: {entry.version}")
        """
        pass

    def list_available_versions(self, bundle_spec: str) -> list[str]:
        """List available versions for a bundle.

        Args:
            bundle_spec: Bundle specifier (name@marketplace or git URL)

        Returns:
            List of available versions (tags), sorted newest first

        Raises:
            BundleInstallError: If bundle not found or listing fails

        Algorithm:
            1. Parse bundle spec to get git URL
            2. If marketplace: resolve to git URL
            3. List git tags for repository
            4. Parse and sort versions
            5. Return sorted list (newest first)

        Example:
            >>> installer = BundleInstaller()
            >>> versions = installer.list_available_versions("fintech-advisor@official")
            >>> print(versions)
            ["2.0.0", "1.5.0", "1.0.0"]
        """
        pass

    def _resolve_version(
        self,
        bundle_spec: str,
        version: str | None
    ) -> tuple[str, str]:
        """Resolve version to git ref.

        Args:
            bundle_spec: Bundle specifier
            version: Version string (or None)

        Returns:
            Tuple of (git_ref, resolved_version_label)

        Algorithm:
            1. If version is None: default to "latest"
            2. If version is "latest": find newest tag
            3. If version is semver: convert to git tag (try v{version} and {version})
            4. If version is branch: use as-is
            5. Verify tag/branch exists
            6. Return (git_ref, version_label)

        Example:
            >>> installer = BundleInstaller()
            >>> ref, label = installer._resolve_version("name@marketplace", "latest")
            >>> print(ref, label)
            ("v2.0.0", "2.0.0")

            >>> ref, label = installer._resolve_version("name@marketplace", "1.5.0")
            >>> print(ref, label)
            ("v1.5.0", "1.5.0")
        """
        pass
```

**Version Resolution Logic:**

```
Input Version → Resolution → Git Ref

None           → "latest"   → newest semver tag
"latest"       → find newest → newest semver tag
"1.2.0"        → check tag   → "v1.2.0" or "1.2.0"
"main"         → branch      → "main"
"develop"      → branch      → "develop"
```

**Error Handling:**
- Version not found: List available versions
- "latest" but no tags: Suggest using branch name instead
- Invalid version format: Show expected formats
- Tag doesn't exist: List similar tags

**Testing Requirements:**
- Test install() with explicit version
- Test install() with "latest" version
- Test install() with version in spec (name@marketplace@1.2.0)
- Test install() default version (None)
- Test update() to specific version
- Test update() to latest (None)
- Test list_available_versions()
- Test _resolve_version() for all cases
- Test error handling for version not found
- Mock GitClient for version operations

---

### Module: cli.commands.bundle (Updated)

**Purpose:** Extended CLI commands with version support

**Location:** `src/nova/cli/commands/bundle.py`

**Contract:** Same as Story 4, plus version commands

**Updated Command: `install`**

```python
@app.command("install")
def bundle_install(
    bundle_spec: str = typer.Argument(..., help="Bundle to install (formats: name@marketplace, name@marketplace@version, github:user/repo, git-url, /local/path)"),
    scope: str = typer.Option("project", "--scope", help="Installation scope (project|global)"),
    version: str = typer.Option(None, "--version", help="Version to install (tag, branch, or 'latest')"),
    force: bool = typer.Option(False, "--force", "-f", help="Reinstall if already installed"),
) -> None:
    """Install a bundle with optional version.

    Version can be specified in three ways:
    1. In bundle spec: fintech-advisor@official@1.2.0
    2. Via --version flag: --version 1.2.0
    3. Default: latest for marketplace, main for git

    Examples:
        # Install latest version from marketplace
        nova bundle install fintech-advisor@official

        # Install specific version (in spec)
        nova bundle install fintech-advisor@official@1.2.0

        # Install specific version (with flag)
        nova bundle install fintech-advisor@official --version 1.2.0

        # Install from branch
        nova bundle install fintech-advisor@official@develop

        # Install latest version explicitly
        nova bundle install fintech-advisor@official@latest

        # Install from GitHub with version
        nova bundle install user/repo --version 2.0.0
    """
    # Validate scope
    if scope not in ["project", "global"]:
        console.print(f"[red]Error: Invalid scope '{scope}'. Must be 'project' or 'global'[/red]")
        raise typer.Exit(1)

    # Parse version from spec if present
    bundle_spec, spec_version = parse_version_spec(bundle_spec)

    # Version priority: spec > flag > default
    install_version = spec_version or version

    installer = BundleInstaller(scope=scope)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            version_display = f" (v{install_version})" if install_version else ""
            progress.add_task(
                description=f"Installing {bundle_spec}{version_display}...",
                total=None
            )

            entry = installer.install(bundle_spec, version=install_version, force=force)

        # Success message
        console.print(f"[green]✓[/green] Installed '{entry.name}'")
        if entry.version:
            console.print(f"  Version: {entry.version}")
        console.print(f"  Location: {entry.location}")
        if entry.marketplace:
            console.print(f"  From: {entry.marketplace} marketplace")

    except BundleInstallError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
```

**Updated Command: `update`**

```python
@app.command("update")
def bundle_update(
    bundle_name: str = typer.Argument(..., help="Bundle name to update"),
    scope: str = typer.Option("project", "--scope", help="Installation scope (project|global)"),
    to_version: str = typer.Option(None, "--to-version", help="Version to update to (default: latest)"),
    to_latest: bool = typer.Option(False, "--to-latest", help="Update to latest version"),
) -> None:
    """Update an installed bundle to a specific version or latest.

    By default, updates to the latest available version.
    Use --to-version to specify a particular version.

    Examples:
        # Update to latest version
        nova bundle update fintech-advisor
        nova bundle update fintech-advisor --to-latest

        # Update to specific version
        nova bundle update fintech-advisor --to-version 1.3.0

        # Update global bundle
        nova bundle update tax-helper --scope global --to-latest
    """
    if scope not in ["project", "global"]:
        console.print(f"[red]Error: Invalid scope '{scope}'. Must be 'project' or 'global'[/red]")
        raise typer.Exit(1)

    # Determine target version
    target_version = to_version
    if to_latest and to_version:
        console.print("[yellow]Warning: Both --to-latest and --to-version specified. Using --to-version.[/yellow]")
    elif to_latest:
        target_version = "latest"

    installer = BundleInstaller(scope=scope)

    try:
        # Get current version for display
        current_entry = installer.registry.get_bundle(bundle_name)
        if not current_entry:
            console.print(f"[red]Error: Bundle '{bundle_name}' not installed in {scope} scope[/red]")
            raise typer.Exit(1)

        current_version = current_entry.version or "unknown"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            version_display = f" to v{target_version}" if target_version else " to latest"
            progress.add_task(
                description=f"Updating {bundle_name}{version_display}...",
                total=None
            )

            entry = installer.update(bundle_name, to_version=target_version)

        # Success message
        if entry.version and entry.version != current_version:
            console.print(f"[green]✓[/green] Updated '{entry.name}' from {current_version} → {entry.version}")
        else:
            console.print(f"[green]✓[/green] Updated '{entry.name}' (v{entry.version})")
        console.print(f"  Location: {entry.location}")

    except BundleInstallError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
```

**New Command: `versions`**

```python
@app.command("versions")
def bundle_versions(
    bundle_spec: str = typer.Argument(..., help="Bundle to list versions for (name@marketplace or git URL)"),
    limit: int = typer.Option(20, "--limit", help="Maximum number of versions to show"),
    show_all: bool = typer.Option(False, "--all", help="Show all versions (no limit)"),
) -> None:
    """List available versions for a bundle.

    Shows available versions from git tags, sorted newest first.
    By default shows the 20 most recent versions.

    Examples:
        # List versions from marketplace
        nova bundle versions fintech-advisor@official

        # List versions from git URL
        nova bundle versions https://github.com/nova-bundles/tax-helper

        # Show all versions
        nova bundle versions fintech-advisor@official --all

        # Limit to 10 versions
        nova bundle versions fintech-advisor@official --limit 10
    """
    installer = BundleInstaller()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(
                description=f"Fetching versions for {bundle_spec}...",
                total=None
            )

            versions = installer.list_available_versions(bundle_spec)

        if not versions:
            console.print(f"[yellow]No versions found for '{bundle_spec}'[/yellow]")
            console.print("\nTip: Bundle may not have any git tags yet.")
            console.print("     Try installing from a branch (e.g., --version main)")
            return

        # Apply limit
        display_versions = versions if show_all else versions[:limit]

        # Display versions
        table = Table(title=f"Available Versions for {bundle_spec}")
        table.add_column("Version", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")

        # Check installed version
        installer_global = BundleInstaller(scope="global")
        installer_project = BundleInstaller(scope="project")

        # Extract bundle name from spec
        bundle_name = bundle_spec.split("@")[0]

        installed_project = installer_project.registry.get_bundle(bundle_name)
        installed_global = installer_global.registry.get_bundle(bundle_name)

        for version in display_versions:
            status = ""
            if installed_project and installed_project.version == version:
                status = "installed (project)"
            elif installed_global and installed_global.version == version:
                status = "installed (global)"

            table.add_row(version, status)

        console.print(table)

        # Show count
        if not show_all and len(versions) > limit:
            console.print(f"\nShowing {limit} of {len(versions)} versions")
            console.print("Use --all to show all versions")
        else:
            console.print(f"\nTotal versions: {len(versions)}")

    except BundleInstallError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
```

**Updated Command: `list` (show versions)**

```python
@app.command("list")
def bundle_list(
    scope: str = typer.Option("all", "--scope", help="Scope to list (project|global|all)"),
    installed: bool = typer.Option(True, "--installed", help="Show only installed bundles"),
    show_versions: bool = typer.Option(True, "--show-versions", help="Show version column"),  # NEW OPTION
) -> None:
    """List installed bundles with version information.

    Shows bundles installed in project and/or global scope,
    including version information by default.

    Examples:
        nova bundle list                          # All installed bundles with versions
        nova bundle list --scope project          # Project bundles only
        nova bundle list --no-show-versions       # Hide version column
    """
    # ... existing scope validation and bundle collection logic ...

    # Display bundles in table
    table = Table(title="Installed Bundles")
    table.add_column("Name", style="cyan", no_wrap=True)

    if show_versions:
        table.add_column("Version", style="yellow")

    table.add_column("Source", style="green")
    table.add_column("Scope", style="blue")
    table.add_column("Location", style="white")

    for bundle, bundle_scope in bundles:
        source_display = bundle.source.type
        if bundle.marketplace:
            source_display = f"{bundle.marketplace} ({bundle.source.type})"

        row = [bundle.name]

        if show_versions:
            row.append(bundle.version or "unknown")

        row.extend([source_display, bundle_scope, bundle.location])

        table.add_row(*row)

    console.print(table)
    console.print(f"\nTotal bundles: {len(bundles)}")
```

**CLI Output Examples:**

```bash
# Install specific version
$ nova bundle install fintech-advisor@official --version 1.2.0
⠋ Installing fintech-advisor@official (v1.2.0)...
✓ Installed 'fintech-advisor'
  Version: 1.2.0
  Location: .nova/bundles/fintech-advisor
  From: official marketplace

# Install with version in spec
$ nova bundle install fintech-advisor@official@1.2.0
⠋ Installing fintech-advisor@official (v1.2.0)...
✓ Installed 'fintech-advisor'
  Version: 1.2.0
  Location: .nova/bundles/fintech-advisor
  From: official marketplace

# List available versions
$ nova bundle versions fintech-advisor@official
⠋ Fetching versions for fintech-advisor@official...

Available Versions for fintech-advisor@official
┌─────────┬─────────────────────┐
│ Version │ Status              │
├─────────┼─────────────────────┤
│ 2.1.0   │                     │
│ 2.0.0   │                     │
│ 1.5.2   │                     │
│ 1.5.1   │                     │
│ 1.5.0   │                     │
│ 1.2.0   │ installed (project) │
│ 1.1.0   │                     │
│ 1.0.0   │                     │
└─────────┴─────────────────────┘

Total versions: 8

# Update to latest
$ nova bundle update fintech-advisor --to-latest
⠋ Updating fintech-advisor to latest...
✓ Updated 'fintech-advisor' from 1.2.0 → 2.1.0
  Location: .nova/bundles/fintech-advisor

# Update to specific version
$ nova bundle update fintech-advisor --to-version 2.0.0
⠋ Updating fintech-advisor to v2.0.0...
✓ Updated 'fintech-advisor' from 1.2.0 → 2.0.0
  Location: .nova/bundles/fintech-advisor

# List bundles with versions
$ nova bundle list
Installed Bundles
┌─────────────────┬─────────┬────────────────┬─────────┬──────────────────────────┐
│ Name            │ Version │ Source         │ Scope   │ Location                 │
├─────────────────┼─────────┼────────────────┼─────────┼──────────────────────────┤
│ fintech-advisor │ 1.2.0   │ official (git) │ project │ .nova/bundles/fintech... │
│ tax-helper      │ 2.1.0   │ official (git) │ project │ .nova/bundles/tax-helper │
└─────────────────┴─────────┴────────────────┴─────────┴──────────────────────────┘

Total bundles: 2
```

**Error Messages:**

```
❌ Error: Version '1.9.0' not found for bundle 'fintech-advisor'
   Available versions:
     • 2.1.0 (latest)
     • 2.0.0
     • 1.5.2
     • 1.5.1
     • 1.2.0
     • 1.0.0

❌ Error: No versions available for bundle 'new-bundle'
   Tip: Bundle may not have any git tags yet.
        Try installing from a branch (e.g., --version main)

❌ Error: Invalid version format '1.2'
   Version must be:
     • Semver tag: 1.2.0, v1.2.0, 2.0.0-beta
     • Branch name: main, develop
     • Special: latest

❌ Error: Cannot resolve 'latest' version
   Bundle has no semver tags available.
   Try installing from a branch:
     nova bundle install fintech-advisor@official --version main
```

**Testing Requirements:**
- Test install command with --version flag
- Test install command with version in spec
- Test install command defaults (no version)
- Test install command with "latest"
- Test install command with branch name
- Test update command with --to-version
- Test update command with --to-latest
- Test update command default (no flags)
- Test versions command output
- Test versions command with --limit
- Test versions command with --all
- Test list command with --show-versions
- Test error messages for version not found
- Test error messages for invalid version format
- Mock BundleInstaller for CLI testing

---

## Manifest Enhancement (from Story 2)

The marketplace manifest schema (from Story 2) already supports versions. This story uses that schema:

```yaml
# Marketplace Manifest (.nova/bundles/manifest.yaml)
marketplace:
  name: "official"
  description: "Official Nova bundles"
  version: "1.0"

bundles:
  - name: "fintech-advisor"
    description: "AI advisor for financial analysis"
    author: "Nova Team"
    tags: ["finance", "analysis"]
    versions:
      - version: "2.1.0"
        source:
          type: "git"
          url: "https://github.com/nova-bundles/fintech-advisor"
          ref: "v2.1.0"
      - version: "2.0.0"
        source:
          type: "git"
          url: "https://github.com/nova-bundles/fintech-advisor"
          ref: "v2.0.0"
      - version: "1.2.0"
        source:
          type: "git"
          url: "https://github.com/nova-bundles/fintech-advisor"
          ref: "v1.2.0"
      # ... more versions ...
```

**Manifest Version Handling:**
- Marketplace manifests CAN list available versions
- But git tags are the source of truth
- Manifest versions are optional (can be auto-generated from tags)
- Installation always uses git tags, not manifest
- Manifest provides metadata (description, author) per version

**Version Discovery Priority:**
1. Git tags (always checked)
2. Manifest versions (supplemental metadata only)

---

## Registry Enhancement

The registry schema (from Story 4) already includes version field. No changes needed:

```json
{
  "bundles": [
    {
      "name": "fintech-advisor",
      "version": "1.2.0",  // Version is already tracked
      "source": {
        "type": "git",
        "url": "https://github.com/nova-bundles/fintech-advisor",
        "ref": "v1.2.0"  // Git ref includes version
      },
      "marketplace": "official",
      "installed_at": "2025-10-19T10:30:00Z",
      "location": ".nova/bundles/fintech-advisor"
    }
  ]
}
```

**Version Tracking:**
- `version`: Human-readable version label (e.g., "1.2.0")
- `source.ref`: Git ref used for installation (e.g., "v1.2.0", "main")
- Both are stored for reference
- Version comes from git tag or branch name

---

## Testing Strategy

### Unit Tests

**Test each module independently:**

- `test_bundles_versioning.py` - Version parsing and comparison
  - Test Version.parse() with various formats
  - Test to_git_ref() conversion
  - Test version comparison operators
  - Test parse_version_spec()
  - Test is_valid_version()
  - Test compare_versions()
  - Test sort_versions()
  - Test get_latest_version()
  - Test edge cases (empty, invalid, special chars)

- `test_bundles_git_client.py` - Git version operations
  - Test list_tags() (mock subprocess)
  - Test get_latest_tag()
  - Test tag_exists()
  - Test error handling

- `test_bundles_installer.py` - Version-aware installation
  - Test install() with version parameter
  - Test install() with version in spec
  - Test install() with "latest"
  - Test update() with to_version
  - Test update() to latest
  - Test list_available_versions()
  - Test _resolve_version()
  - Mock GitClient and versioning functions

### Integration Tests

**Test complete version system:**

- `test_bundle_versioning.py` - End-to-end
  - Test install specific version (full flow)
  - Test install latest version
  - Test update to specific version
  - Test update to latest
  - Test list available versions
  - Test version resolution edge cases
  - Test registry version tracking

- `test_bundle_cli_versioning.py` - CLI version commands
  - Test install with --version flag
  - Test install with version in spec
  - Test update --to-version
  - Test update --to-latest
  - Test versions command
  - Test list with --show-versions
  - Test error cases
  - Mock BundleInstaller

### Test Fixtures

```python
@pytest.fixture
def mock_git_tags():
    """Mock git tags for testing."""
    return ["v2.1.0", "v2.0.0", "v1.5.2", "v1.5.1", "v1.5.0", "v1.2.0", "v1.0.0"]


@pytest.fixture
def mock_git_client_with_versions(monkeypatch):
    """Mock GitClient with version support."""
    class MockGitClient:
        def list_tags(self, repository_url):
            return ["v2.1.0", "v2.0.0", "v1.5.2", "v1.2.0", "v1.0.0"]

        def get_latest_tag(self, repository_url):
            return "v2.1.0"

        def tag_exists(self, repository_url, tag):
            return tag in ["v2.1.0", "v2.0.0", "v1.5.2", "v1.2.0", "v1.0.0"]

        # ... other methods from Story 4 ...

    return MockGitClient()


@pytest.fixture
def sample_registry_with_versions():
    """Sample registry with version info."""
    return [
        BundleRegistryEntry(
            name="test-bundle",
            version="1.2.0",
            source=BundleSourceInfo(
                type="git",
                url="https://github.com/test/bundle",
                ref="v1.2.0"
            ),
            installed_at="2025-10-19T10:00:00Z",
            location=".nova/bundles/test-bundle"
        )
    ]
```

---

## Success Criteria

- [ ] Version parsing works for semver and branch names
- [ ] Version comparison is correct (semver ordering)
- [ ] Git tag listing works (remote ls-remote)
- [ ] "latest" resolves to newest semver tag
- [ ] Install with --version works
- [ ] Install with version in spec works (name@marketplace@1.2.0)
- [ ] Install defaults to "latest" for marketplace bundles
- [ ] Update to specific version works
- [ ] Update to latest works
- [ ] List available versions works
- [ ] CLI displays versions in bundle list
- [ ] Registry tracks version information
- [ ] Error messages are clear and actionable
- [ ] Version not found shows available versions
- [ ] Invalid version format shows expected formats
- [ ] Code follows ruthless simplicity principles
- [ ] All modules have clear, single responsibilities
- [ ] Comprehensive test coverage (unit + integration)
- [ ] Version system is pure labeling (no semantic understanding)

---

## Dependencies

**This Story Depends On:**
- Feature 1: Config Management - MUST be complete
- Feature 2, Story 1: Marketplace Configuration - MUST be complete
- Feature 2, Story 2: Marketplace Manifest System - MUST be complete
- Feature 2, Story 4: Git-Based Bundle Distribution - MUST be complete
  - Uses BundleInstaller
  - Uses GitClient
  - Uses BundleRegistry
  - Extends all with version support

**This Story Enables:**
- Feature 2, Story 6: Dependency resolution (can specify version constraints)
- Bundle migration guides (bundle authors can document version changes)
- Breaking change management (via version numbers)
- Rollback to previous versions (reinstall old version)

**Required Packages:**
- pydantic >= 2.12.3 (already in project)
- typer >= 0.19.2 (already in project)
- rich (already in project)

**No new dependencies needed.**

---

## Implementation Phases

### Phase 1: Version Parsing (Module: versioning)
**Estimated Time:** 1 hour
**Deliverables:**
- Version data model
- Semver parsing
- Version comparison
- Helper functions
- Unit tests

### Phase 2: Git Version Operations (Module: git_client updates)
**Estimated Time:** 1 hour
**Deliverables:**
- Tag listing (git ls-remote)
- Latest tag resolution
- Tag existence checking
- Unit tests

### Phase 3: Version-Aware Installation (Module: installer updates)
**Estimated Time:** 1.5 hours
**Deliverables:**
- Version parameter support
- Version resolution logic
- List available versions
- Update to version
- Unit tests

### Phase 4: CLI Version Commands (Module: cli/commands/bundle.py updates)
**Estimated Time:** 1 hour
**Deliverables:**
- Updated install command
- Updated update command
- New versions command
- Updated list command
- CLI integration tests

### Phase 5: Polish and Documentation
**Estimated Time:** 0.5 hours
**Deliverables:**
- Error message improvements
- CLI help text
- Usage examples
- Version format documentation

**Total Estimated Time:** 5 hours (within 4-5 hour estimate, medium complexity)

---

## What Stories 2-4 Provide

### Story 2: Marketplace Manifest System
- Manifest schema with versions array
- Version metadata (description, author)
- Source URLs per version
- ManifestFetcher to retrieve manifests

### Story 4: Git-Based Bundle Distribution
- BundleInstaller (install/uninstall/update)
- GitClient (clone, pull)
- BundleRegistry (track installations)
- Registry already has version field
- Installation flow and error handling

**What This Story (5) Adds:**
- Version parsing and comparison
- Git tag listing and resolution
- "latest" version resolution
- Install specific versions
- Update to specific versions
- List available versions
- CLI version support

---

## What This Enables for Story 6

### For Story 6: Dependency Resolution (future feature)
- Version constraints can be specified (e.g., ">=1.0.0, <2.0.0")
- Dependency versions can be resolved
- Version compatibility checking
- Conflict resolution based on versions

**Foundation This Story Provides:**
- Version parsing (can be extended for constraints)
- Version comparison (can be used for range checking)
- Version resolution (can be used for dependency resolution)
- Registry tracks versions (can check installed vs required)

---

## Future Considerations (Not in Scope)

These are explicitly **not** included in this story:

- Version constraint parsing (>=, <, ~, ^)
- Dependency version resolution
- Breaking change detection (bundle author responsibility)
- Automatic migrations between versions (bundle author responsibility)
- Version compatibility checking (Nova Core)
- Semantic version understanding (just labels for now)
- Version pinning in lock files
- Version range resolution
- Pre-release version handling (beyond basic parsing)

Keep the implementation focused on VERSION LABELING. Nova Core and bundle authors handle semantic understanding and compatibility.

---

## Appendix: Design Rationale

### Why Git Tags as Source of Truth?

1. **Industry standard**: Package managers use git tags for versions
2. **No duplication**: Version lives in one place (git)
3. **Automatic**: Authors just tag releases
4. **Verifiable**: Git history shows when tags were created
5. **Flexible**: Supports any versioning scheme via tags

### Why Semver Recommended but Not Enforced?

1. **Start simple**: Don't require authors to use semver initially
2. **Flexibility**: Some bundles may use different schemes
3. **Evolution**: Can enforce semver later if needed
4. **Branch support**: Allow installing from branches too
5. **Pragmatic**: Recommendation guides most users, flexibility helps others

### Why "latest" as Special Version?

1. **Common use case**: Most users want latest stable version
2. **Clear intent**: Explicit "give me newest" request
3. **Safe default**: For marketplace bundles, latest is usually best
4. **Familiar**: npm, pip, etc. use similar concepts
5. **Discoverable**: Easy to understand and use

### Why List Tags via `git ls-remote`?

1. **No clone needed**: Can list tags without downloading
2. **Efficient**: Fast operation, minimal bandwidth
3. **Accurate**: Always current (not cached)
4. **Simple**: Standard git command
5. **Reliable**: Works with any git repository

### Why Simple String Comparison Initially?

1. **YAGNI**: Full semver comparison is complex and may not be needed
2. **Good enough**: Simple comparison works for basic cases
3. **Evolvable**: Can add full semver later if needed
4. **Testable**: Easy to test and verify
5. **Clear**: Easy to understand and debug

### Why Store Version in Registry?

1. **Fast lookup**: Don't need to check git for installed version
2. **Display**: Can show versions without git operations
3. **History**: Know what version was installed when
4. **Rollback**: Can see what version to reinstall
5. **Metadata**: Version is part of installation record

This specification provides everything needed to implement Feature 2, Story 5 following the modular design philosophy and ruthless simplicity principles. Version support is pure labeling - git tags are truth, infrastructure transports, bundle authors control semantics.
