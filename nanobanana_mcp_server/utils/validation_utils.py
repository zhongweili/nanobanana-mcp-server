"""Additional validation utilities beyond core validation."""

from typing import Any, List, Optional, Union
import re
import os
from urllib.parse import urlparse
from ..core.exceptions import ValidationError


def validate_display_name(display_name: str) -> None:
    """Validate file display name."""
    if not display_name or not display_name.strip():
        raise ValidationError("Display name cannot be empty")

    if len(display_name) > 256:
        raise ValidationError("Display name too long (max 256 characters)")

    # Check for invalid characters
    invalid_chars = ["<", ">", ":", '"', "|", "?", "*", "\\", "/"]
    for char in invalid_chars:
        if char in display_name:
            raise ValidationError(f"Display name contains invalid character: {char}")


def validate_positive_integer(
    value: Any, name: str, min_value: int = 1, max_value: Optional[int] = None
) -> None:
    """Validate that a value is a positive integer within bounds."""
    if not isinstance(value, int):
        raise ValidationError(f"{name} must be an integer")

    if value < min_value:
        raise ValidationError(f"{name} must be at least {min_value}")

    if max_value and value > max_value:
        raise ValidationError(f"{name} must be at most {max_value}")


def validate_string_length(
    value: str, name: str, min_length: int = 0, max_length: Optional[int] = None
) -> None:
    """Validate string length."""
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a string")

    if len(value) < min_length:
        raise ValidationError(f"{name} must be at least {min_length} characters")

    if max_length and len(value) > max_length:
        raise ValidationError(f"{name} must be at most {max_length} characters")


def validate_email(email: str) -> None:
    """Validate email address format."""
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email address format")


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> None:
    """Validate URL format and scheme."""
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValidationError("Invalid URL format")

        if allowed_schemes and parsed.scheme not in allowed_schemes:
            raise ValidationError(f"URL scheme must be one of: {', '.join(allowed_schemes)}")

    except Exception as e:
        raise ValidationError(f"Invalid URL: {e}")


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> None:
    """Validate file extension."""
    if not filename:
        raise ValidationError("Filename cannot be empty")

    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in [ext.lower() for ext in allowed_extensions]:
        raise ValidationError(f"File extension must be one of: {', '.join(allowed_extensions)}")


def validate_json_structure(
    data: Any, required_fields: List[str], optional_fields: Optional[List[str]] = None
) -> None:
    """Validate JSON structure has required fields."""
    if not isinstance(data, dict):
        raise ValidationError("Data must be a JSON object")

    # Check required fields
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)

    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    # Check for unexpected fields
    if optional_fields is not None:
        allowed_fields = set(required_fields + optional_fields)
        unexpected_fields = set(data.keys()) - allowed_fields
        if unexpected_fields:
            raise ValidationError(f"Unexpected fields: {', '.join(unexpected_fields)}")


def validate_color_hex(color: str) -> None:
    """Validate hex color format."""
    hex_pattern = r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
    if not re.match(hex_pattern, color):
        raise ValidationError("Invalid hex color format (expected #RRGGBB or #RGB)")


def validate_aspect_ratio(
    width: int, height: int, min_ratio: float = 0.1, max_ratio: float = 10.0
) -> None:
    """Validate aspect ratio is within reasonable bounds."""
    if width <= 0 or height <= 0:
        raise ValidationError("Width and height must be positive")

    ratio = width / height
    if ratio < min_ratio or ratio > max_ratio:
        raise ValidationError(
            f"Aspect ratio {ratio:.2f} is outside valid range ({min_ratio}-{max_ratio})"
        )


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing/replacing invalid characters."""
    # Remove path separators
    filename = os.path.basename(filename)

    # Replace invalid characters with underscores
    invalid_chars = '<>:"|?*\\'
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Ensure it's not empty
    if not filename:
        filename = "untitled"

    return filename


def validate_content_type(content_type: str, allowed_types: List[str]) -> None:
    """Validate content type against allowed types."""
    if not content_type:
        raise ValidationError("Content type cannot be empty")

    # Normalize content type (remove charset, etc.)
    main_type = content_type.split(";")[0].strip().lower()

    if main_type not in [t.lower() for t in allowed_types]:
        raise ValidationError(
            f"Content type '{main_type}' not allowed. Allowed types: {', '.join(allowed_types)}"
        )


def validate_rate_limit_params(requests: int, period_seconds: int) -> None:
    """Validate rate limiting parameters."""
    validate_positive_integer(requests, "requests", min_value=1, max_value=10000)
    validate_positive_integer(period_seconds, "period_seconds", min_value=1, max_value=86400)


def validate_pagination_params(page: int, limit: int, max_limit: int = 100) -> None:
    """Validate pagination parameters."""
    validate_positive_integer(page, "page", min_value=1)
    validate_positive_integer(limit, "limit", min_value=1, max_value=max_limit)


def validate_search_query(query: str, min_length: int = 1, max_length: int = 1000) -> None:
    """Validate search query."""
    validate_string_length(query.strip(), "search query", min_length, max_length)

    # Check for SQL injection patterns
    dangerous_patterns = [
        r"\b(union|select|insert|update|delete|drop|create|alter)\b",
        r'[\'";]',
        r"--",
        r"/\*",
    ]

    query_lower = query.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, query_lower):
            raise ValidationError("Search query contains potentially dangerous characters")


def validate_timeout_seconds(
    timeout: Union[int, float], min_timeout: float = 0.1, max_timeout: float = 300.0
) -> None:
    """Validate timeout value in seconds."""
    if not isinstance(timeout, (int, float)):
        raise ValidationError("Timeout must be a number")

    if timeout < min_timeout:
        raise ValidationError(f"Timeout must be at least {min_timeout} seconds")

    if timeout > max_timeout:
        raise ValidationError(f"Timeout must be at most {max_timeout} seconds")


def validate_aspect_ratio_string(aspect_ratio: str) -> None:
    """
    Validate aspect ratio string format and supported values.

    Validates that the aspect ratio string matches one of the values
    supported by the Gemini API.

    Args:
        aspect_ratio: Aspect ratio string (e.g., "16:9", "4:3")

    Raises:
        ValidationError: If aspect ratio is invalid or unsupported

    Supported aspect ratios:
        1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
    """
    if not isinstance(aspect_ratio, str):
        raise ValidationError("Aspect ratio must be a string")

    # Supported aspect ratios according to Gemini API documentation
    # https://ai.google.dev/gemini-api/docs/image-generation#optional_configurations
    SUPPORTED_ASPECT_RATIOS = [
        "1:1", "2:3", "3:2", "3:4", "4:3",
        "4:5", "5:4", "9:16", "16:9", "21:9"
    ]

    if aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
        raise ValidationError(
            f"Unsupported aspect_ratio: '{aspect_ratio}'. "
            f"Supported values: {', '.join(SUPPORTED_ASPECT_RATIOS)}"
        )
