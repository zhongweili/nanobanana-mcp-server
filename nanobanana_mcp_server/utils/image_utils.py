from typing import Dict, List, Tuple, Optional
import base64
from PIL import Image
from io import BytesIO
import logging
from ..config.constants import SUPPORTED_IMAGE_TYPES
from ..core.exceptions import ImageProcessingError, ValidationError


def validate_image_format(mime_type: str) -> bool:
    """Validate that the MIME type is supported."""
    return mime_type.lower() in SUPPORTED_IMAGE_TYPES


def get_image_dimensions(image_b64: str) -> Tuple[int, int]:
    """Get image dimensions from base64 data."""
    try:
        image_data = base64.b64decode(image_b64)
        image = Image.open(BytesIO(image_data))
        return image.size
    except Exception as e:
        logging.error(f"Failed to get image dimensions: {e}")
        raise ValidationError(f"Invalid image data: {e}")


def get_image_info(image_b64: str) -> dict:
    """Get comprehensive image information from base64 data."""
    try:
        image_data = base64.b64decode(image_b64)
        image = Image.open(BytesIO(image_data))

        return {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
            "width": image.width,
            "height": image.height,
            "size_bytes": len(image_data),
            "aspect_ratio": round(image.width / image.height, 2),
            "color_mode": image.mode,
            "has_transparency": image.mode in ("RGBA", "LA") or "transparency" in image.info,
        }
    except Exception as e:
        logging.error(f"Failed to get image info: {e}")
        raise ValidationError(f"Invalid image data: {e}")


def optimize_image_size(image_b64: str, max_size: int = 20 * 1024 * 1024) -> str:
    """Optimize image size if it exceeds the maximum limit."""
    try:
        image_data = base64.b64decode(image_b64)

        if len(image_data) <= max_size:
            return image_b64

        # Implement basic compression by reducing quality/size
        image = Image.open(BytesIO(image_data))

        # Calculate scale factor to reduce size
        scale_factor = (max_size * 0.8 / len(image_data)) ** 0.5
        new_width = int(image.width * scale_factor)
        new_height = int(image.height * scale_factor)

        # Resize image
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save with compression
        output = BytesIO()
        if image.format == "JPEG":
            resized_image.save(output, format="JPEG", quality=85, optimize=True)
        else:
            resized_image.save(output, format="PNG", optimize=True)

        output.seek(0)
        optimized_data = output.read()

        # If still too large, raise error
        if len(optimized_data) > max_size:
            raise ValidationError(
                f"Image size {len(optimized_data)} still exceeds maximum {max_size} after optimization"
            )

        return base64.b64encode(optimized_data).decode()

    except Exception as e:
        logging.error(f"Failed to optimize image size: {e}")
        raise ImageProcessingError(f"Image optimization failed: {e}")


def convert_image_format(image_b64: str, target_format: str = "PNG") -> str:
    """Convert image to specified format."""
    try:
        image_data = base64.b64decode(image_b64)
        image = Image.open(BytesIO(image_data))

        # Handle transparency for JPEG conversion
        if target_format.upper() == "JPEG" and image.mode in ("RGBA", "LA"):
            # Create white background for JPEG
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "RGBA":
                background.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
            else:
                background.paste(image)
            image = background

        output = BytesIO()
        image.save(output, format=target_format.upper())
        output.seek(0)

        return base64.b64encode(output.read()).decode()

    except Exception as e:
        logging.error(f"Failed to convert image format: {e}")
        raise ImageProcessingError(f"Image format conversion failed: {e}")


