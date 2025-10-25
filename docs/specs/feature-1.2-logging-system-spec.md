---
status: draft
priority: p2
created: "2025-10-24"
---

# Feature 1.2: Logging System - Technical Specification

**Status:** 🚧 Draft
**Priority:** P2 (Should Have - Foundation for debugging and monitoring)
**Created:** 2025-10-24

## Overview

This specification defines Nova's logging system design that supports both CLI and library usage contexts. The system must provide detailed diagnostic logs for CLI users while remaining unobtrusive for library integrators.

### Goals

- Provide file-based logging for CLI users with rotation and retention
- Default to disabled logging for library usage (Loguru best practice)
- Support configurable log levels, formats, and output destinations
- Enable structured logging (JSON) for parsing and monitoring
- Follow XDG Base Directory specification for log file storage

### Non-Goals

- Real-time log streaming or tailing features
- Log aggregation or centralized logging infrastructure
- Performance profiling or metrics collection
- User-visible terminal output (logs are background diagnostic data)

## Design Philosophy

- **Library-first**: Logging disabled by default; library users opt-in explicitly
- **CLI convenience**: CLI automatically enables file logging without user intervention
- **Separation of concerns**: Logs are for developers/debugging, not end-user messages
- **Human-readable logs**: Default to text format for easy reading; JSON available for structured parsing
- **XDG compliant**: Logs stored in `~/.local/share/nova/logs/` (data directory)

## Architecture

### Current State

Nova already has Loguru configured in `src/nova/utils/logging.py`:
- ✅ `setup_logging(config)` - Configures logger with dev/prod modes
- ✅ `create_logger(scope)` - Creates scoped loggers for different modules
- ✅ Environment-based formatting (colorized dev, JSON prod)
- ❌ Not currently used anywhere in the codebase

### Proposed Changes

Following ADR-001 (CLI/Business Logic Separation):
- **Core modules**: Use standard logger calls (`logger.info()`, `logger.debug()`, etc.)
- **CLI layer**: Configures logging sinks (file paths, rotation, format)
- **Library mode**: Logging disabled by default via `logger.disable("nova")`

## Configuration

### Logging Configuration Model

**Important:**
- Logging configuration is **global-only**. It should only be present in the global config file (`~/.config/nova/config.yaml`), not in project or user configs.
- `LoggingConfig` is defined in the **config module**, not the logging module, to avoid forcing loguru as a dependency for library users who only use config models.

**Location:** `src/nova/config/models.py`

```python
@dataclass(kw_only=True)
class LoggingConfig:
    """Logging configuration for Nova.

    Attributes:
        enabled: Whether logging is enabled
        log_level: Minimum severity level to log
        log_file: Path to log file (None = XDG default)
        rotation: When to rotate log files
        retention: How long to keep old log files
        format: Log format (json or text)
    """
    enabled: bool = Field(default=True)
    log_level: Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    log_file: str | None = Field(default=None)  # None uses XDG default
    rotation: str = Field(default="10 MB")  # "10 MB", "daily", "weekly", "1 day"
    retention: str = Field(default="7 days")  # "7 days", "10" (number of files)
    format: Literal["json", "text"] = Field(default="text")
```

**Integration with NovaConfig:**

In the same file (`src/nova/config/models.py`):

```python
@dataclass(kw_only=True)
class NovaConfig:
    # ... existing fields ...
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
```

**Why in config module, not logging module:**
- Config models should not depend on loguru
- Library users who import `NovaConfig` shouldn't be forced to install loguru
- Only code that actually uses logging functions (like `setup_cli_logging()`) needs loguru
- This keeps dependencies minimal for library users

### User Configuration

Users can configure logging **only in the global config** (`~/.config/nova/config.yaml`).

**Note:** Logging configuration is global-only and cannot be set in project (`.nova/config.yaml`) or user configs. This ensures consistent logging behavior across all projects on the system.

