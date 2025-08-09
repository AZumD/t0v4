"""Custom exception types for TOVA v4."""


class TovaError(Exception):
    """Base exception for TOVA-specific errors."""


class ConfigurationError(TovaError):
    """Raised when configuration is missing or invalid."""


class PluginError(TovaError):
    """Raised for plugin-related failures.""" 