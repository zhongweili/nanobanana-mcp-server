"""Custom exceptions for the Nano Banana MCP Server."""


class NanoBananaError(Exception):
    """Base exception class for all Nano Banana errors."""

    pass


class ConfigurationError(NanoBananaError):
    """Raised when there's a configuration issue."""

    pass


class ValidationError(NanoBananaError):
    """Raised when input validation fails."""

    pass


class GeminiAPIError(NanoBananaError):
    """Raised when Gemini API calls fail."""

    pass


class ImageProcessingError(NanoBananaError):
    """Raised when image processing fails."""

    pass


class FileOperationError(NanoBananaError):
    """Raised when file operations fail."""

    pass
