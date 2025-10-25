"""Nova - A modular CLI tool and library for development workflows.

By default, Nova's internal logging is disabled when used as a library.
Library users can enable logging by calling nova.enable_logging().
"""

from nova.common import disable_library_logging, enable_library_logging

disable_library_logging()

enable_logging = enable_library_logging

__all__ = [
    "enable_logging",
]
