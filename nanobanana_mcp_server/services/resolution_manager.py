"""Resolution management and validation service for image generation.

This module provides centralized resolution handling, validation, and optimization
for both Flash and Pro models, supporting multiple input formats and memory constraints.
"""

import logging
import re

from ..config.constants import (
    BYTES_PER_PIXEL_RGBA,
    IMAGE_OVERHEAD_MULTIPLIER,
    MAX_ASPECT_RATIO,
    MEMORY_BUFFER_PERCENT,
    MIN_ASPECT_RATIO,
    RESOLUTION_PRESETS,
)
from ..config.settings import ResolutionConfig
from ..core.exceptions import ValidationError
from ..services.model_selector import ModelTier


class ResolutionManager:
    """Centralized resolution handling and validation service.

    Manages resolution parsing, validation, conversion between formats,
    and memory estimation for both Flash and Pro models.
    """

    def __init__(self, config: ResolutionConfig | None = None):
        """Initialize with resolution configuration.

        Args:
            config: Resolution configuration. Uses default if not provided.
        """
        self.config = config or ResolutionConfig()
        self.logger = logging.getLogger(__name__)

    def validate_resolution(
        self,
        resolution: str | dict | list | None,
        model_tier: ModelTier,
        prompt_hints: list[str] | None = None,
    ) -> tuple[int, int]:
        """Validate and normalize resolution based on model capabilities.

        Args:
            resolution: Resolution specification in various formats
            model_tier: Model tier (FLASH or PRO)
            prompt_hints: Optional list of resolution hints from prompt

        Returns:
            Tuple of (width, height) after validation

        Raises:
            ValidationError: If resolution is invalid or exceeds limits
        """
        # Parse resolution input
        width, height = self.parse_resolution(resolution, model_tier)

        # Get model limits
        max_res = (
            self.config.pro_max_resolution
            if model_tier == ModelTier.PRO
            else self.config.flash_max_resolution
        )

        # Normalize to fit within limits
        width, height = self.normalize_resolution(width, height, max_res)

        # Check memory constraints
        self._validate_memory_constraints(width, height)

        # Log resolution decision
        self.logger.debug(f"Validated resolution: {width}x{height} for {model_tier.value} model")

        return width, height

    def parse_resolution(
        self, resolution: str | dict | list | None, model_tier: ModelTier | None = None
    ) -> tuple[int, int]:
        """Parse resolution from various input formats.

        Supports:
        - Preset strings: "4k", "2k", "1080p", etc.
        - Dimension specifications: {"width": 3840, "height": 2160}
        - String dimensions: "3840x2160"
        - List dimensions: [3840, 2160]
        - Aspect ratio with target: {"aspect_ratio": "16:9", "target_size": "4k"}

        Args:
            resolution: Resolution specification
            model_tier: Optional model tier for dynamic presets

        Returns:
            Tuple of (width, height)

        Raises:
            ValidationError: If format is invalid
        """
        # Handle None - use default
        if resolution is None:
            resolution = self.config.default_resolution

        # String format
        if isinstance(resolution, str):
            return self._parse_string_resolution(resolution, model_tier)

        # Dictionary format
        elif isinstance(resolution, dict):
            return self._parse_dict_resolution(resolution, model_tier)

        # List format
        elif isinstance(resolution, list):
            return self._parse_list_resolution(resolution)

        else:
            raise ValidationError(f"Invalid resolution type: {type(resolution).__name__}")

    def _parse_string_resolution(
        self, resolution: str, model_tier: ModelTier | None = None
    ) -> tuple[int, int]:
        """Parse string resolution format.

        Args:
            resolution: String resolution (preset or "WxH")
            model_tier: Optional model tier for dynamic presets

        Returns:
            Tuple of (width, height)
        """
        resolution = resolution.lower().strip()

        # Check for dimension format (e.g., "1920x1080")
        if "x" in resolution:
            parts = resolution.split("x")
            if len(parts) != 2:
                raise ValidationError(f"Invalid resolution format: {resolution}")
            try:
                width = int(parts[0].strip())
                height = int(parts[1].strip())
                return width, height
            except ValueError:
                raise ValidationError(f"Invalid resolution dimensions: {resolution}")

        # Check for preset
        if resolution in self.config.presets:
            width, height = self.config.presets[resolution]

            # Handle dynamic presets
            if width == 0 or height == 0:
                return self._get_dynamic_preset(resolution, model_tier)
            return width, height

        # Check for constant presets
        if resolution in RESOLUTION_PRESETS:
            return RESOLUTION_PRESETS[resolution]

        # Special handling for model-specific presets
        if resolution in ["high", "medium", "low", "original"]:
            return self._get_dynamic_preset(resolution, model_tier)

        raise ValidationError(f"Unknown resolution preset: {resolution}")

    def _parse_dict_resolution(
        self, resolution: dict, model_tier: ModelTier | None = None
    ) -> tuple[int, int]:
        """Parse dictionary resolution format.

        Args:
            resolution: Dictionary with width/height or aspect_ratio
            model_tier: Optional model tier for target size

        Returns:
            Tuple of (width, height)
        """
        # Direct width/height specification
        if "width" in resolution and "height" in resolution:
            try:
                width = int(resolution["width"])
                height = int(resolution["height"])
                return width, height
            except (TypeError, ValueError):
                raise ValidationError("Width and height must be integers")

        # Aspect ratio with target size
        elif "aspect_ratio" in resolution:
            return self._parse_aspect_ratio_resolution(resolution, model_tier)

        else:
            raise ValidationError("Dictionary must have either 'width'/'height' or 'aspect_ratio'")

    def _parse_list_resolution(self, resolution: list) -> tuple[int, int]:
        """Parse list resolution format.

        Args:
            resolution: List with [width, height]

        Returns:
            Tuple of (width, height)
        """
        if len(resolution) != 2:
            raise ValidationError("List resolution must have exactly 2 elements")

        try:
            width = int(resolution[0])
            height = int(resolution[1])
            return width, height
        except (TypeError, ValueError):
            raise ValidationError("List elements must be integers")

    def _parse_aspect_ratio_resolution(
        self, resolution: dict, model_tier: ModelTier | None = None
    ) -> tuple[int, int]:
        """Parse aspect ratio with target size.

        Args:
            resolution: Dict with aspect_ratio and target_size/max_dimension
            model_tier: Optional model tier

        Returns:
            Tuple of (width, height)
        """
        aspect_ratio_str = resolution.get("aspect_ratio")
        if not aspect_ratio_str:
            raise ValidationError("aspect_ratio is required")

        # Parse aspect ratio
        if isinstance(aspect_ratio_str, str) and ":" in aspect_ratio_str:
            parts = aspect_ratio_str.split(":")
            try:
                aspect_ratio = float(parts[0]) / float(parts[1])
            except (ValueError, ZeroDivisionError):
                raise ValidationError(f"Invalid aspect ratio: {aspect_ratio_str}")
        else:
            try:
                aspect_ratio = float(aspect_ratio_str)
            except (TypeError, ValueError):
                raise ValidationError(f"Invalid aspect ratio: {aspect_ratio_str}")

        # Validate aspect ratio
        if aspect_ratio < MIN_ASPECT_RATIO or aspect_ratio > MAX_ASPECT_RATIO:
            raise ValidationError(
                f"Aspect ratio {aspect_ratio:.2f} outside valid range "
                f"({MIN_ASPECT_RATIO}-{MAX_ASPECT_RATIO})"
            )

        # Get target dimension
        if "target_size" in resolution:
            target_width, target_height = self.parse_resolution(
                resolution["target_size"], model_tier
            )
            max_dimension = max(target_width, target_height)
        elif "max_dimension" in resolution:
            max_dimension = int(resolution["max_dimension"])
        else:
            raise ValidationError("aspect_ratio requires either 'target_size' or 'max_dimension'")

        # Calculate dimensions maintaining aspect ratio
        if aspect_ratio >= 1:  # Landscape or square
            width = max_dimension
            height = int(max_dimension / aspect_ratio)
        else:  # Portrait
            height = max_dimension
            width = int(max_dimension * aspect_ratio)

        return width, height

    def _get_dynamic_preset(
        self, preset: str, model_tier: ModelTier | None = None
    ) -> tuple[int, int]:
        """Get dynamic preset based on model capabilities.

        Args:
            preset: Preset name (high, medium, low, original)
            model_tier: Model tier

        Returns:
            Tuple of (width, height)
        """
        # Determine max resolution
        if model_tier == ModelTier.PRO:
            max_res = self.config.pro_max_resolution
        elif model_tier == ModelTier.FLASH:
            max_res = self.config.flash_max_resolution
        else:
            # Default to Flash if not specified
            max_res = self.config.flash_max_resolution

        # Calculate based on preset
        if preset == "original" or preset == "high":
            size = max_res
        elif preset == "medium":
            size = int(max_res * 0.5)
        elif preset == "low":
            size = int(max_res * 0.25)
        else:
            size = max_res

        return size, size  # Square by default

    def normalize_resolution(self, width: int, height: int, max_resolution: int) -> tuple[int, int]:
        """Normalize resolution to fit within model limits.

        Maintains aspect ratio while downscaling if necessary.

        Args:
            width: Original width
            height: Original height
            max_resolution: Maximum allowed dimension

        Returns:
            Normalized (width, height) tuple
        """
        # Check if normalization is needed
        if width <= max_resolution and height <= max_resolution:
            return width, height

        # Calculate scale factor to fit within limits
        scale = max_resolution / max(width, height)

        # Apply scaling
        new_width = int(width * scale)
        new_height = int(height * scale)

        # Ensure minimum size
        new_width = max(16, new_width)
        new_height = max(16, new_height)

        self.logger.info(
            f"Normalized resolution from {width}x{height} to "
            f"{new_width}x{new_height} (scale: {scale:.2f})"
        )

        return new_width, new_height

    def estimate_memory(self, width: int, height: int, format: str = "png") -> int:
        """Estimate memory usage for an image of given dimensions.

        Args:
            width: Image width
            height: Image height
            format: Image format (affects bytes per pixel)

        Returns:
            Estimated bytes required
        """
        # Calculate base memory requirement
        bytes_per_pixel = BYTES_PER_PIXEL_RGBA if format in ["png", "webp"] else 3
        base_memory = width * height * bytes_per_pixel

        # Apply overhead multiplier for processing
        estimated_memory = int(base_memory * IMAGE_OVERHEAD_MULTIPLIER)

        return estimated_memory

    def _validate_memory_constraints(self, width: int, height: int) -> None:
        """Validate that resolution won't exceed memory limits.

        Args:
            width: Image width
            height: Image height

        Raises:
            ValidationError: If memory usage would exceed limit
        """
        estimated_bytes = self.estimate_memory(width, height)
        limit_bytes = self.config.memory_limit_mb * 1024 * 1024

        # Check with buffer
        available_bytes = limit_bytes * (1 - MEMORY_BUFFER_PERCENT)

        if estimated_bytes > available_bytes:
            estimated_mb = estimated_bytes / (1024 * 1024)
            raise ValidationError(
                f"Estimated memory usage ({estimated_mb:.1f}MB) exceeds "
                f"available limit ({self.config.memory_limit_mb}MB with "
                f"{int(MEMORY_BUFFER_PERCENT * 100)}% buffer)"
            )

    def get_resolution_preset(self, preset_name: str, model_tier: ModelTier) -> tuple[int, int]:
        """Get resolution dimensions for a named preset.

        Args:
            preset_name: Name of the preset
            model_tier: Model tier for dynamic presets

        Returns:
            Tuple of (width, height)

        Raises:
            ValidationError: If preset not found
        """
        try:
            return self.parse_resolution(preset_name, model_tier)
        except ValidationError:
            raise ValidationError(f"Unknown resolution preset: {preset_name}")

    def extract_resolution_hints(self, prompt: str) -> list[str]:
        """Extract resolution hints from prompt text.

        Looks for keywords like "4k", "high resolution", "ultra HD", etc.

        Args:
            prompt: Text prompt to analyze

        Returns:
            List of resolution-related keywords found
        """
        hints = []
        prompt_lower = prompt.lower()

        # Resolution keywords to look for
        keywords = [
            "4k",
            "uhd",
            "ultra hd",
            "ultra high definition",
            "2k",
            "qhd",
            "quad hd",
            "1080p",
            "full hd",
            "fhd",
            "720p",
            "hd",
            "high resolution",
            "high res",
            "hi-res",
            "low resolution",
            "low res",
            "professional",
            "production quality",
            "detailed",
            "ultra detailed",
            "crisp",
            "sharp",
            "pristine",
        ]

        for keyword in keywords:
            if keyword in prompt_lower:
                hints.append(keyword)

        # Look for resolution patterns (e.g., "3840x2160")
        resolution_pattern = r"\b\d{3,4}\s*x\s*\d{3,4}\b"
        if re.search(resolution_pattern, prompt_lower):
            hints.append("custom_resolution")

        return hints

    def recommend_resolution(
        self,
        prompt: str,
        model_tier: ModelTier,
        input_images: list[tuple[int, int]] | None = None,
    ) -> str:
        """Recommend optimal resolution based on prompt and inputs.

        Args:
            prompt: Text prompt
            model_tier: Model tier being used
            input_images: Optional list of input image dimensions

        Returns:
            Recommended resolution preset name
        """
        # Extract hints from prompt
        hints = self.extract_resolution_hints(prompt)

        # Check for explicit resolution requests
        if "4k" in hints or "uhd" in hints or "ultra hd" in hints:
            return "4k" if model_tier == ModelTier.PRO else "2k"
        elif "2k" in hints or "qhd" in hints:
            return "2k"
        elif "1080p" in hints or "full hd" in hints or "fhd" in hints:
            return "1080p"
        elif "720p" in hints or "hd" in hints:
            return "720p"

        # Check for quality indicators
        quality_indicators = [
            "professional",
            "production",
            "high resolution",
            "detailed",
            "ultra detailed",
            "crisp",
            "sharp",
        ]
        if any(indicator in hints for indicator in quality_indicators):
            return "high"

        # Check for speed indicators
        if "low resolution" in hints or "low res" in hints:
            return "low"

        # Consider input images
        if input_images:
            max_dim = max(max(width, height) for width, height in input_images)
            if max_dim >= 3000:
                return "4k" if model_tier == ModelTier.PRO else "2k"
            elif max_dim >= 2000:
                return "2k"
            elif max_dim >= 1500:
                return "1080p"

        # Default based on model
        if model_tier == ModelTier.PRO:
            return "2k"  # Good balance for Pro
        else:
            return "1024"  # Default for Flash

    def format_resolution_string(self, width: int, height: int) -> str:
        """Format resolution as a readable string.

        Args:
            width: Image width
            height: Image height

        Returns:
            Formatted resolution string (e.g., "1920x1080 (1080p)")
        """
        resolution_str = f"{width}x{height}"

        # Add common name if applicable
        common_names = {
            (3840, 3840): "4K Square",
            (3840, 2160): "4K UHD",
            (2160, 3840): "4K Portrait",
            (2048, 2048): "2K Square",
            (1920, 1080): "1080p FHD",
            (1080, 1920): "1080p Portrait",
            (1280, 720): "720p HD",
            (1024, 1024): "1K Square",
        }

        if (width, height) in common_names:
            resolution_str += f" ({common_names[(width, height)]})"

        return resolution_str
