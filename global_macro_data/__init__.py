from .gmd import (
    GMDCommandError,
    PACKAGE_VERSION,
    gmd,
    get_available_versions,
    get_current_version,
    list_variables,
    list_countries,
    VALID_VARIABLES,
)

__version__ = PACKAGE_VERSION

__all__ = [
    "gmd",
    "GMDCommandError",
    "__version__",
    "get_available_versions",
    "get_current_version",
    "list_variables",
    "list_countries",
    "VALID_VARIABLES",
]
