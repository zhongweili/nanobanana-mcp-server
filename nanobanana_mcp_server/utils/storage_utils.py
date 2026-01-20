"""Storage optimization utilities for progressive image storage."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image as PILImage
import io

from ..config.constants import COMPRESSION_PROFILES


class ProgressiveImageStorage:
    """Handle progressive storage of images with multiple variants."""

    def __init__(self, thumbnail_sizes: List[int] = None):
        """Initialize progressive storage handler.

        Args:
            thumbnail_sizes: List of thumbnail sizes to generate
        """
        self.thumbnail_sizes = thumbnail_sizes or [256, 512, 1024]
        self.logger = logging.getLogger(__name__)
        self.compression_profiles = COMPRESSION_PROFILES

    def generate_variants(
        self,
        image_bytes: bytes,
        mime_type: str = "image/png"
    ) -> Dict[str, bytes]:
        """Generate multiple resolution variants of an image.

        Args:
            image_bytes: Original image data
            mime_type: MIME type of image

        Returns:
            Dictionary mapping variant names to image bytes
        """
        variants = {}

        try:
            # Open original image
            image = PILImage.open(io.BytesIO(image_bytes))
            orig_width, orig_height = image.size

            # Always include original
            variants["original"] = image_bytes

            # Generate thumbnails at different sizes
            for size in self.thumbnail_sizes:
                if orig_width > size or orig_height > size:
                    variant_name = f"thumb_{size}"
                    variant_bytes = self._create_variant(
                        image,
                        size,
                        self._get_compression_for_size(size)
                    )
                    variants[variant_name] = variant_bytes
                    self.logger.debug(f"Generated {variant_name} variant")

            # Generate display variant (1024px) if larger
            if orig_width > 1024 or orig_height > 1024:
                variants["display"] = self._create_variant(
                    image,
                    1024,
                    self.compression_profiles.get("display", 85)
                )

            # Generate preview variant (512px) if larger
            if orig_width > 512 or orig_height > 512:
                variants["preview"] = self._create_variant(
                    image,
                    512,
                    self.compression_profiles.get("preview", 80)
                )

            return variants

        except Exception as e:
            self.logger.error(f"Failed to generate variants: {e}")
            # Return at least the original
            return {"original": image_bytes}

    def _create_variant(
        self,
        image: PILImage.Image,
        max_size: int,
        quality: int
    ) -> bytes:
        """Create a resized variant of an image.

        Args:
            image: PIL Image object
            max_size: Maximum dimension
            quality: JPEG quality (1-100)

        Returns:
            Variant image bytes
        """
        # Calculate new dimensions maintaining aspect ratio
        orig_width, orig_height = image.size
        aspect_ratio = orig_width / orig_height

        if orig_width > orig_height:
            new_width = min(max_size, orig_width)
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = min(max_size, orig_height)
            new_width = int(new_height * aspect_ratio)

        # Resize image
        resized = image.resize(
            (new_width, new_height),
            PILImage.Resampling.LANCZOS
        )

        # Convert to RGB if necessary (for JPEG)
        if resized.mode not in ('RGB', 'L'):
            resized = resized.convert('RGB')

        # Save to bytes
        buffer = io.BytesIO()
        resized.save(buffer, format='JPEG', quality=quality, optimize=True)
        return buffer.getvalue()

    def _get_compression_for_size(self, size: int) -> int:
        """Get appropriate compression quality for thumbnail size.

        Args:
            size: Thumbnail size

        Returns:
            Compression quality (1-100)
        """
        if size <= 256:
            return self.compression_profiles.get("thumbnail", 70)
        elif size <= 512:
            return self.compression_profiles.get("preview", 80)
        else:
            return self.compression_profiles.get("display", 85)

    def calculate_storage_savings(
        self,
        original_bytes: int,
        variants: Dict[str, bytes]
    ) -> Dict[str, any]:
        """Calculate storage savings from optimization.

        Args:
            original_bytes: Size of original image
            variants: Dictionary of variants

        Returns:
            Storage statistics
        """
        total_variant_size = sum(len(v) for v in variants.values())
        savings = original_bytes - total_variant_size

        return {
            "original_size": original_bytes,
            "total_variant_size": total_variant_size,
            "savings_bytes": max(0, savings),
            "savings_percent": max(0, (savings / original_bytes * 100)) if original_bytes > 0 else 0,
            "variant_count": len(variants),
            "variants": {
                name: len(data)
                for name, data in variants.items()
            }
        }


class OptimizedImageRetrieval:
    """Optimize image retrieval based on client requirements."""

    def __init__(self, variants_dir: Path):
        """Initialize retrieval optimizer.

        Args:
            variants_dir: Directory containing image variants
        """
        self.variants_dir = variants_dir
        self.logger = logging.getLogger(__name__)

    def get_optimal_variant(
        self,
        image_id: str,
        requested_size: Optional[int] = None,
        available_variants: Dict[str, str] = None
    ) -> Tuple[str, str]:
        """Get the optimal image variant for a request.

        Args:
            image_id: Image identifier
            requested_size: Requested maximum dimension
            available_variants: Dictionary of available variants

        Returns:
            Tuple of (variant_name, file_path)
        """
        if not available_variants:
            # Default to original if no variants
            return "original", str(self.variants_dir / f"{image_id}.png")

        if requested_size is None:
            # No size specified, return original
            return "original", available_variants.get("original", "")

        # Find the smallest variant that meets the requirement
        suitable_variants = []
        for name, path in available_variants.items():
            if name == "original":
                suitable_variants.append((float('inf'), name, path))
            elif name.startswith("thumb_"):
                size = int(name.split("_")[1])
                if size >= requested_size:
                    suitable_variants.append((size, name, path))
            elif name == "display":
                suitable_variants.append((1024, name, path))
            elif name == "preview":
                suitable_variants.append((512, name, path))

        # Sort by size and return the smallest suitable variant
        if suitable_variants:
            suitable_variants.sort(key=lambda x: x[0])
            _, name, path = suitable_variants[0]
            self.logger.debug(f"Selected variant {name} for size {requested_size}")
            return name, path

        # No suitable variant, return original
        return "original", available_variants.get("original", "")

    def estimate_bandwidth_savings(
        self,
        original_size: int,
        variant_size: int,
        request_count: int = 1
    ) -> Dict[str, any]:
        """Estimate bandwidth savings from using variants.

        Args:
            original_size: Size of original image
            variant_size: Size of selected variant
            request_count: Number of requests

        Returns:
            Bandwidth statistics
        """
        original_bandwidth = original_size * request_count
        variant_bandwidth = variant_size * request_count
        savings = original_bandwidth - variant_bandwidth

        return {
            "original_bandwidth": original_bandwidth,
            "variant_bandwidth": variant_bandwidth,
            "savings_bytes": savings,
            "savings_percent": (savings / original_bandwidth * 100) if original_bandwidth > 0 else 0,
            "request_count": request_count
        }


def optimize_image_format(
    image_bytes: bytes,
    target_format: str = "webp",
    quality: int = 85
) -> Tuple[bytes, str]:
    """Optimize image format for better compression.

    Args:
        image_bytes: Original image data
        target_format: Target format (webp, jpeg, png)
        quality: Compression quality

    Returns:
        Tuple of (optimized_bytes, mime_type)
    """
    try:
        # Open image
        image = PILImage.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary for JPEG/WebP
        if target_format in ["webp", "jpeg"] and image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')

        # Save in target format
        buffer = io.BytesIO()
        if target_format == "webp":
            image.save(buffer, format='WEBP', quality=quality, method=6)
            mime_type = "image/webp"
        elif target_format == "jpeg":
            image.save(buffer, format='JPEG', quality=quality, optimize=True)
            mime_type = "image/jpeg"
        else:
            image.save(buffer, format='PNG', optimize=True)
            mime_type = "image/png"

        optimized_bytes = buffer.getvalue()

        # Only return optimized if it's smaller
        if len(optimized_bytes) < len(image_bytes):
            return optimized_bytes, mime_type
        else:
            return image_bytes, "image/png"

    except Exception as e:
        logging.error(f"Format optimization failed: {e}")
        return image_bytes, "image/png"