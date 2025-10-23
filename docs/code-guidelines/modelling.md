# Modelling Guidelines

## Reusable Field Types

When defining Pydantic models, prefer using shared Annotated types from `nova.utils.types` for common constraints (non-empty strings, sequences, identifiers). This keeps validation consistent and centralizes updates.

- Only add an alias when a constraint is reused in multiple places.
- Put new aliases in `src/nova/utils/types/fields.py` and export them via `src/nova/utils/types/__init__.py`.
- Immutable aliases are the default; add `Mutable...` variants only when mutation is required.
