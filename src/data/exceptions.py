"""Domain errors raised while loading or querying commercial data."""


class DataValidationError(ValueError):
    """Raised when a source CSV is missing required data or has invalid values."""


class IdentityVerificationRequiredError(PermissionError):
    """Raised when a protected order query lacks trusted identity context."""