def create_thumbnail(source_path: str, thumb_path: str, size: int = 256) -> None:
    """
    Create a thumbnail from an image file, saving to disk.

    Args:
        source_path: Path to source image file
        thumb_path: Path where thumbnail should be saved
        size: Maximum thumbnail size (maintains aspect ratio)
    """
    try:
        with Image.open(source_path) as image:
            # Create thumbnail maintaining aspect ratio
            image.thumbnail((size, size), Image.Resampling.LANCZOS)

            # Convert to RGB for JPEG if necessary
            if image.mode in ("RGBA", "LA", "P"):
                rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                if image.mode in ("RGBA", "LA"):
                    rgb_image.paste(image, mask=image.split()[-1])
                else:
                    rgb_image.paste(image)
                image = rgb_image

            # Save as JPEG for smaller file size
            image.save(thumb_path, format="JPEG", quality=85, optimize=True)

    except Exception as e:
        logging.error(f"Failed to create thumbnail {source_path} -> {thumb_path}: {e}")
        raise ImageProcessingError(f"Thumbnail creation failed: {e}")


def create_thumbnail_base64(image_b64: str, size: Tuple[int, int] = (256, 256)) -> str:
    """Create a thumbnail from base64 image data."""
    try:
        image_data = base64.b64decode(image_b64)
        image = Image.open(BytesIO(image_data))

        # Create thumbnail maintaining aspect ratio
        image.thumbnail(size, Image.Resampling.LANCZOS)

        output = BytesIO()
        # Use PNG for thumbnails to preserve quality
        image.save(output, format="PNG", optimize=True)
        output.seek(0)

        return base64.b64encode(output.read()).decode()

    except Exception as e:
        logging.error(f"Failed to create thumbnail: {e}")
        raise ImageProcessingError(f"Thumbnail creation failed: {e}")


def create_multiple_thumbnails(
    image_bytes: bytes,
    sizes: List[int] = None,
    format: str = "JPEG",
    quality: int = 85
) -> Dict[int, bytes]:
    """Create multiple thumbnail sizes from image data.

    Args:
        image_bytes: Original image data
        sizes: List of thumbnail sizes (max dimension)
        format: Output format (JPEG, PNG, WEBP)
        quality: Compression quality for JPEG/WEBP

    Returns:
        Dictionary mapping size to thumbnail bytes
    """
    if sizes is None:
        sizes = [256, 512, 1024]

    thumbnails = {}

    try:
        image = Image.open(BytesIO(image_bytes))
        orig_width, orig_height = image.size

        for size in sizes:
            # Skip if image is already smaller
            if orig_width <= size and orig_height <= size:
                continue

            # Create a copy for resizing
            thumb_image = image.copy()

            # Calculate new dimensions
            thumb_image.thumbnail((size, size), Image.Resampling.LANCZOS)

            # Convert to RGB for JPEG/WEBP if necessary
            if format in ("JPEG", "WEBP") and thumb_image.mode in ("RGBA", "LA", "P"):
                rgb_image = Image.new("RGB", thumb_image.size, (255, 255, 255))
                if thumb_image.mode == "P":
                    thumb_image = thumb_image.convert("RGBA")
                if thumb_image.mode in ("RGBA", "LA"):
                    rgb_image.paste(thumb_image, mask=thumb_image.split()[-1])
                else:
                    rgb_image.paste(thumb_image)
                thumb_image = rgb_image

            # Save to bytes
            output = BytesIO()
            if format == "JPEG":
                thumb_image.save(output, format="JPEG", quality=quality, optimize=True)
            elif format == "WEBP":
                thumb_image.save(output, format="WEBP", quality=quality, method=6)
            else:
                thumb_image.save(output, format="PNG", optimize=True)

            output.seek(0)
            thumbnails[size] = output.read()

    except Exception as e:
        logging.error(f"Failed to create multiple thumbnails: {e}")
        raise ImageProcessingError(f"Multiple thumbnail creation failed: {e}")

    return thumbnails


