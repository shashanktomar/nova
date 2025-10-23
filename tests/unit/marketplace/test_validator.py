from __future__ import annotations

import json

from nova.marketplace.models import MarketplaceInvalidManifestError
from nova.marketplace.validator import validate_marketplace


def test_validate_marketplace_returns_error_when_manifest_missing(tmp_path) -> None:
    result = validate_marketplace(tmp_path)

    assert result.is_err()
    error = result.unwrap_err()
    assert isinstance(error, MarketplaceInvalidManifestError)
    assert "marketplace.json not found" in error.message


def test_validate_marketplace_returns_error_for_invalid_json(tmp_path) -> None:
    manifest_path = tmp_path / "marketplace.json"
    manifest_path.write_text("{ invalid json }")

    result = validate_marketplace(tmp_path)

    assert result.is_err()
    error = result.unwrap_err()
    assert isinstance(error, MarketplaceInvalidManifestError)
    assert "Invalid JSON" in error.message


def test_validate_marketplace_returns_error_for_missing_required_fields(
    tmp_path,
) -> None:
    manifest_path = tmp_path / "marketplace.json"
    manifest_path.write_text(json.dumps({"name": "test"}))

    result = validate_marketplace(tmp_path)

    assert result.is_err()
    error = result.unwrap_err()
    assert isinstance(error, MarketplaceInvalidManifestError)
    assert "Invalid marketplace.json" in error.message


def test_validate_marketplace_returns_ok_for_valid_manifest(tmp_path) -> None:
    manifest_path = tmp_path / "marketplace.json"
    manifest_data = {
        "name": "test-marketplace",
        "version": "1.0.0",
        "description": "A test marketplace",
        "owner": {"name": "Test Owner"},
        "bundles": [
            {
                "name": "test-bundle",
                "description": "A test bundle",
                "source": "./bundles/test",
                "version": "1.0.0",
            }
        ],
    }
    manifest_path.write_text(json.dumps(manifest_data))

    result = validate_marketplace(tmp_path)

    assert result.is_ok()
    manifest = result.unwrap()
    assert manifest.name == "test-marketplace"
    assert manifest.version == "1.0.0"
    assert len(manifest.bundles) == 1


def test_validate_marketplace_returns_error_when_file_not_readable(tmp_path) -> None:
    manifest_path = tmp_path / "marketplace.json"
    manifest_path.write_text('{"name": "test"}')
    manifest_path.chmod(0o000)

    try:
        result = validate_marketplace(tmp_path)

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, MarketplaceInvalidManifestError)
        assert "Failed to read marketplace.json" in error.message
    finally:
        # Restore permissions for cleanup
        manifest_path.chmod(0o644)