```yaml
logging:
  enabled: true
  log_level: "INFO"
  log_file: "~/.local/share/nova/logs/nova.log"  # Optional override
  rotation: "10 MB"
  retention: "7 days"
  format: "text"  # or "json" for structured logging
```

**Default behavior (no config):**
- Enabled: `true`
- Level: `INFO`
- File: `~/.local/share/nova/logs/nova.log`
- Rotation: `10 MB`
- Retention: `7 days`
- Format: `text`

## Implementation

### 1. Core Logging Utilities

**Location:** `src/nova/utils/logging.py`

**Imports:**
```python
from loguru import logger
from pathlib import Path
import sys

from nova.config.models import LoggingConfig  # Import config from config module
from nova.settings import AppInfo
from nova.utils import PathsConfig
```

**Note:** `LoggingConfig` is defined in `src/nova/config/models.py`, not here. The logging module imports it to use in function signatures.

**New functions:**

```python
def setup_cli_logging(app_info: AppInfo, config: LoggingConfig, paths: PathsConfig) -> int:
    """Setup file-based logging for CLI usage.

    Configures Loguru with file sink, rotation, and retention
    based on user configuration. Returns handler ID for later removal.

    Args:
        app_info: Application metadata
        config: Logging configuration
        paths: Path configuration for determining log file location

    Returns:
        Handler ID from logger.add()
    """
    ...

def disable_library_logging() -> None:
    """Disable Nova logging for library usage.

    Should be called in nova/__init__.py to ensure Nova doesn't
    emit logs by default when used as a library.
    """
    logger.disable("nova")

def enable_library_logging(level: str = "INFO") -> int:
    """Enable Nova logging for library users.

    Helper function for library users who want to see Nova's logs.
    Configures stderr output with specified level.

    Args:
        level: Minimum log level to emit

    Returns:
        Handler ID from logger.add()

    Example:
        >>> import nova
        >>> nova.enable_logging("DEBUG")
    """
    ...

def get_default_log_file_path(paths: PathsConfig) -> Path:
    """Get default log file path following XDG spec.

    Returns: ~/.local/share/nova/logs/nova.log
    """
    ...
```

**Update existing:**

```python
def setup_logging(config: LoggingConfig) -> None:
    """Setup the default logger.

    DEPRECATED: Use setup_cli_logging() for CLI or disable_library_logging() for library.
    This function remains for backward compatibility.
    """
    ...
```

### 2. CLI Integration

**Location:** `src/nova/cli/main.py` (or wherever CLI is initialized)

```python
from nova.utils.logging import setup_cli_logging, create_logger
from nova.settings import settings
from nova.config.file import FileConfigStore

logger = create_logger("cli")

def main():
    """Main CLI entry point."""
    # Load ONLY global config for logging configuration
    # (logging cannot be configured in project/user configs)
    config_store = FileConfigStore(paths=settings.to_file_config_paths())
    global_config_result = config_store.load_global()

    if is_err(global_config_result):
        # No global config or error - use defaults
        logging_config = LoggingConfig()
    else:
        global_config = global_config_result.unwrap()
        logging_config = global_config.logging

    # Setup logging for CLI
    if logging_config.enabled:
        setup_cli_logging(
            app_info=settings.app,
            config=logging_config,
            paths=settings.to_paths_config()
        )
        logger.debug("CLI logging initialized", config=logging_config)

    # Continue with CLI...
```

**Key points:**
- Only load global config for logging configuration
- If global config doesn't exist or fails to load, use `LoggingConfig()` defaults
- Don't merge logging config from project/user scopes

### 3. Library Integration

**Location:** `src/nova/__init__.py`

```python
from nova.utils.logging import disable_library_logging, enable_library_logging

# Disable logging by default for library usage
disable_library_logging()

# Export helper for library users
__all__ = [
    # ... existing exports ...
    "enable_logging",
]

# Convenience alias
enable_logging = enable_library_logging
```

