"""Gemini 3 Pro Image specialized service for high-quality generation."""

import base64
from datetime import UTC, datetime
import hashlib
from io import BytesIO
import logging
import os
from typing import Any

from fastmcp.utilities.types import Image as MCPImage
from PIL import Image as PILImage

from ..config.constants import TEMP_FILE_SUFFIX
from ..config.settings import MediaResolution, ProImageConfig, ThinkingLevel
from ..core.exceptions import ImageProcessingError
from ..core.progress_tracker import ProgressContext
from ..utils.image_utils import create_thumbnail, validate_image_format
from ..utils.validation_utils import resolve_output_path, validate_aspect_ratio_string
from .gemini_client import GeminiClient
from .image_storage_service import ImageStorageService


def _atomic_write_bytes(full_path: str, data: bytes) -> None:
    """Write bytes to full_path via a temp file and atomic replace."""
    temp_path = f"{full_path}{TEMP_FILE_SUFFIX}"
    try:
        with open(temp_path, "wb") as f:
            f.write(data)
        os.replace(temp_path, full_path)
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        raise


class ProImageService:
    """Service for high-quality image generation using Gemini 3 Pro Image model."""

    def __init__(
        self,
        gemini_client: GeminiClient,
        config: ProImageConfig,
        storage_service: ImageStorageService | None = None,
    ):
        self.gemini_client = gemini_client
        self.config = config
        self.storage_service = storage_service
        self.logger = logging.getLogger(__name__)
        self._tier_label = (
            "nb2"
            if config.model_name.strip().lower() == "gemini-3.1-flash-image-preview"
            else "pro"
        )

    def generate_images(
        self,
        prompt: str,
        n: int = 1,
        resolution: str = "high",
        aspect_ratio: str | None = None,
        output_path: str | None = None,
        thinking_level: ThinkingLevel | None = None,
        enable_grounding: bool | None = None,
        media_resolution: MediaResolution | None = None,
        negative_prompt: str | None = None,
        system_instruction: str | None = None,
        input_images: list[tuple[str, str]] | None = None,
        use_storage: bool = True,
    ) -> tuple[list[MCPImage], list[dict[str, Any]]]:
        """
        Generate high-quality images using Gemini 3 Pro Image.

        Features:
        - Up to 4K resolution support
        - Google Search grounding for factual accuracy
        - Advanced reasoning with configurable thinking levels
        - Professional-grade outputs

        Args:
            prompt: Main generation prompt
            n: Number of images to generate
            resolution: Output resolution ('high', '4k', '2k', '1k')
            aspect_ratio: Output aspect ratio (e.g., '1:1', '16:9', '4:5')
            output_path: Optional output path for saving images
            thinking_level: Reasoning depth (LOW or HIGH)
            enable_grounding: Enable Google Search grounding
            media_resolution: Vision processing detail level
            negative_prompt: Optional constraints to avoid
            system_instruction: Optional system-level guidance
            input_images: List of (base64, mime_type) tuples for conditioning
            use_storage: Store images and return resource links with thumbnails

        Returns:
            Tuple of (image_blocks_or_resource_links, metadata_list)
        """
        # Apply defaults from config
        if thinking_level is None:
            thinking_level = self.config.default_thinking_level
        if enable_grounding is None:
            enable_grounding = self.config.enable_search_grounding
        if media_resolution is None:
            media_resolution = self.config.default_media_resolution

        # Validate aspect_ratio if provided
        if aspect_ratio:
            validate_aspect_ratio_string(
                aspect_ratio,
                allow_extreme=self.config.supports_extreme_aspect_ratios,
            )

        with ProgressContext(
            "pro_image_generation",
            f"Generating {n} high-quality image(s) with Gemini 3 Pro...",
            {"prompt": prompt[:100], "count": n, "resolution": resolution},
        ) as progress:
            progress.update(5, "Configuring Pro model parameters...")

            self.logger.info(
                f"Pro generation: prompt='{prompt[:50]}...', n={n}, "
                f"resolution={resolution}, thinking={thinking_level.value}, "
                f"grounding={enable_grounding}"
            )

            progress.update(10, "Preparing generation request...")

            # Build content with Pro-optimized prompt
            contents = []

            # System instruction (optional)
            if system_instruction:
                contents.append(system_instruction)
            elif enable_grounding:
                # Add grounding hint for Pro model
                contents.append(
                    "Use real-world knowledge and current information "
                    "to create accurate, detailed images."
                )

            # Enhanced prompt for Pro model
            enhanced_prompt = self._enhance_prompt_for_pro(prompt, resolution, negative_prompt)
            contents.append(enhanced_prompt)

            # Add input images if provided (Pro benefits from images-first)
            if input_images:
                images_b64, mime_types = zip(*input_images, strict=False)
                image_parts = self.gemini_client.create_image_parts(
                    list(images_b64), list(mime_types)
                )
                # Pro model: place images before text for better context
                contents = image_parts + contents

            progress.update(20, "Sending requests to Gemini 3 Pro API...")

            # Generate images
            all_images = []
            all_metadata = []

            for i in range(n):
                try:
                    progress.update(
                        20 + (i * 70 // n), f"Generating high-quality image {i + 1}/{n}..."
                    )

                    # Build generation config for the current image model.
                    # Resolution is passed and mapped to image_size in gemini_client.
                    gen_config = {
                        "resolution": resolution,  # Will be mapped to image_size (1K, 2K, 4K)
                    }
                    if self.config.supports_thinking:
                        gen_config["thinking_level"] = thinking_level.value

                    # Grounding is controlled via prompt/system instruction
                    # not as a direct API parameter

                    response = self.gemini_client.generate_content(
                        contents,
                        config=gen_config,
                        aspect_ratio=aspect_ratio,
                    )
                    images = self.gemini_client.extract_images(response)

                    for j, image_bytes in enumerate(images):
                        # Pro metadata
                        metadata = {
                            "model": self.config.model_name,
                            "model_tier": self._tier_label,
                            "response_index": i + 1,
                            "image_index": j + 1,
                            "resolution": resolution,
                            "aspect_ratio": aspect_ratio,
                            "thinking_level": (
                                thinking_level.value if self.config.supports_thinking else None
                            ),
                            "media_resolution": (
                                media_resolution.value
                                if self.config.supports_media_resolution
                                else None
                            ),
                            "grounding_enabled": enable_grounding,
                            "mime_type": f"image/{self.config.default_image_format}",
                            "synthid_watermark": True,
                            "prompt": prompt,
                            "enhanced_prompt": enhanced_prompt,
                            "negative_prompt": negative_prompt,
                        }

                        # Storage handling - custom output_path takes precedence
                        if output_path:
                            # Save directly to specified output path
                            timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
                            image_hash = hashlib.md5(
                                image_bytes, usedforsecurity=False
                            ).hexdigest()[:8]
                            default_filename = f"pro_{timestamp}_{i + 1}_{j + 1}_{image_hash}.{self.config.default_image_format}"
                            overall_index = (i * len(images)) + j + 1

                            full_path = resolve_output_path(
                                output_path=output_path,
                                default_dir=os.path.dirname(output_path) or ".",
                                default_filename=default_filename,
                                image_index=overall_index,
                            )

                            # Ensure output directory exists
                            os.makedirs(os.path.dirname(full_path) or ".", exist_ok=True)

                            # Write image file (atomic)
                            _atomic_write_bytes(full_path, image_bytes)

                            # Get image dimensions
                            with PILImage.open(BytesIO(image_bytes)) as img:
                                width, height = img.size

                            # Create thumbnail alongside the image (graceful degradation)
                            path_stem, _ = os.path.splitext(full_path)
                            thumb_path = f"{path_stem}_thumb.jpeg"
                            try:
                                create_thumbnail(full_path, thumb_path, size=256)
                                # Read thumbnail for response
                                with open(thumb_path, "rb") as f:
                                    thumb_data = f.read()
                                thumbnail_image = MCPImage(data=thumb_data, format="jpeg")
                                all_images.append(thumbnail_image)
                            except ImageProcessingError as e:
                                # Thumbnail failed, return full image instead
                                self.logger.warning(
                                    f"Thumbnail creation failed, using full image: {e}"
                                )
                                thumb_path = None
                                full_image = MCPImage(
                                    data=image_bytes, format=self.config.default_image_format
                                )
                                all_images.append(full_image)

                            metadata.update(
                                {
                                    "full_path": full_path,
                                    "thumb_path": thumb_path,
                                    "size_bytes": len(image_bytes),
                                    "width": width,
                                    "height": height,
                                    "is_stored": True,
                                    "output_path_used": True,
                                }
                            )

                            all_metadata.append(metadata)

                            self.logger.info(
                                f"Generated Pro image {i + 1}.{j + 1} - "
                                f"saved to {full_path} "
                                f"({len(image_bytes)} bytes, {width}x{height})"
                            )

                        elif use_storage and self.storage_service:
                            # Use storage service for default behavior
                            stored_info = self.storage_service.store_image(
                                image_bytes, f"image/{self.config.default_image_format}", metadata
                            )

                            thumbnail_b64 = self.storage_service.get_thumbnail_base64(
                                stored_info.id
                            )
                            if thumbnail_b64:
                                thumbnail_bytes = base64.b64decode(thumbnail_b64)
                                thumbnail_image = MCPImage(data=thumbnail_bytes, format="jpeg")
                                all_images.append(thumbnail_image)

                            metadata.update(
                                {
                                    "storage_id": stored_info.id,
                                    "full_image_uri": f"file://images/{stored_info.id}",
                                    "full_path": stored_info.full_path,
                                    "thumbnail_uri": f"file://images/{stored_info.id}/thumbnail",
                                    "size_bytes": stored_info.size_bytes,
                                    "thumbnail_size_bytes": stored_info.thumbnail_size_bytes,
                                    "width": stored_info.width,
                                    "height": stored_info.height,
                                    "expires_at": stored_info.expires_at,
                                    "is_stored": True,
                                }
                            )

                            all_metadata.append(metadata)

                            self.logger.info(
                                f"Generated Pro image {i + 1}.{j + 1} - "
                                f"stored as {stored_info.id} "
                                f"({stored_info.size_bytes} bytes, {stored_info.width}x{stored_info.height})"
                            )
                        else:
                            # Direct return without storage
                            mcp_image = MCPImage(
                                data=image_bytes, format=self.config.default_image_format
                            )
                            all_images.append(mcp_image)
                            all_metadata.append(metadata)

                            self.logger.info(
                                f"Generated Pro image {i + 1}.{j + 1} "
                                f"(size: {len(image_bytes)} bytes)"
                            )

                except Exception as e:
                    self.logger.error(f"Failed to generate Pro image {i + 1}: {e}")
                    # Re-raise to see the actual error
                    raise

            progress.update(100, f"Generated {len(all_images)} high-quality image(s)")

            if not all_images:
                self.logger.warning("No images were generated by Pro model")

            return all_images, all_metadata

    def edit_images(
        self,
        instruction: str,
        *,
        base_image_b64: str | None = None,
        mime_type: str = "image/png",
        file_data_part: dict[str, Any] | None = None,
        output_path: str | None = None,
        thinking_level: ThinkingLevel | None = None,
        media_resolution: MediaResolution | None = None,
        use_storage: bool = True,
    ) -> tuple[list[MCPImage], list[dict[str, Any]]]:
        """
        Edit an image and return thumbnails + per-image metadata.

        Input can be provided as either:
        - Inline image bytes (base_image_b64 + mime_type)
        - Files API reference (file_data_part = {file_data:{mime_type, uri}})
        """
        if thinking_level is None:
            thinking_level = self.config.default_thinking_level
        if media_resolution is None:
            media_resolution = self.config.default_media_resolution

        with ProgressContext(
            "pro_image_editing",
            f"Editing image with {self.config.model_name}...",
            {"instruction": instruction[:100]},
        ) as progress:
            progress.update(10, "Configuring model editing parameters...")

            # Validate image mime type when available
            source_mime_type = mime_type
            if file_data_part:
                source_mime_type = (
                    (file_data_part.get("file_data") or {}).get("mime_type") or source_mime_type
                )
            validate_image_format(source_mime_type)

            progress.update(20, "Preparing edit request...")

            # Enhanced instruction for higher quality edits
            enhanced_instruction = (
                f"{instruction}\n\n"
                "Maintain the original image's quality and style. "
                "Make precise, high-quality edits."
            )

            # Build contents: prefer file_data when available to avoid base64 transfer.
            if file_data_part:
                contents = [file_data_part, enhanced_instruction]
            else:
                if not base_image_b64:
                    raise ImageProcessingError(
                        "Missing base_image_b64: provide base_image_b64 or file_data_part"
                    )
                image_parts = self.gemini_client.create_image_parts(
                    [base_image_b64], [source_mime_type]
                )
                contents = [*image_parts, enhanced_instruction]

            progress.update(40, "Sending edit request to Gemini API...")

            gen_config: dict[str, Any] = {}
            if self.config.supports_thinking:
                gen_config["thinking_level"] = thinking_level.value
            if self.config.supports_media_resolution:
                gen_config["media_resolution"] = media_resolution.value

            response = self.gemini_client.generate_content(contents, config=gen_config)
            image_bytes_list = self.gemini_client.extract_images(response)

            progress.update(70, "Processing edited image(s)...")

            mcp_images: list[MCPImage] = []
            all_metadata: list[dict[str, Any]] = []

            for i, image_bytes in enumerate(image_bytes_list):
                edit_index = i + 1

                metadata: dict[str, Any] = {
                    "model": self.config.model_name,
                    "model_tier": self._tier_label,
                    "instruction": instruction,
                    "thinking_level": (
                        thinking_level.value if self.config.supports_thinking else None
                    ),
                    "media_resolution": (
                        media_resolution.value
                        if self.config.supports_media_resolution
                        else None
                    ),
                    "source_mime_type": source_mime_type,
                    "result_mime_type": f"image/{self.config.default_image_format}",
                    "synthid_watermark": True,
                    "edit_index": edit_index,
                }

                if output_path:
                    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
                    image_hash = hashlib.md5(image_bytes, usedforsecurity=False).hexdigest()[:8]
                    default_filename = (
                        f"edit_{self._tier_label}_{timestamp}_{edit_index}_{image_hash}.{self.config.default_image_format}"
                    )

                    full_path = resolve_output_path(
                        output_path=output_path,
                        default_dir=os.path.dirname(output_path) or ".",
                        default_filename=default_filename,
                        image_index=edit_index,
                    )

                    os.makedirs(os.path.dirname(full_path) or ".", exist_ok=True)
                    _atomic_write_bytes(full_path, image_bytes)

                    with PILImage.open(BytesIO(image_bytes)) as img:
                        width, height = img.size

                    path_stem, _ = os.path.splitext(full_path)
                    thumb_path = f"{path_stem}_thumb.jpeg"
                    try:
                        create_thumbnail(full_path, thumb_path, size=256)
                        with open(thumb_path, "rb") as f:
                            thumb_data = f.read()
                        mcp_images.append(MCPImage(data=thumb_data, format="jpeg"))
                    except ImageProcessingError as e:
                        self.logger.warning(f"Thumbnail creation failed, using full image: {e}")
                        thumb_path = None
                        mcp_images.append(
                            MCPImage(data=image_bytes, format=self.config.default_image_format)
                        )

                    metadata.update(
                        {
                            "full_path": full_path,
                            "thumb_path": thumb_path,
                            "size_bytes": len(image_bytes),
                            "width": width,
                            "height": height,
                            "is_stored": True,
                            "output_path_used": True,
                        }
                    )

                elif use_storage and self.storage_service:
                    stored_info = self.storage_service.store_image(
                        image_bytes, f"image/{self.config.default_image_format}", metadata
                    )

                    thumbnail_b64 = self.storage_service.get_thumbnail_base64(stored_info.id)
                    if thumbnail_b64:
                        thumbnail_bytes = base64.b64decode(thumbnail_b64)
                        mcp_images.append(MCPImage(data=thumbnail_bytes, format="jpeg"))
                    else:
                        mcp_images.append(
                            MCPImage(data=image_bytes, format=self.config.default_image_format)
                        )

                    metadata.update(
                        {
                            "storage_id": stored_info.id,
                            "full_image_uri": f"file://images/{stored_info.id}",
                            "full_path": stored_info.full_path,
                            "thumbnail_uri": f"file://images/{stored_info.id}/thumbnail",
                            "size_bytes": stored_info.size_bytes,
                            "thumbnail_size_bytes": stored_info.thumbnail_size_bytes,
                            "width": stored_info.width,
                            "height": stored_info.height,
                            "expires_at": stored_info.expires_at,
                            "is_stored": True,
                        }
                    )
                else:
                    mcp_images.append(
                        MCPImage(data=image_bytes, format=self.config.default_image_format)
                    )

                all_metadata.append(metadata)

            progress.update(100, f"Edited image(s), returned {len(mcp_images)} result(s)")
            return mcp_images, all_metadata

    def edit_image(
        self,
        instruction: str,
        base_image_b64: str,
        mime_type: str = "image/png",
        thinking_level: ThinkingLevel | None = None,
        media_resolution: MediaResolution | None = None,
        use_storage: bool = True,
    ) -> tuple[list[MCPImage], int]:
        """
        Edit images with Pro model's enhanced understanding.

        Benefits:
        - Better context understanding
        - Higher quality edits
        - Maintains fine details

        Args:
            instruction: Natural language editing instruction
            base_image_b64: Base64 encoded source image
            mime_type: MIME type of source image
            thinking_level: Reasoning depth
            media_resolution: Vision processing detail level
            use_storage: Store edited images and return resource links

        Returns:
            Tuple of (edited_images_or_resource_links, count)
        """
        edited_images, _metadata = self.edit_images(
            instruction,
            base_image_b64=base_image_b64,
            mime_type=mime_type,
            thinking_level=thinking_level,
            media_resolution=media_resolution,
            use_storage=use_storage,
        )
        return edited_images, len(edited_images)

    def _enhance_prompt_for_pro(
        self, prompt: str, resolution: str, negative_prompt: str | None
    ) -> str:
        """
        Enhance prompt to leverage Pro model capabilities.

        Pro model benefits from:
        - Narrative, descriptive prompts
        - Specific composition/lighting details
        - Quality and detail emphasis
        """
        enhanced = prompt

        # Pro model benefits from narrative prompts
        if len(prompt) < 50:
            enhanced = (
                f"Create a high-quality, detailed image: {prompt}. "
                "Pay attention to composition, lighting, and fine details."
            )

        # Resolution hints for 4K/high-res
        if resolution in ["4k", "high", "2k"]:
            if "text" in prompt.lower() or "diagram" in prompt.lower():
                enhanced += " Ensure text is sharp and clearly readable at high resolution."
            if resolution == "4k":
                enhanced += " Render at maximum 4K quality with exceptional detail."

        # Negative constraints
        if negative_prompt:
            enhanced += f"\n\nAvoid: {negative_prompt}"

        return enhanced
