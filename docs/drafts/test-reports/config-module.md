# Config Module Test Coverage Report

## Coverage Snapshot
- Command: `just test-cov` (pytest + coverage)
- Module coverage: ≈92.5% lines (236/255); branch coverage not reported
- Notable files below target: `src/nova/config/file/store.py` (83%), `file/paths.py` (90%), `resolver.py` (95%)
- HTML report: `htmlcov/index.html`

## High Priority Gaps
- `src/nova/config/file/store.py:101` – Missing test for `ConfigNotFoundError` when the path vanishes between discovery and load.
- `src/nova/config/file/store.py:151` – Pydantic validation failures untested; no guarantee that `ConfigValidationError.field/message` remain stable.

## Medium Priority Gaps
- `src/nova/config/file/store.py:137` – Blank YAML (`None` root) fallback to `{}` not asserted.
- `src/nova/config/resolver.py:28,31` – Guards that skip malformed `NOVA_CONFIG__` keys lack coverage.
- `src/nova/config/file/paths.py:39,42-43` – `_normalize_start_dir` resilience for file inputs and `Path.resolve` failures untested.
- `src/nova/config/merger.py:86` – `_extract_marketplace_name` path for Pydantic marketplace objects unverified.

## Low Priority Gaps
- `src/nova/config/file/paths.py:58` – `_resolve_project_configs` returning `(None, None)` when `.nova/` is absent should be locked in with a focused test.

## Test Quality Notes
- `tests/unit/config/test_file_config_store.py` covers cross-scope merging but leans on monkeypatching private methods; consider smaller unit tests for `_load_scope_config`.
- Resolver tests (`tests/unit/config/test_resolver.py`) miss malformed env-key scenarios discussed above.
- No direct tests for `discover_config_paths`; path normalization behaviors surface only through store integration tests.

## Recommended Actions
1. Add fast unit tests hitting the missing error branches in `_load_scope_config` (file disappearance, schema violations, blank YAML handling).
2. Extend resolver tests to assert malformed env keys are ignored and don’t corrupt overrides.
3. Introduce focused tests for `discover_config_paths` edge cases (`working_dir` as file, `Path.resolve` failure, missing `.nova/`).
4. Cover marketplace merge behavior using `MarketplaceConfig` instances to prove `_extract_marketplace_name` handles object entries.
