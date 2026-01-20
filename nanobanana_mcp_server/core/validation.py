"""Input validation utilities."""

from typing import Dict, List, Optional, Tuple, Union
import re
from ..config.constants import (
    SUPPORTED_IMAGE_TYPES,
    RESOLUTION_PRESETS,
    MIN_ASPECT_RATIO,
    MAX_ASPECT_RATIO,
    BYTES_PER_PIXEL_RGBA,
    IMAGE_OVERHEAD_MULTIPLIER,
)
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


def validate_resolution(
    resolution: Union[str, Dict, List, None],
    model_tier: str,
    max_flash: int = 2048,
    max_pro: int = 3840
) -> None:
    """Validate resolution parameter format and values.

    Args:
        resolution: Resolution specification in various formats
        model_tier: Model tier ("flash" or "pro")
        max_flash: Maximum resolution for Flash model
        max_pro: Maximum resolution for Pro model

    Raises:
        ValidationError: If resolution is invalid
    """
    if resolution is None:
        return

    # String preset validation
    if isinstance(resolution, str):
        # Check if it's a valid preset or dimension string
        if resolution not in RESOLUTION_PRESETS and "x" not in resolution:
            if resolution not in ["high", "medium", "low", "original", "1024", "4k", "2k", "1k"]:
                raise ValidationError(f"Invalid resolution preset: {resolution}")

    # Dictionary validation
    elif isinstance(resolution, dict):
        if "width" in resolution and "height" in resolution:
            validate_dimensions(resolution["width"], resolution["height"])
        elif "aspect_ratio" in resolution:
            if "target_size" not in resolution and "max_dimension" not in resolution:
                raise ValidationError(
                    "aspect_ratio requires either target_size or max_dimension"
                )
        else:
            raise ValidationError(
                "Dictionary resolution must have either width/height or aspect_ratio"
            )

    # List validation
    elif isinstance(resolution, list):
        if len(resolution) != 2:
            raise ValidationError("List resolution must have exactly 2 elements [width, height]")
        validate_dimensions(resolution[0], resolution[1])

    else:
        raise ValidationError(f"Invalid resolution type: {type(resolution)}")


def validate_dimensions(width: int, height: int) -> None:
    """Validate image dimensions.

    Args:
        width: Image width in pixels
        height: Image height in pixels

    Raises:
        ValidationError: If dimensions are invalid
    """
    if not isinstance(width, int) or not isinstance(height, int):
        raise ValidationError("Dimensions must be integers")

    if width <= 0 or height <= 0:
        raise ValidationError("Dimensions must be positive")

    if width > 3840 or height > 3840:
        raise ValidationError("Maximum dimension is 3840 pixels")

    # Check aspect ratio
    aspect_ratio = width / height
    if aspect_ratio < MIN_ASPECT_RATIO or aspect_ratio > MAX_ASPECT_RATIO:
        raise ValidationError(
            f"Aspect ratio {aspect_ratio:.2f} outside valid range "
            f"({MIN_ASPECT_RATIO}-{MAX_ASPECT_RATIO})"
        )


def validate_memory_constraints(
    width: int,
    height: int,
    format: str = "png",
    limit_mb: int = 2048
) -> None:
    """Validate that image won't exceed memory constraints.

    Args:
        width: Image width
        height: Image height
        format: Image format
        limit_mb: Memory limit in MB

    Raises:
        ValidationError: If memory usage would exceed limit
    """
    # Estimate memory usage
    bytes_per_pixel = BYTES_PER_PIXEL_RGBA if format in ["png", "webp"] else 3

    estimated_bytes = width * height * bytes_per_pixel * IMAGE_OVERHEAD_MULTIPLIER
    estimated_mb = estimated_bytes / (1024 * 1024)

    if estimated_mb > limit_mb:
        raise ValidationError(
            f"Estimated memory usage ({estimated_mb:.1f}MB) exceeds limit ({limit_mb}MB)"
        )
