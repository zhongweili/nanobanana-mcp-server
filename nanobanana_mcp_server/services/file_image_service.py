"""
File-based image service that saves images to a user-specified directory.
Replaces the temporary storage system with persistent file output.
"""

import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import logging
from PIL import Image as PILImage
import io

from fastmcp.utilities.types import Image as MCPImage
from .gemini_client import GeminiClient
from ..utils.image_utils import validate_image_format
from ..config.settings import GeminiConfig, ServerConfig
from ..core.progress_tracker import ProgressContext


class FileImageService:
    """Service for image generation and saving to user-specified directory."""

    def __init__(
        self, gemini_client: GeminiClient, gemini_config: GeminiConfig, server_config: ServerConfig
    ):
        self.gemini_client = gemini_client
        self.gemini_config = gemini_config
        self.server_config = server_config
        self.output_dir = Path(server_config.image_output_dir)
        self.logger = logging.getLogger(__name__)

        # Thumbnail settings
        self.thumbnail_max_size = (256, 256)
        self.thumbnail_quality = 85
        self.max_thumbnail_bytes = 50 * 1024  # 50KB max

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"FileImageService initialized with output directory: {self.output_dir}")

    def _generate_filename(self, extension: str = "png", counter: int = 1) -> str:
        """Generate timestamp-based filename."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"{timestamp}_{counter:03d}.{extension}"

    def _get_next_filename(self, extension: str = "png") -> str:
        """Get the next available filename with counter."""
        counter = 1
        while True:
            filename = self._generate_filename(extension, counter)
            if not (self.output_dir / filename).exists():
                return filename
            counter += 1
            if counter > 999:  # Safety limit
                # Fallback to microsecond precision
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
                return f"{timestamp}.{extension}"

    def _generate_thumbnail(self, image_bytes: bytes) -> Tuple[bytes, int, int]:
        """Generate a small thumbnail from image bytes."""
        try:
            # Open image
            image = PILImage.open(io.BytesIO(image_bytes))

            # Convert to RGB if needed (for JPEG compatibility)
            if image.mode in ("RGBA", "LA", "P"):
                image = image.convert("RGB")

            # Calculate thumbnail size preserving aspect ratio
            image.thumbnail(self.thumbnail_max_size, PILImage.Resampling.LANCZOS)

            # Save thumbnail as JPEG for smaller size
            output = io.BytesIO()
            format_name = "JPEG"
            image.save(output, format=format_name, quality=self.thumbnail_quality, optimize=True)
            thumbnail_bytes = output.getvalue()

            # If still too large, reduce quality
            quality = self.thumbnail_quality
            while len(thumbnail_bytes) > self.max_thumbnail_bytes and quality > 20:
                quality -= 10
                output = io.BytesIO()
                image.save(output, format=format_name, quality=quality, optimize=True)
                thumbnail_bytes = output.getvalue()

            return thumbnail_bytes, image.width, image.height

        except Exception as e:
            self.logger.error(f"Failed to generate thumbnail: {e}")
            raise

    def generate_images(
        self,
        prompt: str,
        n: int = 1,
        negative_prompt: Optional[str] = None,
        system_instruction: Optional[str] = None,
        input_images: Optional[List[Tuple[str, str]]] = None,
        aspect_ratio: Optional[str] = None,
    ) -> Tuple[List[MCPImage], List[Dict[str, Any]]]:
        """
        Generate images using Gemini API and save to file system.

        Args:
            prompt: Main generation prompt
            n: Number of images to generate
            negative_prompt: Optional negative prompt
            system_instruction: Optional system instruction
            input_images: List of (base64, mime_type) tuples for input images
            aspect_ratio: Optional aspect ratio string (e.g., "16:9")

        Returns:
            Tuple of (thumbnail_images, file_metadata_list)
        """
        with ProgressContext(
            "image_generation", f"Generating {n} image(s)...", {"prompt": prompt[:100], "count": n}
        ) as progress:
            progress.update(10, "Preparing generation request...")

            # Build content list
            contents = []
            if system_instruction:
                contents.append(system_instruction)

            # Add negative prompt constraints
            full_prompt = prompt
            if negative_prompt:
                full_prompt += f"\n\nConstraints (avoid): {negative_prompt}"
            contents.append(full_prompt)

            # Add input images if provided
            if input_images:
                images_b64, mime_types = zip(*input_images)
                image_parts = self.gemini_client.create_image_parts(
                    list(images_b64), list(mime_types)
                )
                contents = image_parts + contents

            progress.update(20, "Sending requests to Gemini API...")

            # Generate images
            thumbnail_images = []
            file_metadata = []

            for i in range(n):
                try:
                    progress.update(20 + (i * 60 // n), f"Generating image {i + 1}/{n}...")

                    response = self.gemini_client.generate_content(
                        contents, aspect_ratio=aspect_ratio
                    )
                    images = self.gemini_client.extract_images(response)

                    for j, image_bytes in enumerate(images):
                        progress.update(
                            20 + ((i * 60 + j * 60 // len(images)) // n),
                            f"Saving image {i + 1}.{j + 1}...",
                        )

                        # Get filename and full path
                        filename = self._get_next_filename(self.gemini_config.default_image_format)
                        full_path = self.output_dir / filename

                        # Save full resolution image
                        with open(full_path, "wb") as f:
                            f.write(image_bytes)

                        # Get image dimensions
                        image = PILImage.open(io.BytesIO(image_bytes))
                        width, height = image.size

                        # Generate thumbnail for inline preview
                        thumbnail_bytes, thumb_w, thumb_h = self._generate_thumbnail(image_bytes)
                        thumbnail_image = MCPImage(data=thumbnail_bytes, format="jpeg")
                        thumbnail_images.append(thumbnail_image)

                        # Create metadata
                        metadata = {
                            "filename": filename,
                            "full_path": str(full_path),
                            "size_bytes": len(image_bytes),
                            "thumbnail_size_bytes": len(thumbnail_bytes),
                            "width": width,
                            "height": height,
                            "aspect_ratio": aspect_ratio,
                            "thumbnail_width": thumb_w,
                            "thumbnail_height": thumb_h,
                            "mime_type": f"image/{self.gemini_config.default_image_format}",
                            "created_at": time.time(),
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "system_instruction": system_instruction,
                            "response_index": i + 1,
                            "image_index": j + 1,
                            "synthid_watermark": True,
                        }
                        file_metadata.append(metadata)

                        self.logger.info(f"Saved image to {full_path} ({len(image_bytes)} bytes)")

                except Exception as e:
                    self.logger.error(f"Failed to generate image {i + 1}: {e}")
                    # Continue with other images rather than failing completely
                    continue

            progress.update(90, f"Successfully generated {len(thumbnail_images)} image(s)")
            progress.update(
                100, f"Generated and saved {len(file_metadata)} image(s) to {self.output_dir}"
            )

            return thumbnail_images, file_metadata

    def edit_image(
        self, instruction: str, base_image_b64: str, mime_type: str = "image/png"
    ) -> Tuple[List[MCPImage], List[Dict[str, Any]]]:
        """
        Edit an image using conversational instructions and save to file system.

        Args:
            instruction: Natural language editing instruction
            base_image_b64: Base64 encoded source image
            mime_type: MIME type of source image

        Returns:
            Tuple of (thumbnail_images, file_metadata_list)
        """
        with ProgressContext(
            "image_editing", "Editing image...", {"instruction": instruction[:100]}
        ) as progress:
            try:
                progress.update(10, "Validating input image...")

                # Validate and prepare image
                validate_image_format(mime_type)

                progress.update(20, "Preparing edit request...")

                # Create parts for Gemini API
                image_parts = self.gemini_client.create_image_parts([base_image_b64], [mime_type])
                contents = image_parts + [instruction]

                progress.update(40, "Sending edit request to Gemini API...")

                # Generate edited image
                response = self.gemini_client.generate_content(contents)
                image_bytes_list = self.gemini_client.extract_images(response)

                progress.update(70, "Processing edited image(s)...")

                # Process edited images
                thumbnail_images = []
                file_metadata = []

                for i, image_bytes in enumerate(image_bytes_list):
                    progress.update(
                        70 + (i * 20 // len(image_bytes_list)),
                        f"Saving result {i + 1}/{len(image_bytes_list)}...",
                    )

                    # Get filename and full path
                    filename = self._get_next_filename(self.gemini_config.default_image_format)
                    full_path = self.output_dir / filename

                    # Save full resolution image
                    with open(full_path, "wb") as f:
                        f.write(image_bytes)

                    # Get image dimensions
                    image = PILImage.open(io.BytesIO(image_bytes))
                    width, height = image.size

                    # Generate thumbnail for inline preview
                    thumbnail_bytes, thumb_w, thumb_h = self._generate_thumbnail(image_bytes)
                    thumbnail_image = MCPImage(data=thumbnail_bytes, format="jpeg")
                    thumbnail_images.append(thumbnail_image)

                    # Create metadata
                    metadata = {
                        "filename": filename,
                        "full_path": str(full_path),
                        "size_bytes": len(image_bytes),
                        "thumbnail_size_bytes": len(thumbnail_bytes),
                        "width": width,
                        "height": height,
                        "thumbnail_width": thumb_w,
                        "thumbnail_height": thumb_h,
                        "mime_type": f"image/{self.gemini_config.default_image_format}",
                        "created_at": time.time(),
                        "instruction": instruction,
                        "source_mime_type": mime_type,
                        "edit_index": i + 1,
                        "synthid_watermark": True,
                    }
                    file_metadata.append(metadata)

                    self.logger.info(
                        f"Saved edited image to {full_path} ({len(image_bytes)} bytes)"
                    )

                progress.update(
                    100, f"Successfully edited and saved {len(thumbnail_images)} image(s)"
                )
                return thumbnail_images, file_metadata

            except Exception as e:
                self.logger.error(f"Failed to edit image: {e}")
                raise

    def get_output_stats(self) -> Dict[str, Any]:
        """Get statistics about the output directory."""
        try:
            image_files = (
                list(self.output_dir.glob("*.png"))
                + list(self.output_dir.glob("*.jpg"))
                + list(self.output_dir.glob("*.jpeg"))
            )

            total_size = sum(f.stat().st_size for f in image_files)

            return {
                "output_directory": str(self.output_dir),
                "total_images": len(image_files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "recent_images": [
                    str(f.name)
                    for f in sorted(image_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
                ],
            }
        except Exception as e:
            self.logger.error(f"Failed to get output stats: {e}")
            return {"output_directory": str(self.output_dir), "error": str(e)}