### 4. Core Module Usage

**Pattern for all core modules:**

```python
# src/nova/marketplace/api.py
from nova.utils.logging import create_logger

logger = create_logger("marketplace")

class Marketplace:
    def sync(self) -> Result[None, MarketplaceError]:
        logger.info("Starting marketplace sync", marketplace_count=len(self._sources))

        for source in self._sources:
            logger.debug("Processing marketplace", source=source.name, url=source.url)

            result = self._clone_repository(source.url)
            if is_err(result):
                logger.error("Failed to clone marketplace",
                           source=source.name,
                           error=str(result.unwrap_err()))
                return result

            logger.success("Marketplace synced", source=source.name)

        logger.info("Marketplace sync completed")
        return Ok(None)
```

**Logging conventions:**
- Use structured logging: `logger.info("message", key=value, ...)`
- Include context: module name, operation, relevant IDs
- Use appropriate levels:
  - `TRACE`: Very detailed debugging (e.g., loop iterations)
  - `DEBUG`: Detailed debugging (e.g., function calls, state changes)
  - `INFO`: General informational messages (e.g., operations starting/completing)
  - `SUCCESS`: Successful completion of significant operations
  - `WARNING`: Recoverable issues or deprecated usage
  - `ERROR`: Errors that prevent operation completion
  - `CRITICAL`: System-level failures requiring immediate attention

## Log File Management

### Directory Structure

Following ADR-003 (XDG Base Directory):

```
~/.local/share/nova/logs/
├── nova.log                    # Current log file
├── nova.2024-10-23.log        # Rotated log
├── nova.2024-10-22.log
└── nova.2024-10-21.log
```

### Rotation Strategies

Log rotation creates a new log file when certain conditions are met. The current log file is renamed with a timestamp, and a fresh `nova.log` is created.

**Supported rotation strategies:**

**1. By Size** (recommended for most users)
```yaml
rotation: "10 MB"    # Rotate when file reaches 10 MB (default)
rotation: "500 KB"   # Rotate when file reaches 500 KB
rotation: "1 GB"     # Rotate when file reaches 1 GB
```

When the log file reaches the specified size, it's rotated:
- Current: `nova.log` (10 MB) → Renamed to: `nova.2024-10-24_14-30-00.log`
- New file: `nova.log` (empty) is created

**2. By Time** (for regular intervals)
```yaml
rotation: "daily"     # Rotate at midnight each day
rotation: "weekly"    # Rotate every Monday at midnight
rotation: "00:00"     # Rotate at midnight (same as "daily")
rotation: "1 week"    # Rotate every 7 days
rotation: "1 day"     # Rotate every 24 hours
```

When the time condition is met:
- Current: `nova.log` → Renamed to: `nova.2024-10-24.log`
- New file: `nova.log` (empty) is created

**Note:** These are the only rotation strategies supported through configuration. Custom rotation logic is not supported.

### Retention Policies

**By count:**
```yaml
retention: 10         # Keep last 10 rotated files
```

**By age:**
```yaml
retention: "7 days"   # Delete files older than 7 days
retention: "2 weeks"  # Delete files older than 2 weeks
```


## Log Formats

### Text Format (default)

Human-readable format for easy reading and debugging:

```
2024-10-24 14:20:00 | INFO     | marketplace:sync:42 - Starting marketplace sync | marketplace_count=3
2024-10-24 14:20:01 | DEBUG    | marketplace:_clone:78 - Processing marketplace | source=official url=https://github.com/...
2024-10-24 14:20:05 | SUCCESS  | marketplace:sync:56 - Marketplace synced | source=official
```

### JSON Format

Structured JSON for parsing, tooling, and programmatic analysis:

