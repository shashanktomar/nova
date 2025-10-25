"""Marketplace validation."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from nova.marketplace.models import (
    MarketplaceError,
    MarketplaceInvalidManifestError,
    MarketplaceManifest,
)
from nova.utils.functools.models import Err, Ok, Result


def validate_marketplace(
    marketplace_dir: Path,
) -> Result[MarketplaceManifest, MarketplaceError]:
    manifest_path = marketplace_dir / "marketplace.json"

    if not manifest_path.exists():
        return Err(
            MarketplaceInvalidManifestError(
                source=str(marketplace_dir),
                message="marketplace.json not found in repository",
            )
        )

    try:
        content = manifest_path.read_text()
        data = json.loads(content)
        manifest = MarketplaceManifest.model_validate(data)
        return Ok(manifest)

    except json.JSONDecodeError as e:
        return Err(
            MarketplaceInvalidManifestError(
                source=str(marketplace_dir),
                message=f"Invalid JSON in marketplace.json: {e}",
            )
        )
    except ValidationError as e:
        errors = "; ".join(f"{err['loc'][0]}: {err['msg']}" for err in e.errors())
        return Err(
            MarketplaceInvalidManifestError(
                source=str(marketplace_dir),
                message=f"Invalid marketplace.json: {errors}",
            )
        )
    except Exception as e:
        return Err(
            MarketplaceInvalidManifestError(
                source=str(marketplace_dir),
                message=f"Failed to read marketplace.json: {e}",
            )
        )
