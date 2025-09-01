"""Input validation utilities."""

from typing import List, Optional
import re
from ..config.constants import SUPPORTED_IMAGE_TYPES
from .exceptions import ValidationError


def validate_prompt(prompt: str) -> None:
    """Validate image generation prompt."""
    if not prompt or not prompt.strip():
        raise ValidationError("Prompt cannot be empty")

    if len(prompt) > 8192:
        raise ValidationError("Prompt too long (max 8192 characters)")

    # Check for potentially harmful content patterns
    harmful_patterns = [
        r"\b(?:nude|naked|nsfw)\b",
        r"\b(?:violence|gore|blood)\b",
        r"\b(?:hate|racist|offensive)\b",
    ]

    for pattern in harmful_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            raise ValidationError("Prompt contains potentially inappropriate content")


def validate_image_count(n: int) -> None:
    """Validate requested image count."""
    if not isinstance(n, int):
        raise ValidationError("Image count must be an integer")

    if n < 1 or n > 4:
        raise ValidationError("Image count must be between 1 and 4")


def validate_image_format(mime_type: str) -> None:
    """Validate image MIME type."""
    if not mime_type:
        raise ValidationError("MIME type cannot be empty")

    if mime_type.lower() not in SUPPORTED_IMAGE_TYPES:
        raise ValidationError(
            f"Unsupported image format: {mime_type}. "
            f"Supported types: {', '.join(SUPPORTED_IMAGE_TYPES)}"
        )


def validate_base64_image(image_b64: str) -> None:
    """Validate base64 encoded image."""
    if not image_b64:
        raise ValidationError("Base64 image data cannot be empty")

    try:
        import base64

        base64.b64decode(image_b64, validate=True)
    except Exception as e:
        raise ValidationError(f"Invalid base64 image data: {e}")


def validate_image_list_consistency(
    images_b64: Optional[List[str]], mime_types: Optional[List[str]]
) -> None:
    """Validate that image lists are consistent."""
    if images_b64 is None and mime_types is None:
        return

    if images_b64 is None or mime_types is None:
        raise ValidationError("Both images_b64 and mime_types must be provided together")

    if len(images_b64) != len(mime_types):
        raise ValidationError(
            f"images_b64 ({len(images_b64)}) and mime_types ({len(mime_types)}) "
            "must have the same length"
        )

    if len(images_b64) > 4:
        raise ValidationError("Maximum 4 input images allowed")

    # Validate each image and MIME type
    for i, (img_b64, mime_type) in enumerate(zip(images_b64, mime_types)):
        try:
            validate_base64_image(img_b64)
            validate_image_format(mime_type)
        except ValidationError as e:
            raise ValidationError(f"Invalid image {i + 1}: {e}")


def validate_file_path(path: str) -> None:
    """Validate file path for uploads."""
    if not path or not path.strip():
        raise ValidationError("File path cannot be empty")

    # Basic path traversal protection
    if ".." in path or path.startswith("/"):
        raise ValidationError("Invalid file path: potential security risk")

    import os

    if not os.path.exists(path):
        raise ValidationError(f"File not found: {path}")

    if not os.path.isfile(path):
        raise ValidationError(f"Path is not a file: {path}")


def validate_edit_instruction(instruction: str) -> None:
    """Validate image edit instruction."""
    if not instruction or not instruction.strip():
        raise ValidationError("Edit instruction cannot be empty")

    if len(instruction) > 2048:
        raise ValidationError("Edit instruction too long (max 2048 characters)")

    # Check for harmful edit instructions
    harmful_patterns = [
        r"\b(?:remove|delete)\s+(?:clothes|clothing)\b",
        r"\b(?:add|create)\s+(?:nude|naked|nsfw)\b",
    ]

    for pattern in harmful_patterns:
        if re.search(pattern, instruction, re.IGNORECASE):
            raise ValidationError("Edit instruction contains inappropriate content")