```json
{
  "text": "Starting marketplace sync",
  "record": {
    "time": {"timestamp": 1729785600.123},
    "level": {"name": "INFO", "no": 20},
    "message": "Starting marketplace sync",
    "extra": {
      "scope": "marketplace",
      "marketplace_count": 3
    },
    "name": "nova.marketplace.api",
    "function": "sync",
    "line": 42,
    "file": {"name": "api.py", "path": "/path/to/nova/marketplace/api.py"},
    "thread": {"id": 12345, "name": "MainThread"},
    "process": {"id": 67890, "name": "MainProcess"}
  }
}
```


## Environment-Specific Behavior

### Development (`NOVA_APP__ENVIRONMENT=dev`)
- Default level: `DEBUG`
- Format: `text` (human-readable)

### Production (`NOVA_APP__ENVIRONMENT=prod`)
- Default level: `INFO`
- Format: `text` (can be changed to `json` for log aggregation)

**Note:** Users can override format to `json` in any environment if they need structured logging for parsing/analysis.

### Testing (`NOVA_APP__ENVIRONMENT=test`)
- Logging disabled by default
- Can be enabled for test debugging

## Configuration Management

Logging configuration is managed through the global config file (`~/.config/nova/config.yaml`). Users edit this file directly to change logging settings.

**Example global config:**
```yaml
# ~/.config/nova/config.yaml
logging:
  enabled: true
  log_level: "INFO"
  log_file: null  # Use default XDG path
  rotation: "10 MB"
  retention: "7 days"
  format: "text"
```

**To change log level:** Edit `~/.config/nova/config.yaml` and change `log_level: "DEBUG"`

**To disable logging:** Edit `~/.config/nova/config.yaml` and change `enabled: false`

**Note:** Changes take effect the next time Nova CLI is invoked. There are no CLI commands for managing logging configuration.

## Library Usage Examples

### Basic Usage (Logging Disabled by Default)

```python
import nova
from nova.marketplace import Marketplace

# Nova's internal logs are disabled by default
# Your application logs are unaffected
marketplace = Marketplace(config_provider=...)
marketplace.sync()  # No Nova logs emitted
```

### Enabling Nova Logs

```python
import nova
from nova.marketplace import Marketplace

# Enable Nova's logs to stderr
nova.enable_logging("DEBUG")

marketplace = Marketplace(config_provider=...)
marketplace.sync()  # Nova logs now visible on stderr
```

### Custom Log Configuration

```python
import nova
# Note: If you need direct loguru access, import it at the top of your file
# from loguru import logger

# Disable Nova's default logging
# (already disabled, but showing explicit control)

# Enable Nova's logger with custom sink
# (assuming you imported logger above)
logger.enable("nova")
logger.add(
    "my_app_logs/nova.log",
    filter=lambda record: record["name"].startswith("nova"),
    level="INFO",
    rotation="1 day"
)

# Now Nova logs go to your custom file
marketplace = Marketplace(config_provider=...)
marketplace.sync()
```

## Testing

### Unit Tests

**Location:** `tests/unit/utils/test_logging.py`

```python
def test_setup_cli_logging_creates_log_file(tmp_path):
    """Test that CLI logging creates log file."""
    ...

def test_setup_cli_logging_respects_level():
    """Test that log level configuration is respected."""
    ...

def test_disable_library_logging():
    """Test that library logging is disabled."""
    ...

def test_enable_library_logging():
    """Test that library logging can be re-enabled."""
    ...

def test_log_rotation_by_size():
    """Test that logs rotate when reaching size threshold."""
    ...

def test_log_retention_removes_old_files():
    """Test that old log files are removed per retention policy."""
    ...

def test_text_format_is_human_readable():
    """Test that text format is human-readable."""
    ...

def test_json_format_is_valid_json():
    """Test that JSON format produces parseable JSON."""
    ...
```

### Integration Tests

**Location:** `tests/integration/test_logging.py`

```python
def test_cli_logging_end_to_end():
    """Test that CLI commands produce log entries."""
    ...

def test_library_mode_no_logs_by_default():
    """Test that library usage doesn't emit logs."""
    ...

def test_log_file_creation_in_xdg_directory():
    """Test that log file is created in correct XDG location."""
    ...
```

