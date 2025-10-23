"""Validation helpers for Nova utilities."""

from __future__ import annotations

from pydantic import ValidationError

__all__ = ["format_validation_error"]


def format_validation_error(kind: str, error: ValidationError) -> str:
    """Return a concise validation error message scoped to the provided kind."""
    details = error.errors()
    message = details[0].get("msg") if details else str(error)
    return f"Invalid {kind}: {message}"
