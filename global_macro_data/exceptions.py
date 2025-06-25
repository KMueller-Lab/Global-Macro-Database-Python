INTRO = (
    "\nGlobal Macro Database by Müller et al. (2025)\n"
    "Website: https://www.globalmacrodata.com\n\n"
)


class InvalidVariableError(ValueError):
    """Raised when one or more variable codes are invalid."""

    def __init__(self, invalid_vars: list[str]):
        self.invalid_vars = invalid_vars

        # Format variable list nicely
        if len(invalid_vars) == 1:
            var_list = invalid_vars[0]
            var_intro = "Invalid variable code"
        else:
            var_list = ', '.join(invalid_vars)
            var_intro = "Invalid variable codes"

        message = (
            INTRO +
            f"{var_intro}: {var_list}\n\n"
            "To see the list of valid variable codes, "
            "use: gmd.list_variables()"
        )

        super().__init__(message)


class InvalidVersionError(ValueError):
    """Raised when a requested dataset version does not exist."""

    def __init__(
        self, requested_version: str,
        available: list[str],
        current: str
    ):

        self.requested_version = requested_version
        self.available_versions = available
        self.current_version = current

        message = (
            INTRO +
            f"Error: '{requested_version}' is not a valid dataset version.\n"
            f"Available versions: {', '.join(available)}\n"
            f"Current version: {current}"
        )
        super().__init__(message)


class RawModeError(ValueError):
    """Raised when raw=True is used incorrectly."""

    def __init__(self):
        message = (
            INTRO +
            "'raw=True' requires specifying exactly one variable.\n"
            "Raw data is only accessed variable-wise using: "
            "gmd(variable, raw=True)\n"
            "For full documentation: https://www.globalmacrodata.com/GMD.xlsx"
        )
        super().__init__(message)


class DataDownloadError(ConnectionError):
    """Raised when data cannot be downloaded from the remote source."""

    def __init__(self, original_exception: Exception):
        message = (
            INTRO +
            f"Error downloading data:\n{original_exception}"
        )
        super().__init__(message)
        self.original_exception = original_exception


class InvalidCountryError(ValueError):
    """Raised when one or more country codes are invalid."""

    def __init__(self, invalid_codes: list[str]):
        self.invalid_codes = invalid_codes

        if len(invalid_codes) == 1:
            msg = f"Invalid country code: '{invalid_codes[0]}'"
        else:
            msg = f"Invalid country codes: {', '.join(invalid_codes)}"

        message = (
            INTRO +
            f"{msg}\n\n"
            "To see the list of valid country codes, use: gmd.list_countries()"
        )
        super().__init__(message)