## Error Handling

### Permission Errors

If log directory is not writable:
```python
# Log to stderr instead and warn user
logger.warning(
    "Cannot write to log file, logging to stderr",
    log_path=log_path,
    error=str(error)
)
```

### Disk Space Issues

If disk is full during rotation:
- Loguru handles this gracefully by keeping current file open
- Warning logged to stderr if possible

### Invalid Configuration

If logging config is invalid:
```python
# Fall back to defaults
logger.warning(
    "Invalid logging configuration, using defaults",
    config=config,
    error=str(error)
)
```

### Logging Config in Wrong Scope

If logging configuration is found in project or user config:
```python
# This should be caught during config validation
# and produce a clear error message
raise ConfigError(
    "Logging configuration can only be set in global config (~/.config/nova/config.yaml). "
    "Found logging configuration in project/user config which is not allowed."
)
```

## Performance Considerations

### Asynchronous Logging

For high-throughput scenarios, enable async logging:

```python
logger.add(
    log_file,
    enqueue=True,  # Enable async logging via queue
    level=config.log_level,
)
```

### Lazy Evaluation

For expensive log message formatting:

```python
# Only compute expensive_function() if DEBUG level is active
logger.opt(lazy=True).debug(
    "Expensive computation: {result}",
    result=lambda: expensive_function()
)
```

### Filtering at Source

Use filters to prevent unnecessary log processing:

```python
logger.add(
    log_file,
    filter=lambda record: record["level"].no >= 20,  # INFO and above
)
```

## Security Considerations

### Sensitive Data

**Never log:**
- Passwords or API keys
- Personal identifiable information (PII)
- Authentication tokens
- Private repository contents

**Safe to log:**
- Operation names and status
- Non-sensitive configuration values
- Error types and codes (not full error messages if they contain secrets)
- Timing information

### Diagnose Mode

Loguru's `diagnose=True` shows variable values in tracebacks. This is useful for development but **must be disabled in production**:

```python
# In setup_cli_logging()
diagnose = app_info.environment == "dev"
logger.add(log_file, diagnose=diagnose)
```

## Migration Path

### Phase 1: Foundation (This Spec)
1. Add `LoggingConfig` to config models (global-only)
2. Implement `setup_cli_logging()`, `disable_library_logging()`, `enable_library_logging()`
3. Integrate logging into CLI main entry point (load from global config only)
4. Disable logging in `nova/__init__.py` for library mode
5. Add validation to prevent logging config in project/user scopes

### Phase 2: Module Integration
1. Add logging to `nova.marketplace` module
2. Add logging to `nova.config` module
3. Add logging to other core modules as developed

### Phase 3: Enhancement
1. Add CLI command: `nova logs tail` (optional)
2. Add CLI command: `nova logs clear` (optional)
3. Add log parsing utilities for debugging (optional)

## Dependencies

- **Loguru**: Already installed and configured
- **Feature 1 (Config Management)**: Required for configuration loading
- **ADR-003 (XDG Directories)**: Defines log file location

## Future Enhancements

Potential future additions (not in this spec):

- CLI commands: `nova logs show`, `nova logs tail`, `nova logs clear`
- CLI command: `nova config set logging.log_level DEBUG` (config management commands)
- Log parsing utilities for JSON format
- Structured log filtering by module/level
- Log export to common formats (CSV, etc.)
- Integration with external logging services (optional)

## References

- [ADR-001: CLI and Business Logic Separation](../architecture/adr-001-cli-business-logic-separation.md)
- [ADR-003: XDG Base Directory Structure](../architecture/adr-003-xdg-directory-structure.md)
- [Loguru Documentation](https://loguru.readthedocs.io/)
- [Feature 1 Specification](./feature-1-config-management-spec.md)
