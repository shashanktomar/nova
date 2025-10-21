# Feature 2, Story 6: Bundle Publishing - Implementation Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Updated:** 2025-10-20
**Author:** AI Architecture Team (zen-architect)

## Overview

This specification defines the implementation for bundle publishing workflow (Feature 2, Story 6, P2 priority). It follows the "bricks and studs" modular design philosophy - each module is a self-contained brick with clear contracts (studs) that can be independently generated and regenerated.

This story implements the bundle publishing workflow. It allows bundle authors to publish their bundles to marketplaces by generating manifest entries. The infrastructure validates that bundles have required metadata but does NOT validate bundle content quality - that's the marketplace maintainer's responsibility during PR review.

**Story Scope:**
- Bundle metadata file (`bundle.yaml`) in bundle root
- Bundle structure validation (has required files)
- Manifest entry generation from bundle metadata
- Publishing workflow (dry-run, generate entry)
- Version tagging support
- Publishing instructions for authors

**Out of Scope:**
- Bundle content validation (marketplace maintainers review quality)
- Bundle quality review (human maintainers approve PRs)
- Automated testing of bundles (bundle authors' CI/CD)
- Bundle signing/verification (future security feature)
- Automated marketplace PR creation (future enhancement)
- Bundle type-specific validation (Features 3, 5 define their own)

## Architecture Summary

**Approach:** Generate manifest entry from bundle metadata, output for manual PR

**Key Decisions:**
- `bundle.yaml` in bundle root defines metadata
- Publishing = REGISTRATION only (adds to marketplace manifest)
- Bundle must already be in git repo with proper structure
- Infrastructure validates metadata exists, not content quality
- Marketplace maintainers approve PRs (human review)
- Start simple: manual PR workflow, automate later if needed
- Clear instructions for authors on publishing process
- Dry-run mode essential for testing

**Publishing Flow:**
```
1. Author creates bundle with bundle.yaml
2. Author runs `nova bundle validate` to check structure
3. Author runs `nova bundle publish --dry-run` to preview manifest entry
4. Author runs `nova bundle publish --marketplace <name>` to generate entry
5. Nova outputs manifest entry to stdout
6. Author manually creates PR to marketplace repo with entry
7. Marketplace maintainer reviews and merges PR
```

**Bundle Metadata Schema (`bundle.yaml`):**
```yaml
name: "my-bundle"
version: "1.0.0"
type: "domain"  # or "extension"
description: "Brief description of the bundle"
author:
  name: "Author Name"
  email: "author@example.com"
homepage: "https://docs.example.com/my-bundle"
repository: "https://github.com/user/my-bundle"

# Type-specific metadata (defined by Features 3, 5)
# Domain bundles might have: domain_data
# Extension bundles might have: extension_metadata
```

## Module Structure

```
src/nova/
├── bundles/
│   ├── __init__.py          # Public API exports (already exists)
│   ├── metadata.py          # Bundle metadata models and parsing
│   ├── validator.py         # Bundle structure validation
│   ├── publisher.py         # Publishing workflow
│   └── generator.py         # Manifest entry generation
└── cli/
    └── commands/
        └── bundle.py        # Update with publish commands
```

---

## Module Specifications

### Module: bundles.metadata

**Purpose:** Define bundle metadata schema and parsing

**Location:** `src/nova/bundles/metadata.py`

**Contract:**
- **Inputs:** YAML content from bundle.yaml file
- **Outputs:** Validated Pydantic model instances
- **Side Effects:** Reads bundle.yaml from filesystem
- **Dependencies:** pydantic, yaml, pathlib

**Public Interface:**

```python
from pathlib import Path
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Any

class BundleAuthorMetadata(BaseModel):
    """Bundle author metadata.

    Attributes:
        name: Author name
        email: Author email (optional)

    Example:
        >>> author = BundleAuthorMetadata(
        ...     name="John Doe",
        ...     email="john@example.com"
        ... )
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


class BundleMetadata(BaseModel):
    """Bundle metadata from bundle.yaml.

    This is the metadata that bundle authors provide in their bundle root.

    Attributes:
        name: Bundle name (unique identifier)
        version: Bundle version (semver recommended)
        type: Bundle type (domain, extension, etc.)
        description: Human-readable bundle description
        author: Bundle author information
        homepage: Bundle documentation/homepage URL (optional)
        repository: Bundle source repository URL
        extra: Additional type-specific metadata (not validated)

    Example:
        >>> metadata = BundleMetadata(
        ...     name="fintech-advisor",
        ...     version="1.0.0",
        ...     type="domain",
        ...     description="Financial advisory domain knowledge",
        ...     author=BundleAuthorMetadata(name="Nova Team"),
        ...     repository="https://github.com/nova-bundles/fintech-advisor"
        ... )
    """
    model_config = {"extra": "allow"}  # Allow type-specific fields

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Bundle name"
    )
    version: str = Field(
        min_length=1,
        max_length=50,
        description="Bundle version"
    )
    type: str = Field(
        min_length=1,
        max_length=50,
        description="Bundle type"
    )
    description: str = Field(
        min_length=1,
        max_length=500,
        description="Bundle description"
    )
    author: BundleAuthorMetadata = Field(
        description="Bundle author information"
    )
    homepage: HttpUrl | None = Field(
        default=None,
        description="Bundle homepage/documentation URL"
    )
    repository: str = Field(
        min_length=1,
        description="Bundle source repository URL"
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
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Bundle name must contain only letters, numbers, hyphens, and underscores"
            )
        return v

    @field_validator("repository")
    @classmethod
    def validate_repository(cls, v: str) -> str:
        """Validate repository URL format.

        Args:
            v: Repository URL to validate

        Returns:
            Validated URL

        Raises:
            ValueError: If URL is invalid
        """
        # Must be a valid URL or git URL
        if not (v.startswith(("http://", "https://", "git@", "git://"))):
            raise ValueError(
                "Repository must be a valid URL (http://, https://, git@, or git://)"
            )
        return v


class BundleMetadataReader:
    """Read and parse bundle metadata from bundle.yaml.

    Handles reading bundle.yaml from bundle root directory and parsing
    it into validated BundleMetadata instance.

    Example:
        >>> reader = BundleMetadataReader()
        >>> metadata = reader.read(Path("/path/to/bundle"))
        >>> print(metadata.name, metadata.version)
    """

    def __init__(self):
        """Initialize metadata reader."""
        pass

    def read(self, bundle_path: Path) -> BundleMetadata:
        """Read bundle metadata from bundle.yaml.

        Args:
            bundle_path: Path to bundle root directory

        Returns:
            Validated BundleMetadata instance

        Raises:
            FileNotFoundError: If bundle.yaml doesn't exist
            ValueError: If bundle.yaml is invalid

        Algorithm:
            1. Check for bundle.yaml in bundle_path
            2. Read YAML content
            3. Parse with Pydantic validation
            4. Return BundleMetadata instance

        Example:
            >>> reader = BundleMetadataReader()
            >>> metadata = reader.read(Path("~/my-bundle"))
            >>> assert metadata.name == "my-bundle"
        """
        pass

    def validate_yaml_content(self, yaml_content: str) -> tuple[bool, list[str]]:
        """Validate YAML content without raising exceptions.

        Useful for checking validity before parsing.

        Args:
            yaml_content: YAML string to validate

        Returns:
            Tuple of (is_valid, error_messages)
            If valid: (True, [])
            If invalid: (False, ["error1", "error2", ...])

        Example:
            >>> reader = BundleMetadataReader()
            >>> is_valid, errors = reader.validate_yaml_content(yaml_str)
            >>> if not is_valid:
            ...     print(f"Errors: {errors}")
        """
        pass
```

**Validation Rules:**
- Bundle name: Alphanumeric with hyphens/underscores, 1-100 chars
- Version: Any non-empty string (semver recommended)
- Type: Any string 1-50 chars (not validated semantically)
- Description: 1-500 chars
- Author name: Required, 1-200 chars
- Author email: Optional, basic format validation
- Homepage: Optional, valid URL
- Repository: Required, valid URL or git URL
- Extra fields: Allowed (type-specific metadata)

**Testing Requirements:**
- Test BundleAuthorMetadata validation (valid, invalid email)
- Test BundleMetadata validation (all fields)
- Test name validation (valid, invalid characters)
- Test repository URL validation
- Test extra fields are preserved
- Test BundleMetadataReader.read() with valid bundle.yaml
- Test BundleMetadataReader.read() with missing file
- Test BundleMetadataReader.read() with invalid YAML
- Test validate_yaml_content() for valid/invalid YAML

---

### Module: bundles.validator

**Purpose:** Validate bundle structure and metadata

**Location:** `src/nova/bundles/validator.py`

**Contract:**
- **Inputs:** Path to bundle directory
- **Outputs:** Validation results (pass/fail with messages)
- **Side Effects:** Reads filesystem to check structure
- **Dependencies:** pathlib, bundles.metadata

**Public Interface:**

```python
from pathlib import Path
from dataclasses import dataclass
from nova.bundles.metadata import BundleMetadataReader

@dataclass
class ValidationResult:
    """Result of bundle validation.

    Attributes:
        valid: Whether bundle is valid
        errors: List of error messages
        warnings: List of warning messages
        metadata: Parsed bundle metadata (if valid)

    Example:
        >>> result = ValidationResult(
        ...     valid=True,
        ...     errors=[],
        ...     warnings=["Missing README.md"],
        ...     metadata=metadata_obj
        ... )
    """
    valid: bool
    errors: list[str]
    warnings: list[str]
    metadata: BundleMetadata | None = None


class BundleValidator:
    """Validate bundle structure and metadata.

    Validates that a bundle has required structure:
    - bundle.yaml exists and is valid
    - Bundle is in a git repository
    - Basic structure requirements

    Does NOT validate bundle content quality - that's marketplace maintainer's job.

    Example:
        >>> validator = BundleValidator()
        >>> result = validator.validate(Path("~/my-bundle"))
        >>> if result.valid:
        ...     print("Bundle is valid!")
        >>> else:
        ...     print(f"Errors: {result.errors}")
    """

    def __init__(self, metadata_reader: BundleMetadataReader | None = None):
        """Initialize bundle validator.

        Args:
            metadata_reader: BundleMetadataReader instance (creates default if None)
        """
        pass

    def validate(self, bundle_path: Path) -> ValidationResult:
        """Validate bundle structure and metadata.

        Args:
            bundle_path: Path to bundle root directory

        Returns:
            ValidationResult with validation status and messages

        Validation Checks:
            ERRORS (must pass):
            - bundle_path exists and is directory
            - bundle.yaml exists in bundle root
            - bundle.yaml is valid YAML
            - bundle.yaml has all required fields
            - Bundle is in a git repository

            WARNINGS (recommended):
            - README.md exists (recommended)
            - License file exists (recommended)

        Algorithm:
            1. Check bundle_path exists
            2. Check bundle.yaml exists
            3. Read and parse bundle.yaml
            4. Validate bundle is in git repo
            5. Check for recommended files (warnings)
            6. Return ValidationResult

        Example:
            >>> validator = BundleValidator()
            >>> result = validator.validate(Path("~/my-bundle"))
            >>> print(f"Valid: {result.valid}")
            >>> print(f"Errors: {result.errors}")
            >>> print(f"Warnings: {result.warnings}")
        """
        pass

    def _check_git_repository(self, bundle_path: Path) -> tuple[bool, str | None]:
        """Check if bundle is in a git repository.

        Args:
            bundle_path: Path to bundle directory

        Returns:
            Tuple of (is_git_repo, error_message)
            If git repo: (True, None)
            If not: (False, "error message")

        Algorithm:
            1. Walk up directory tree looking for .git
            2. If found: return (True, None)
            3. If not found: return (False, error message)
        """
        pass

    def _check_recommended_files(self, bundle_path: Path) -> list[str]:
        """Check for recommended files in bundle.

        Args:
            bundle_path: Path to bundle directory

        Returns:
            List of warning messages for missing recommended files

        Recommended Files:
            - README.md: Bundle documentation
            - LICENSE or LICENSE.txt: License file
        """
        pass
```

**Validation Categories:**

**ERRORS (must pass to publish):**
- Bundle directory exists
- bundle.yaml exists in bundle root
- bundle.yaml is valid YAML syntax
- bundle.yaml has all required fields
- Bundle is in a git repository
- Bundle name is valid format
- Repository URL is valid

**WARNINGS (recommended but not required):**
- README.md exists
- LICENSE file exists

**Testing Requirements:**
- Test validate() with valid bundle (all checks pass)
- Test validate() with missing bundle.yaml (error)
- Test validate() with invalid bundle.yaml (error)
- Test validate() with bundle not in git (error)
- Test validate() with missing README (warning)
- Test validate() with missing LICENSE (warning)
- Test _check_git_repository() finds .git directory
- Test _check_git_repository() returns false when not in git
- Test _check_recommended_files() detects missing files
- Test ValidationResult structure

---

### Module: bundles.generator

**Purpose:** Generate marketplace manifest entry from bundle metadata

**Location:** `src/nova/bundles/generator.py`

**Contract:**
- **Inputs:** BundleMetadata instance
- **Outputs:** Marketplace manifest entry (YAML string)
- **Side Effects:** None (pure transformation)
- **Dependencies:** yaml, bundles.metadata, marketplace.manifest

**Public Interface:**

```python
import yaml
from nova.bundles.metadata import BundleMetadata
from nova.marketplace.manifest import BundleManifestEntry, BundleSource, BundleAuthor


class ManifestEntryGenerator:
    """Generate marketplace manifest entry from bundle metadata.

    Transforms bundle.yaml metadata into marketplace manifest entry format.

    Example:
        >>> generator = ManifestEntryGenerator()
        >>> entry_yaml = generator.generate(bundle_metadata)
        >>> print(entry_yaml)  # YAML string for manifest
    """

    def __init__(self):
        """Initialize manifest entry generator."""
        pass

    def generate(
        self,
        bundle_metadata: BundleMetadata,
        source_type: str = "git"
    ) -> str:
        """Generate YAML manifest entry from bundle metadata.

        Args:
            bundle_metadata: Bundle metadata from bundle.yaml
            source_type: Source type (git, http, local) - default: git

        Returns:
            YAML string for marketplace manifest entry

        Algorithm:
            1. Create BundleSource from repository URL
            2. Create BundleAuthor from author metadata
            3. Create BundleManifestEntry with all fields
            4. Serialize to YAML with formatting
            5. Return YAML string

        Example:
            >>> generator = ManifestEntryGenerator()
            >>> metadata = BundleMetadata(
            ...     name="my-bundle",
            ...     version="1.0.0",
            ...     type="domain",
            ...     description="My bundle",
            ...     author=BundleAuthorMetadata(name="Author"),
            ...     repository="https://github.com/user/my-bundle"
            ... )
            >>> yaml_entry = generator.generate(metadata)
            >>> # Output is YAML string ready for manifest
        """
        pass

    def generate_entry_dict(
        self,
        bundle_metadata: BundleMetadata,
        source_type: str = "git"
    ) -> dict:
        """Generate manifest entry as dictionary.

        Args:
            bundle_metadata: Bundle metadata from bundle.yaml
            source_type: Source type (git, http, local)

        Returns:
            Dictionary representation of manifest entry

        Useful for programmatic access or further processing.

        Example:
            >>> generator = ManifestEntryGenerator()
            >>> entry_dict = generator.generate_entry_dict(metadata)
            >>> print(entry_dict["name"])  # "my-bundle"
        """
        pass

    def format_yaml(self, entry_dict: dict) -> str:
        """Format entry dictionary as YAML string.

        Args:
            entry_dict: Manifest entry dictionary

        Returns:
            Formatted YAML string

        Format:
            - Indented 2 spaces
            - No document start marker (---)
            - Sorted keys for consistency
            - Readable formatting

        Example:
            >>> generator = ManifestEntryGenerator()
            >>> yaml_str = generator.format_yaml(entry_dict)
            >>> print(yaml_str)
        """
        pass
```

**Generated YAML Format:**

```yaml
name: "my-bundle"
type: "domain"
version: "1.0.0"
description: "Brief description of the bundle"
source:
  type: "git"
  url: "https://github.com/user/my-bundle"
author:
  name: "Author Name"
  email: "author@example.com"
homepage: "https://docs.example.com/my-bundle"
```

**Testing Requirements:**
- Test generate() produces valid YAML
- Test generate() includes all required fields
- Test generate() with optional homepage
- Test generate() with no email
- Test generate_entry_dict() returns correct structure
- Test format_yaml() produces readable YAML
- Test generated YAML parses back to BundleManifestEntry

---

### Module: bundles.publisher

**Purpose:** Bundle publishing workflow orchestration

**Location:** `src/nova/bundles/publisher.py`

**Contract:**
- **Inputs:** Bundle path, marketplace name, dry-run flag
- **Outputs:** Publishing instructions and manifest entry
- **Side Effects:**
  - Validates bundle structure
  - Reads bundle metadata
  - Outputs manifest entry
- **Dependencies:** All other bundles modules, marketplace modules

**Public Interface:**

```python
from pathlib import Path
from dataclasses import dataclass
from nova.bundles.validator import BundleValidator, ValidationResult
from nova.bundles.metadata import BundleMetadataReader
from nova.bundles.generator import ManifestEntryGenerator
from nova.marketplace.config import get_marketplace_config


@dataclass
class PublishResult:
    """Result of bundle publish operation.

    Attributes:
        success: Whether publish was successful
        manifest_entry: Generated manifest entry YAML (if successful)
        validation_result: Bundle validation result
        instructions: Instructions for completing publication
        errors: List of error messages

    Example:
        >>> result = PublishResult(
        ...     success=True,
        ...     manifest_entry="name: my-bundle\n...",
        ...     validation_result=validation_result,
        ...     instructions="Create PR to...",
        ...     errors=[]
        ... )
    """
    success: bool
    manifest_entry: str | None
    validation_result: ValidationResult
    instructions: str
    errors: list[str]


class BundlePublishError(Exception):
    """Error during bundle publishing."""
    pass


class BundlePublisher:
    """Publish bundles to marketplace.

    Handles the publishing workflow:
    1. Validate bundle structure
    2. Read bundle metadata
    3. Generate manifest entry
    4. Output instructions for PR

    Does NOT:
    - Create PR automatically (future enhancement)
    - Validate bundle content (marketplace maintainer's job)
    - Modify marketplace files directly

    Example:
        >>> publisher = BundlePublisher()
        >>> result = publisher.publish(
        ...     bundle_path=Path("~/my-bundle"),
        ...     marketplace="official",
        ...     dry_run=False
        ... )
        >>> print(result.manifest_entry)
        >>> print(result.instructions)
    """

    def __init__(
        self,
        validator: BundleValidator | None = None,
        metadata_reader: BundleMetadataReader | None = None,
        generator: ManifestEntryGenerator | None = None
    ):
        """Initialize bundle publisher.

        Args:
            validator: BundleValidator instance (creates default if None)
            metadata_reader: BundleMetadataReader instance (creates default if None)
            generator: ManifestEntryGenerator instance (creates default if None)
        """
        pass

    def publish(
        self,
        bundle_path: Path,
        marketplace: str,
        dry_run: bool = False
    ) -> PublishResult:
        """Publish bundle to marketplace.

        Args:
            bundle_path: Path to bundle root directory
            marketplace: Marketplace name to publish to
            dry_run: If True, validate and preview only (don't generate final output)

        Returns:
            PublishResult with manifest entry and instructions

        Raises:
            BundlePublishError: If publishing fails

        Workflow:
            1. Validate bundle structure and metadata
            2. If validation fails: return errors
            3. Read bundle metadata
            4. Verify marketplace exists in config
            5. Generate manifest entry YAML
            6. Generate publishing instructions
            7. Return PublishResult

        Example:
            >>> publisher = BundlePublisher()
            >>> result = publisher.publish(
            ...     bundle_path=Path("~/my-bundle"),
            ...     marketplace="official",
            ...     dry_run=True
            ... )
            >>> if result.success:
            ...     print("Preview:")
            ...     print(result.manifest_entry)
        """
        pass

    def generate_publishing_instructions(
        self,
        marketplace: str,
        bundle_name: str,
        manifest_entry: str
    ) -> str:
        """Generate instructions for completing publication.

        Args:
            marketplace: Marketplace name
            bundle_name: Bundle name
            manifest_entry: Generated manifest entry YAML

        Returns:
            Formatted instructions string

        Instructions Include:
            1. Where to find marketplace repository
            2. How to add manifest entry
            3. How to create PR
            4. What reviewers will check

        Example:
            >>> publisher = BundlePublisher()
            >>> instructions = publisher.generate_publishing_instructions(
            ...     "official",
            ...     "my-bundle",
            ...     yaml_entry
            ... )
            >>> print(instructions)
        """
        pass

    def _verify_marketplace_exists(self, marketplace: str) -> tuple[bool, str | None]:
        """Verify marketplace exists in config.

        Args:
            marketplace: Marketplace name

        Returns:
            Tuple of (exists, error_message)
            If exists: (True, None)
            If not: (False, error message with available marketplaces)
        """
        pass
```

**Publishing Instructions Template:**

```
Publishing Instructions for '{bundle_name}' to '{marketplace}' Marketplace
═══════════════════════════════════════════════════════════════════════

1. Marketplace Repository
   Clone the marketplace repository:
   {marketplace_url}

2. Add Manifest Entry
   Open the manifest file (typically manifest.yaml or bundles.yaml)

   Add the following entry to the 'bundles' list:

   {manifest_entry}

3. Create Pull Request
   - Commit your changes
   - Push to a new branch
   - Create PR to marketplace repository
   - Title: "Add {bundle_name} bundle"
   - Description: Brief explanation of what your bundle does

4. What Reviewers Will Check
   - Bundle metadata is complete and accurate
   - Bundle actually exists at repository URL
   - Bundle provides value to marketplace users
   - Bundle follows marketplace guidelines (if any)

5. After Merge
   - Your bundle will be available in the marketplace
   - Users can install with: nova bundle install {bundle_name}@{marketplace}

Need help? Check marketplace documentation or contact maintainers.
```

**Testing Requirements:**
- Test publish() with valid bundle (dry-run)
- Test publish() with valid bundle (actual publish)
- Test publish() with invalid bundle (validation fails)
- Test publish() with non-existent marketplace
- Test publish() workflow end-to-end
- Test generate_publishing_instructions() format
- Test _verify_marketplace_exists() with valid/invalid marketplace
- Test error handling for all failure modes

---

### Module: cli.commands.bundle (Update)

**Purpose:** Add publishing commands to bundle CLI

**Location:** `src/nova/cli/commands/bundle.py`

**Contract:**
- **Inputs:** Command-line arguments
- **Outputs:** Terminal output, manifest entries
- **Side Effects:**
  - Validates bundles
  - Reads bundle metadata
  - Displays formatted output
- **Dependencies:** typer, rich, bundles modules

**Public Interface (New Commands):**

```python
# Add to existing bundle CLI commands from Story 4

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from nova.bundles.validator import BundleValidator
from nova.bundles.publisher import BundlePublisher, BundlePublishError

app = typer.Typer(help="Manage Nova bundles")
console = Console()


@app.command("init")
def bundle_init(
    bundle_path: Path = typer.Argument(
        Path.cwd(),
        help="Path to bundle directory (default: current directory)"
    ),
) -> None:
    """Create bundle.yaml template.

    Generates a bundle.yaml template file in the bundle directory
    with all required fields and helpful comments.

    Example:
        nova bundle init                  # In current directory
        nova bundle init ~/my-bundle      # In specific directory
    """
    bundle_path = bundle_path.resolve()

    # Check if bundle.yaml already exists
    bundle_yaml_path = bundle_path / "bundle.yaml"
    if bundle_yaml_path.exists():
        console.print(f"[yellow]bundle.yaml already exists in {bundle_path}[/yellow]")
        if not typer.confirm("Overwrite?"):
            raise typer.Exit(0)

    # Generate template
    template = """# Nova Bundle Metadata
# Complete this template with your bundle information

name: "my-bundle"
version: "1.0.0"
type: "domain"  # or "extension"
description: "Brief description of what this bundle provides"

author:
  name: "Your Name"
  email: "your.email@example.com"  # Optional

# Optional: Bundle homepage/documentation URL
# homepage: "https://docs.example.com/my-bundle"

# Required: Source repository URL
repository: "https://github.com/yourusername/my-bundle"

# Type-specific metadata can be added below
# For domain bundles: see Feature 3 documentation
# For extension bundles: see Feature 5 documentation
"""

    # Write template
    bundle_yaml_path.write_text(template)

    console.print(f"[green]✓[/green] Created bundle.yaml in {bundle_path}")
    console.print("\nNext steps:")
    console.print("  1. Edit bundle.yaml with your bundle information")
    console.print("  2. Run 'nova bundle validate' to check structure")
    console.print("  3. Run 'nova bundle publish --dry-run' to preview")


@app.command("validate")
def bundle_validate(
    bundle_path: Path = typer.Argument(
        Path.cwd(),
        help="Path to bundle directory (default: current directory)"
    ),
) -> None:
    """Validate bundle structure and metadata.

    Checks that bundle has required structure:
    - bundle.yaml exists and is valid
    - Bundle is in git repository
    - Recommended files exist (warnings)

    Example:
        nova bundle validate                  # Validate current directory
        nova bundle validate ~/my-bundle      # Validate specific directory
    """
    bundle_path = bundle_path.resolve()

    console.print(f"Validating bundle at: [cyan]{bundle_path}[/cyan]\n")

    validator = BundleValidator()
    result = validator.validate(bundle_path)

    # Display errors
    if result.errors:
        console.print("[red]✗ Validation Errors:[/red]")
        for error in result.errors:
            console.print(f"  • {error}")
        console.print()

    # Display warnings
    if result.warnings:
        console.print("[yellow]⚠ Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  • {warning}")
        console.print()

    # Display result
    if result.valid:
        console.print("[green]✓ Bundle is valid![/green]")

        if result.metadata:
            # Display bundle info
            console.print(Panel(
                f"[bold]{result.metadata.name}[/bold] v{result.metadata.version}\n"
                f"Type: {result.metadata.type}\n"
                f"Author: {result.metadata.author.name}\n"
                f"Repository: {result.metadata.repository}",
                title="Bundle Info"
            ))

        console.print("\nNext step:")
        console.print("  nova bundle publish --marketplace <name> --dry-run")
    else:
        console.print("[red]✗ Bundle validation failed[/red]")
        console.print("\nFix the errors above and run validation again.")
        raise typer.Exit(1)


@app.command("publish")
def bundle_publish(
    marketplace: str = typer.Option(
        ...,
        "--marketplace",
        "-m",
        help="Marketplace to publish to"
    ),
    bundle_path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Path to bundle directory"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview without generating final output"
    ),
) -> None:
    """Publish bundle to marketplace.

    Generates marketplace manifest entry for your bundle.
    You'll need to manually create a PR to the marketplace repository.

    Examples:
        # Preview publication
        nova bundle publish --marketplace official --dry-run

        # Generate manifest entry for publication
        nova bundle publish --marketplace official

        # Publish bundle from specific path
        nova bundle publish --marketplace company --path ~/my-bundle
    """
    bundle_path = bundle_path.resolve()

    console.print(f"Publishing bundle from: [cyan]{bundle_path}[/cyan]")
    console.print(f"Target marketplace: [cyan]{marketplace}[/cyan]")
    if dry_run:
        console.print("[yellow](DRY RUN - Preview Only)[/yellow]")
    console.print()

    try:
        publisher = BundlePublisher()

        with console.status("[bold green]Preparing bundle for publication..."):
            result = publisher.publish(
                bundle_path=bundle_path,
                marketplace=marketplace,
                dry_run=dry_run
            )

        if not result.success:
            # Validation failed
            console.print("[red]✗ Cannot publish bundle - validation failed:[/red]\n")

            for error in result.errors:
                console.print(f"  • {error}")

            if result.validation_result.warnings:
                console.print("\n[yellow]Warnings:[/yellow]")
                for warning in result.validation_result.warnings:
                    console.print(f"  • {warning}")

            console.print("\nFix validation errors and try again:")
            console.print("  nova bundle validate")
            raise typer.Exit(1)

        # Success - display manifest entry
        console.print("[green]✓ Bundle validated successfully![/green]\n")

        if dry_run:
            console.print(Panel(
                "This is a preview. Use without --dry-run to generate final output.",
                title="Dry Run Mode",
                style="yellow"
            ))
            console.print()

        # Display manifest entry with syntax highlighting
        console.print(Panel(
            Syntax(result.manifest_entry, "yaml", theme="monokai"),
            title="Marketplace Manifest Entry"
        ))
        console.print()

        if not dry_run:
            # Display publishing instructions
            console.print(Panel(
                result.instructions,
                title="Publishing Instructions"
            ))

    except BundlePublishError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
```

**New CLI Commands:**

1. **`nova bundle init [path]`**
   - Create bundle.yaml template
   - Generates template with helpful comments
   - Can specify bundle directory (default: current)

2. **`nova bundle validate [path]`**
   - Validate bundle structure
   - Check bundle.yaml is valid
   - Verify git repository
   - Show errors and warnings
   - Display bundle info if valid

3. **`nova bundle publish --marketplace <name> [--path] [--dry-run]`**
   - Publish bundle to marketplace
   - Validate bundle first
   - Generate manifest entry
   - Show publishing instructions
   - Dry-run mode for preview

**CLI Usage Examples:**

```bash
# Create bundle.yaml template
$ nova bundle init
✓ Created bundle.yaml in /current/directory

Next steps:
  1. Edit bundle.yaml with your bundle information
  2. Run 'nova bundle validate' to check structure
  3. Run 'nova bundle publish --dry-run' to preview

# Validate bundle
$ nova bundle validate
Validating bundle at: /path/to/bundle

⚠ Warnings:
  • Recommended file missing: README.md
  • Recommended file missing: LICENSE

✓ Bundle is valid!

╭──────────── Bundle Info ────────────╮
│ my-bundle v1.0.0                    │
│ Type: domain                        │
│ Author: John Doe                    │
│ Repository: https://github.com/...  │
╰─────────────────────────────────────╯

Next step:
  nova bundle publish --marketplace official --dry-run

# Publish (dry-run)
$ nova bundle publish --marketplace official --dry-run
Publishing bundle from: /path/to/bundle
Target marketplace: official
(DRY RUN - Preview Only)

✓ Bundle validated successfully!

╭─────── Dry Run Mode ───────╮
│ This is a preview. Use     │
│ without --dry-run to       │
│ generate final output.     │
╰────────────────────────────╯

╭── Marketplace Manifest Entry ──╮
│ name: "my-bundle"              │
│ type: "domain"                 │
│ version: "1.0.0"               │
│ ...                            │
╰────────────────────────────────╯

# Publish (actual)
$ nova bundle publish --marketplace official
Publishing bundle from: /path/to/bundle
Target marketplace: official

✓ Bundle validated successfully!

╭── Marketplace Manifest Entry ──╮
│ name: "my-bundle"              │
│ type: "domain"                 │
│ version: "1.0.0"               │
│ description: "..."             │
│ source:                        │
│   type: "git"                  │
│   url: "https://github.com/..." │
│ author:                        │
│   name: "John Doe"             │
│   email: "john@example.com"    │
│ repository: "https://..."      │
╰────────────────────────────────╯

╭─── Publishing Instructions ───╮
│                                │
│ 1. Marketplace Repository      │
│    Clone: https://...          │
│                                │
│ 2. Add Manifest Entry          │
│    [entry shown above]         │
│                                │
│ 3. Create Pull Request         │
│    - Commit changes            │
│    - Create PR                 │
│    - Title: "Add my-bundle"    │
│                                │
│ ...                            │
╰────────────────────────────────╯
```

**Error Messages:**

```
❌ Error: bundle.yaml not found
   Path: /path/to/bundle

   Create bundle.yaml with: nova bundle init

❌ Error: Bundle not in git repository
   Path: /path/to/bundle

   Initialize git repository:
     cd /path/to/bundle
     git init
     git add .
     git commit -m "Initial commit"

❌ Error: Marketplace 'unknown' not found

   Configured marketplaces:
     • official
     • company

   Add marketplace:
     nova marketplace add unknown <url>

❌ Validation Errors:
   • Invalid bundle name: must contain only letters, numbers, hyphens, and underscores
   • Invalid repository URL: must start with http://, https://, or git@
   • Missing required field: author.name
```

**Testing Requirements:**
- Test init command creates template
- Test init command handles existing file
- Test validate command with valid bundle
- Test validate command with invalid bundle
- Test validate command displays errors/warnings
- Test publish command with --dry-run
- Test publish command actual publish
- Test publish command with invalid marketplace
- Test publish command with validation failures
- Test CLI output formatting
- Test error message clarity
- Mock BundleValidator and BundlePublisher

---

## bundle.yaml Schema

### Complete Schema

```yaml
# Required fields
name: "bundle-name"           # Alphanumeric, hyphens, underscores only
version: "1.0.0"              # Any string (semver recommended)
type: "domain"                # Bundle type (domain, extension, etc.)
description: "Description"    # 1-500 chars

# Required author information
author:
  name: "Author Name"         # Required
  email: "author@example.com" # Optional

# Optional fields
homepage: "https://..."       # Bundle documentation URL
repository: "https://..."     # Source repository URL (required)

# Type-specific metadata (not validated by infrastructure)
# Add any additional fields needed for your bundle type
```

### Example: Domain Bundle

```yaml
name: "fintech-advisor"
version: "1.0.0"
type: "domain"
description: "Financial advisory domain knowledge and tools"

author:
  name: "Nova Team"
  email: "team@nova.dev"

homepage: "https://docs.nova.dev/bundles/fintech-advisor"
repository: "https://github.com/nova-bundles/fintech-advisor"

# Domain-specific metadata (defined by Feature 3)
domain_data:
  categories:
    - "finance"
    - "advisory"
  knowledge_areas:
    - "investment"
    - "retirement-planning"
```

### Example: Extension Bundle

```yaml
name: "syntax-highlighter"
version: "2.1.0"
type: "extension"
description: "Advanced syntax highlighting extension"

author:
  name: "Extension Developer"
  email: "dev@example.com"

repository: "https://github.com/extensions/syntax-highlighter"

# Extension-specific metadata (defined by Feature 5)
extension_metadata:
  supported_languages:
    - "python"
    - "javascript"
    - "rust"
  requires_version: ">=0.1.0"
```

---

## Publishing Workflow Documentation

### For Bundle Authors

#### Step 1: Create Bundle Structure

```bash
# Create bundle directory
mkdir my-bundle
cd my-bundle

# Initialize git
git init

# Create bundle.yaml
nova bundle init

# Edit bundle.yaml with your information
# Add your bundle content (domain data, extension code, etc.)
```

#### Step 2: Validate Bundle

```bash
# Validate structure and metadata
nova bundle validate

# Fix any errors
# Warnings are optional but recommended
```

#### Step 3: Preview Publication

```bash
# Dry-run to preview manifest entry
nova bundle publish --marketplace official --dry-run

# Review the generated manifest entry
# Check for accuracy
```

#### Step 4: Publish Bundle

```bash
# Generate manifest entry
nova bundle publish --marketplace official

# Copy the manifest entry
# Follow the displayed instructions to create PR
```

#### Step 5: Create PR

```bash
# Clone marketplace repository (from instructions)
git clone <marketplace-repo-url>
cd <marketplace-repo>

# Create new branch
git checkout -b add-my-bundle

# Edit manifest file (typically manifest.yaml)
# Add your bundle entry to the 'bundles' list

# Commit and push
git add manifest.yaml
git commit -m "Add my-bundle to marketplace"
git push origin add-my-bundle

# Create PR on GitHub/GitLab
```

#### Step 6: Wait for Review

Marketplace maintainers will review:
- Bundle metadata is complete
- Bundle exists at repository URL
- Bundle provides value to users
- Bundle follows marketplace guidelines

#### Step 7: After Merge

Your bundle is now available:
```bash
nova bundle install my-bundle@official
```

---

## Error Handling

### Validation Errors

**Missing bundle.yaml:**
```
❌ Validation Error

  Path: /path/to/bundle
  Error: bundle.yaml not found

  Create bundle.yaml with:
    nova bundle init
```

**Invalid YAML syntax:**
```
❌ Validation Error

  File: bundle.yaml
  Error: Invalid YAML syntax at line 5

  mapping values are not allowed here

  Check YAML syntax and indentation
```

**Missing required fields:**
```
❌ Validation Error

  File: bundle.yaml
  Missing required fields:
    • name
    • version
    • author.name

  See bundle.yaml template:
    nova bundle init
```

**Not in git repository:**
```
❌ Validation Error

  Path: /path/to/bundle
  Error: Bundle not in git repository

  Initialize git:
    cd /path/to/bundle
    git init
    git add .
    git commit -m "Initial commit"
```

### Publishing Errors

**Marketplace not found:**
```
❌ Publishing Error

  Marketplace 'unknown' not configured

  Configured marketplaces:
    • official
    • company

  Add marketplace:
    nova marketplace add unknown <url>
```

**Bundle validation failed:**
```
❌ Publishing Error

  Cannot publish - bundle validation failed

  Errors:
    • Invalid bundle name format
    • Missing repository URL

  Fix errors and validate:
    nova bundle validate
```

---

## Testing Strategy

### Unit Tests

**Test each module independently:**

- `test_bundles_metadata.py` - Metadata models
  - Test BundleAuthorMetadata validation
  - Test BundleMetadata validation
  - Test name/repository validation
  - Test BundleMetadataReader.read()
  - Test validate_yaml_content()
  - Test extra fields preserved

- `test_bundles_validator.py` - Validation
  - Test validate() with valid bundle
  - Test validate() with missing bundle.yaml
  - Test validate() with invalid YAML
  - Test validate() with bundle not in git
  - Test _check_git_repository()
  - Test _check_recommended_files()
  - Test ValidationResult structure

- `test_bundles_generator.py` - Manifest generation
  - Test generate() produces valid YAML
  - Test generate() includes all fields
  - Test generate_entry_dict()
  - Test format_yaml()
  - Test generated YAML parses correctly

- `test_bundles_publisher.py` - Publishing workflow
  - Test publish() with valid bundle (dry-run)
  - Test publish() with valid bundle (actual)
  - Test publish() with invalid bundle
  - Test publish() with non-existent marketplace
  - Test generate_publishing_instructions()
  - Test _verify_marketplace_exists()
  - Test error handling

### Integration Tests

**Test complete publishing system:**

- `test_publishing_workflow.py` - End-to-end
  - Test complete publishing workflow
  - Test dry-run mode
  - Test validation integration
  - Test manifest generation
  - Test instructions generation

- `test_bundle_cli_publishing.py` - CLI commands
  - Test init command
  - Test validate command
  - Test publish command (dry-run)
  - Test publish command (actual)
  - Test error cases
  - Test output formatting
  - Mock validators and publishers

### Test Fixtures

```python
@pytest.fixture
def sample_bundle_dir(tmp_path):
    """Sample bundle directory with bundle.yaml."""
    bundle_dir = tmp_path / "test-bundle"
    bundle_dir.mkdir()

    # Create bundle.yaml
    bundle_yaml = bundle_dir / "bundle.yaml"
    bundle_yaml.write_text("""
name: test-bundle
version: 1.0.0
type: domain
description: Test bundle for testing
author:
  name: Test Author
  email: test@example.com
repository: https://github.com/test/bundle
""")

    # Initialize git
    (bundle_dir / ".git").mkdir()

    return bundle_dir


@pytest.fixture
def sample_bundle_metadata():
    """Sample bundle metadata for testing."""
    return BundleMetadata(
        name="test-bundle",
        version="1.0.0",
        type="domain",
        description="Test bundle",
        author=BundleAuthorMetadata(
            name="Test Author",
            email="test@example.com"
        ),
        repository="https://github.com/test/bundle"
    )
```

---

## Success Criteria

- [ ] BundleMetadata models defined and validated
- [ ] BundleMetadataReader reads bundle.yaml correctly
- [ ] BundleValidator validates structure and metadata
- [ ] Validation checks for git repository
- [ ] Validation provides errors and warnings
- [ ] ManifestEntryGenerator produces valid YAML
- [ ] Generated entries match marketplace manifest format
- [ ] BundlePublisher orchestrates workflow
- [ ] Publishing instructions are clear and complete
- [ ] CLI command `nova bundle init` creates template
- [ ] CLI command `nova bundle validate` validates bundle
- [ ] CLI command `nova bundle publish --dry-run` previews
- [ ] CLI command `nova bundle publish` generates entry
- [ ] Error messages are clear and actionable
- [ ] Code follows ruthless simplicity principles
- [ ] All modules have clear, single responsibilities
- [ ] Comprehensive test coverage (unit + integration)
- [ ] Documentation includes complete workflow

---

## Dependencies

**This Story Depends On:**
- Feature 1: Config Management - MUST be complete
- Feature 2, Story 1: Marketplace Configuration - MUST be complete
  - Uses MarketplaceConfig to verify marketplace exists
- Feature 2, Story 2: Marketplace Manifest System - MUST be complete
  - Uses BundleManifestEntry format for generated entries
  - Uses BundleSource and BundleAuthor models

**This Story Completes:**
- Feature 2: Bundle Distribution Infrastructure
  - Stories 1-4: Discovery and installation
  - Story 6: Publishing (this story)
  - Full distribution cycle: publish → marketplace → install

**Required Packages:**
- pydantic >= 2.12.3 (already in project)
- pyyaml >= 6.0 (already in project)
- typer >= 0.19.2 (already in project)
- rich (already in project from Story 1)

---

## Implementation Phases

### Phase 1: Metadata Models (Module: bundles.metadata)
**Estimated Time:** 1 hour
**Deliverables:**
- BundleAuthorMetadata model
- BundleMetadata model with validation
- BundleMetadataReader
- Unit tests

### Phase 2: Validation (Module: bundles.validator)
**Estimated Time:** 1.5 hours
**Deliverables:**
- BundleValidator implementation
- Structure validation checks
- Git repository check
- Recommended files check
- ValidationResult structure
- Unit tests

### Phase 3: Generation (Module: bundles.generator)
**Estimated Time:** 1 hour
**Deliverables:**
- ManifestEntryGenerator
- YAML generation from metadata
- Entry formatting
- Unit tests

### Phase 4: Publishing Workflow (Module: bundles.publisher)
**Estimated Time:** 1.5 hours
**Deliverables:**
- BundlePublisher orchestration
- Publishing instructions generation
- Marketplace verification
- PublishResult structure
- Unit tests

### Phase 5: CLI Commands (Update: cli/commands/bundle.py)
**Estimated Time:** 1 hour
**Deliverables:**
- init, validate, publish commands
- Rich formatting and syntax highlighting
- Error handling and messages
- CLI integration tests

### Phase 6: Documentation and Polish
**Estimated Time:** 0.5 hours
**Deliverables:**
- bundle.yaml template with comments
- Publishing workflow documentation
- Error message improvements
- CLI help text

**Total Estimated Time:** 6.5 hours (buffer beyond 5-6 hour estimate)

---

## What Stories 2-5 Provide and How This Completes the Cycle

### Story 2: Marketplace Manifest System Provides
- BundleManifestEntry format specification
- BundleSource and BundleAuthor models
- Manifest YAML schema and validation

### Story 4: Bundle Distribution Provides
- Bundle installation from marketplace
- Registry of installed bundles
- Git operations for cloning bundles

### What This Story (6) Completes

**The Full Distribution Cycle:**

1. **Author Creates Bundle**
   - `nova bundle init` → bundle.yaml template
   - Author develops bundle content
   - `nova bundle validate` → check structure

2. **Author Publishes to Marketplace**
   - `nova bundle publish --marketplace official` → manifest entry
   - Author creates PR to marketplace repo
   - Marketplace maintainer reviews and merges

3. **Bundle Appears in Marketplace**
   - Manifest updated with new bundle
   - `nova marketplace refresh` → fetch updated manifest
   - `nova marketplace show official` → see new bundle

4. **Users Discover and Install**
   - `nova marketplace search <query>` → find bundle
   - `nova bundle install bundle-name@official` → install from marketplace
   - Bundle is installed and ready to use

**Complete Cycle:** Create → Publish → Discover → Install → Use

---

## Future Enhancements (Not in Scope)

These are explicitly **not** included in this story but could be added later:

- Automated PR creation via GitHub API
- Bundle signing and verification
- Publishing to multiple marketplaces at once
- Automated version bumping
- Changelog generation from git history
- Bundle publishing analytics
- Bundle deprecation workflow
- Bundle transfer between authors
- Bundle templates/scaffolding for different types

Keep the implementation simple and focused on the core workflow. Add automation later if users request it.

---

## Appendix: Design Rationale

### Why bundle.yaml in Bundle Root?

1. Convention from other systems (package.json, Cargo.toml, etc.)
2. Easy to find and edit
3. Part of bundle version control
4. Travels with bundle code
5. Can be validated independently

### Why Manual PR Workflow?

1. YAGNI - Keep it simple for MVP
2. Marketplace maintainers need to review anyway
3. PR review workflow is familiar to developers
4. Automated PR creation is complex (auth, API, etc.)
5. Can add automation later if needed

### Why Generate Manifest Entry Instead of Full Manifest?

1. Marketplace may have many bundles
2. Authors only need to add their entry
3. Reduces PR conflicts
4. Clear instructions for where to add entry
5. Marketplace maintainer controls final manifest

### Why Validate Git Repository?

1. Bundles must be cloneable from git
2. Users will install via git clone
3. Ensures bundle is version controlled
4. Repository URL must work
5. Standard distribution method

### Why Allow Extra Fields in bundle.yaml?

1. Different bundle types have different needs
2. Features 3 and 5 define type-specific metadata
3. Infrastructure doesn't need to understand all fields
4. Forward compatibility for new bundle types
5. Extensibility without breaking changes

### Why Dry-Run Mode?

1. Authors can preview before publishing
2. Test manifest generation
3. Verify metadata is correct
4. Review publishing instructions
5. Build confidence before actual publish

### Why NOT Validate Bundle Content?

1. Infrastructure = transport layer only
2. Marketplace maintainers = quality reviewers
3. Bundle types have different validation needs
4. Features 3 and 5 define type-specific validation
5. Separation of concerns

This specification provides everything needed to implement Feature 2, Story 6 following the modular design philosophy and ruthless simplicity principles.