def resize_image(
    image_bytes: bytes,
    max_width: int,
    max_height: int,
    maintain_aspect: bool = True
) -> bytes:
    """Resize an image to fit within specified dimensions.

    Args:
        image_bytes: Original image data
        max_width: Maximum width
        max_height: Maximum height
        maintain_aspect: Whether to maintain aspect ratio

    Returns:
        Resized image bytes
    """
    try:
        image = Image.open(BytesIO(image_bytes))

        if maintain_aspect:
            # Calculate scaling factor
            width_ratio = max_width / image.width
            height_ratio = max_height / image.height
            scale_factor = min(width_ratio, height_ratio)

            if scale_factor < 1:
                new_width = int(image.width * scale_factor)
                new_height = int(image.height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            # Resize to exact dimensions
            image = image.resize((max_width, max_height), Image.Resampling.LANCZOS)

        # Save to bytes
        output = BytesIO()
        # Detect format from original
        format_name = image.format or "PNG"
        image.save(output, format=format_name, optimize=True)
        output.seek(0)

        return output.read()

    except Exception as e:
        logging.error(f"Failed to resize image: {e}")
        raise ImageProcessingError(f"Image resize failed: {e}")


def estimate_file_size(
    width: int,
    height: int,
    format: str = "png",
    quality: int = 85
) -> int:
    """Estimate the file size of an image.

    Args:
        width: Image width
        height: Image height
        format: Image format
        quality: Compression quality (for JPEG/WEBP)

    Returns:
        Estimated file size in bytes
    """
    # Base calculation: width * height * bytes_per_pixel
    total_pixels = width * height

    # Estimation factors based on format and quality
    if format.lower() == "png":
        # PNG: typically 2-4 bytes per pixel for photos
        bytes_per_pixel = 3.0
    elif format.lower() in ("jpeg", "jpg"):
        # JPEG: varies greatly with quality
        if quality >= 95:
            bytes_per_pixel = 1.5
        elif quality >= 85:
            bytes_per_pixel = 0.8
        elif quality >= 75:
            bytes_per_pixel = 0.5
        else:
            bytes_per_pixel = 0.3
    elif format.lower() == "webp":
        # WebP: better compression than JPEG
        if quality >= 95:
            bytes_per_pixel = 1.2
        elif quality >= 85:
            bytes_per_pixel = 0.6
        elif quality >= 75:
            bytes_per_pixel = 0.4
        else:
            bytes_per_pixel = 0.25
    else:
        # Default conservative estimate
        bytes_per_pixel = 3.0

    estimated_size = int(total_pixels * bytes_per_pixel)

    # Add some overhead for metadata
    estimated_size += 1024  # 1KB for headers/metadata

    return estimated_size


def estimate_compression_ratio(original_b64: str, compressed_b64: str) -> float:
    """Estimate compression ratio between original and compressed images."""
    try:
        original_size = len(base64.b64decode(original_b64))
        compressed_size = len(base64.b64decode(compressed_b64))

        return compressed_size / original_size if original_size > 0 else 1.0

    except Exception as e:
        logging.error(f"Failed to estimate compression ratio: {e}")
        return 1.0


def validate_image_content(image_b64: str, mime_type: str) -> bool:
    """Validate that image content matches the declared MIME type."""
    try:
        image_data = base64.b64decode(image_b64)
        image = Image.open(BytesIO(image_data))

        # Map PIL formats to MIME types
        format_mapping = {
            "JPEG": ["image/jpeg", "image/jpg"],
            "PNG": ["image/png"],
            "WEBP": ["image/webp"],
            "GIF": ["image/gif"],
        }

        expected_mimes = format_mapping.get(image.format, [])
        return mime_type.lower() in expected_mimes

    except Exception as e:
        logging.error(f"Failed to validate image content: {e}")
        return False


def detect_image_type(image_b64: str) -> Optional[str]:
    """Detect the actual image type from base64 data."""
    try:
        image_data = base64.b64decode(image_b64)
        image = Image.open(BytesIO(image_data))

        # Map PIL formats to MIME types
        format_mapping = {
            "JPEG": "image/jpeg",
            "PNG": "image/png",
            "WEBP": "image/webp",
            "GIF": "image/gif",
        }

        return format_mapping.get(image.format)

    except Exception as e:
        logging.error(f"Failed to detect image type: {e}")
        return None
