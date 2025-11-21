from typing import List, Optional, Tuple, Dict, Any
from fastmcp.utilities.types import Image as MCPImage
from .gemini_client import GeminiClient
from .image_storage_service import ImageStorageService, StoredImageInfo
from ..utils.image_utils import validate_image_format, optimize_image_size
from ..config.settings import GeminiConfig
from ..core.progress_tracker import ProgressContext
import logging
import base64


class ImageService:
    """Service for image generation and editing operations."""

    def __init__(
        self,
        gemini_client: GeminiClient,
        config: GeminiConfig,
        storage_service: Optional[ImageStorageService] = None,
    ):
        self.gemini_client = gemini_client
        self.config = config
        self.storage_service = storage_service
        self.logger = logging.getLogger(__name__)

    def generate_images(
        self,
        prompt: str,
        n: int = 1,
        negative_prompt: Optional[str] = None,
        system_instruction: Optional[str] = None,
        input_images: Optional[List[Tuple[str, str]]] = None,
        aspect_ratio: Optional[str] = None,
        use_storage: bool = True,
    ) -> Tuple[List[MCPImage], List[Dict[str, Any]]]:
        """
        Generate images using Gemini API.

        Args:
            prompt: Main generation prompt
            n: Number of images to generate
            negative_prompt: Optional negative prompt
            system_instruction: Optional system instruction
            input_images: List of (base64, mime_type) tuples for input images
            aspect_ratio: Optional aspect ratio string (e.g., "16:9")
            use_storage: If True, store images and return resource links with thumbnails

        Returns:
            Tuple of (image_blocks_or_resource_links, metadata_list)
        """
        # Use progress tracking for better UX
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
            all_images = []
            all_metadata = []
            stored_images: List[StoredImageInfo] = []

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
                            f"Processing image {i + 1}.{j + 1}...",
                        )

                        # Generation metadata
                        generation_metadata = {
                            "response_index": i + 1,
                            "image_index": j + 1,
                            "mime_type": f"image/{self.config.default_image_format}",
                            "synthid_watermark": True,
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "system_instruction": system_instruction,
                            "aspect_ratio": aspect_ratio,
                        }

                        if use_storage and self.storage_service:
                            # Store image with automatic thumbnail generation
                            stored_info = self.storage_service.store_image(
                                image_bytes,
                                f"image/{self.config.default_image_format}",
                                generation_metadata,
                            )
                            stored_images.append(stored_info)

                            # Create thumbnail MCP image for preview
                            thumbnail_b64 = self.storage_service.get_thumbnail_base64(
                                stored_info.id
                            )
                            if thumbnail_b64:
                                thumbnail_bytes = base64.b64decode(thumbnail_b64)
                                thumbnail_image = MCPImage(data=thumbnail_bytes, format="jpeg")
                                all_images.append(thumbnail_image)

                            # Enhanced metadata with resource links
                            metadata = {
                                **generation_metadata,
                                "storage_id": stored_info.id,
                                "full_image_uri": f"file://images/{stored_info.id}",
                                "thumbnail_uri": f"file://images/{stored_info.id}/thumbnail",
                                "size_bytes": stored_info.size_bytes,
                                "thumbnail_size_bytes": stored_info.thumbnail_size_bytes,
                                "width": stored_info.width,
                                "height": stored_info.height,
                                "aspect_ratio": aspect_ratio,
                                "expires_at": stored_info.expires_at,
                                "is_stored": True,
                                "preview_mode": "thumbnail_with_resource_link",
                            }
                            all_metadata.append(metadata)

                            self.logger.info(
                                f"Stored image {i + 1}.{j + 1} as {stored_info.id} "
                                f"({stored_info.size_bytes} bytes, thumbnail: {stored_info.thumbnail_size_bytes} bytes)"
                            )
                        else:
                            # Fallback: optimize and return directly (old behavior)
                            optimized_b64 = optimize_image_size(
                                base64.b64encode(image_bytes).decode(), max_size=2 * 1024 * 1024
                            )
                            optimized_bytes = base64.b64decode(optimized_b64)

                            mcp_image = MCPImage(
                                data=optimized_bytes, format=self.config.default_image_format
                            )
                            all_images.append(mcp_image)
                            all_metadata.append(generation_metadata)

                            self.logger.info(
                                f"Generated image {i + 1}.{j + 1} (size: {len(optimized_bytes)} bytes)"
                            )

                except Exception as e:
                    self.logger.error(f"Failed to generate image {i + 1}: {e}")
                    # Continue with other images rather than failing completely
                    continue

            progress.update(90, f"Successfully generated {len(all_images)} image(s)")

            if use_storage and stored_images:
                progress.update(
                    100,
                    f"Generated and stored {len(stored_images)} image(s) with thumbnails and resource links",
                )
            else:
                progress.update(100, f"Generated {len(all_images)} image(s) using direct embedding")

            return all_images, all_metadata

    def edit_image(
        self,
        instruction: str,
        base_image_b64: str,
        mime_type: str = "image/png",
        use_storage: bool = True,
    ) -> Tuple[List[MCPImage], int]:
        """
        Edit an image using conversational instructions.

        Args:
            instruction: Natural language editing instruction
            base_image_b64: Base64 encoded source image
            mime_type: MIME type of source image
            use_storage: If True, store edited images and return resource links with thumbnails

        Returns:
            Tuple of (edited_images_or_resource_links, count)
        """
        # Use progress tracking for better UX
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

                # Convert to MCP images with storage support
                mcp_images = []
                for i, image_bytes in enumerate(image_bytes_list):
                    progress.update(
                        70 + (i * 20 // len(image_bytes_list)),
                        f"Processing result {i + 1}/{len(image_bytes_list)}...",
                    )

                    # Edit metadata
                    edit_metadata = {
                        "instruction": instruction,
                        "source_mime_type": mime_type,
                        "result_mime_type": f"image/{self.config.default_image_format}",
                        "synthid_watermark": True,
                        "edit_index": i + 1,
                    }

                    if use_storage and self.storage_service:
                        # Store edited image with automatic thumbnail generation
                        stored_info = self.storage_service.store_image(
                            image_bytes, f"image/{self.config.default_image_format}", edit_metadata
                        )

                        # Create thumbnail MCP image for preview
                        thumbnail_b64 = self.storage_service.get_thumbnail_base64(stored_info.id)
                        if thumbnail_b64:
                            thumbnail_bytes = base64.b64decode(thumbnail_b64)
                            thumbnail_image = MCPImage(data=thumbnail_bytes, format="jpeg")
                            mcp_images.append(thumbnail_image)

                        self.logger.info(
                            f"Stored edited image {i + 1} as {stored_info.id} "
                            f"({stored_info.size_bytes} bytes, thumbnail: {stored_info.thumbnail_size_bytes} bytes)"
                        )
                    else:
                        # Fallback: optimize and return directly (old behavior)
                        optimized_b64 = optimize_image_size(
                            base64.b64encode(image_bytes).decode(), max_size=5 * 1024 * 1024
                        )
                        optimized_bytes = base64.b64decode(optimized_b64)

                        mcp_image = MCPImage(
                            data=optimized_bytes, format=self.config.default_image_format
                        )
                        mcp_images.append(mcp_image)

                        self.logger.info(
                            f"Edited image optimized (size: {len(optimized_bytes)} bytes)"
                        )

                progress.update(
                    100, f"Successfully edited image, generated {len(mcp_images)} result(s)"
                )
                return mcp_images, len(mcp_images)

            except Exception as e:
                self.logger.error(f"Failed to edit image: {e}")
                raise
