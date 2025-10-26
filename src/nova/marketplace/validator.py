"""Marketplace validation."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from nova.common import create_logger
from nova.marketplace.models import (
    MarketplaceError,
    MarketplaceInvalidManifestError,
    MarketplaceManifest,
)
from nova.utils.functools.models import Err, Ok, Result

logger = create_logger("marketplace.validator")


def load_and_validate_marketplace(
    marketplace_dir: Path,
) -> Result[MarketplaceManifest, MarketplaceError]:
    logger.debug("Validating marketplace", path=str(marketplace_dir))
    manifest_path = marketplace_dir / "marketplace.json"

    if not manifest_path.exists():
        error = MarketplaceInvalidManifestError(
            source=str(marketplace_dir),
            message="marketplace.json not found in repository",
        )
        logger.error("Marketplace validation failed", path=str(marketplace_dir), error=error.message)
        return Err(error)

    try:
        content = manifest_path.read_text()
        data = json.loads(content)
        manifest = MarketplaceManifest.model_validate(data)
        logger.debug("Marketplace validated", name=manifest.name, bundles=len(manifest.bundles))
        return Ok(manifest)

    except json.JSONDecodeError as e:
        error = MarketplaceInvalidManifestError(
            source=str(marketplace_dir),
            message=f"Invalid JSON in marketplace.json: {e}",
        )
        logger.error("Marketplace validation failed", path=str(marketplace_dir), error=error.message)
        return Err(error)
    except ValidationError as e:
        errors = "; ".join(f"{err['loc'][0]}: {err['msg']}" for err in e.errors())
        error = MarketplaceInvalidManifestError(
            source=str(marketplace_dir),
            message=f"Invalid marketplace.json: {errors}",
        )
        logger.error("Marketplace validation failed", path=str(marketplace_dir), error=error.message)
        return Err(error)
    except Exception as e:
        error = MarketplaceInvalidManifestError(
            source=str(marketplace_dir),
            message=f"Failed to read marketplace.json: {e}",
        )
        logger.error("Marketplace validation failed", path=str(marketplace_dir), error=error.message)
        return Err(error)
