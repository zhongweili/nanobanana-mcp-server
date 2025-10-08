"""
Enhanced Image Service following workflows.md patterns.

Implements the complete workflow sequences:
1. Generation: M->G->FS->F->D (save full-res, create thumbnail, upload to Files API, track in DB)
2. Editing: M->F->G->FS->F->D (get file, edit, save, upload new, track with parent_file_id)
"""

from typing import List, Optional, Tuple, Dict, Any
from fastmcp.utilities.types import Image as MCPImage
from .gemini_client import GeminiClient
from .files_api_service import FilesAPIService
from .image_database_service import ImageDatabaseService
from ..utils.image_utils import create_thumbnail, validate_image_format
from ..config.settings import GeminiConfig
from ..config.constants import THUMBNAIL_SIZE, TEMP_FILE_SUFFIX
from PIL import Image as PILImage
import os
import logging
import mimetypes
import base64
from datetime import datetime
import hashlib
from io import BytesIO


class EnhancedImageService:
    """
    Enhanced image service implementing workflows.md patterns.

    Coordinates between:
    - Gemini API (G) for generation/editing
    - Local filesystem (FS) for full-res storage + 256px thumbnails
    - Files API (F) for cloud storage and sharing
    - Database (D) for metadata tracking and relationships
    """

    def __init__(
        self,
        gemini_client: GeminiClient,
        files_api_service: FilesAPIService,
        db_service: ImageDatabaseService,
        config: GeminiConfig,
        out_dir: Optional[str] = None,
    ):
        """
        Initialize enhanced image service.

        Args:
            gemini_client: Gemini API client
            files_api_service: Files API service
            db_service: Database service
            config: Gemini configuration
            out_dir: Output directory for images (defaults to OUT_DIR env var)
        """
        self.gemini_client = gemini_client
        self.files_api = files_api_service
        self.db_service = db_service
        self.config = config
        self.out_dir = out_dir or "output"
        self.logger = logging.getLogger(__name__)

        # Ensure output directory exists
        os.makedirs(self.out_dir, exist_ok=True)

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
        Generate images following the complete workflow from workflows.md.

        Implements sequence:
        1. M->>G: generateContent([text prompt])
        2. G-->>M: inline image bytes (base64)
        3. M->>FS: save full-res image
        4. M->>FS: create 256px thumbnail (JPEG)
        5. M->>F: files.upload(full-res path)
        6. F-->>M: { name:file_id, uri:file_uri }
        7. M->>D: upsert {path, thumb_path, mime, w,h, file_id, file_uri, expires_at}
        8. M-->>L: { path, thumb_data_url, mime, w,h, files_api:{name,uri} }

        Args:
            prompt: Main generation prompt
            n: Number of images to generate
            negative_prompt: Optional negative prompt
            system_instruction: Optional system instruction
            input_images: List of (base64, mime_type) tuples for input images
            aspect_ratio: Optional aspect ratio string (e.g., "16:9")

        Returns:
            Tuple of (thumbnail_images, metadata_list)
        """
        try:
            self.logger.info(f"Starting image generation: n={n}, prompt='{prompt[:50]}...'")

            # Step 1: Build content list for Gemini API
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

            # Generate all images
            all_thumbnail_images = []
            all_metadata = []

            for i in range(n):
                try:
                    self.logger.debug(f"Generating image {i + 1}/{n}...")

                    # Step 1-2: M->>G: generateContent -> G-->>M: inline image bytes
                    response = self.gemini_client.generate_content(
                        contents, aspect_ratio=aspect_ratio
                    )
                    images = self.gemini_client.extract_images(response)

                    for j, image_bytes in enumerate(images):
                        # Process each generated image through the full workflow
                        thumbnail_image, metadata = self._process_generated_image(
                            image_bytes,
                            i + 1,
                            j + 1,
                            prompt,
                            negative_prompt,
                            system_instruction,
                            aspect_ratio,
                        )

                        all_thumbnail_images.append(thumbnail_image)
                        all_metadata.append(metadata)

                except Exception as e:
                    self.logger.error(f"Failed to generate image {i + 1}: {e}")
                    # Continue with other images rather than failing completely
                    continue

            self.logger.info(f"Successfully generated {len(all_thumbnail_images)} images")
            return all_thumbnail_images, all_metadata

        except Exception as e:
            self.logger.error(f"Image generation failed: {e}")
            raise

    def edit_image_by_file_id(
        self, file_id: str, edit_prompt: str
    ) -> Tuple[List[MCPImage], List[Dict[str, Any]]]:
        """
        Edit image by file_id following workflows.md pattern.

        Implements sequence:
        1. M->>F: files.get(file_id)
        2. F-->>M: { uri, mime, status: valid } OR expired/not found
        3. If expired -> Lookup local path -> Re-upload if needed
        4. M->>G: generateContent([{file_data:{mime, uri}}, edit_prompt])
        5. G-->>M: inline edited image
        6. M->>FS: save new full-res image + new thumbnail
        7. M->>F: files.upload(new image)
        8. F-->>M: { name:new_file_id, uri:new_file_uri }
        9. M->>D: upsert {path2, parent_file_id:file_id, ...}
        10. M-->>L: { path2, thumb_data_url2, files_api:{name:new_file_id,uri:new_file_uri}, parent_file_id }

        Args:
            file_id: Files API file ID to edit
            edit_prompt: Natural language editing instruction

        Returns:
            Tuple of (thumbnail_images, metadata_list)
        """
        try:
            self.logger.info(
                f"Editing image by file_id: {file_id}, instruction: '{edit_prompt[:50]}...'"
            )

            # Step 1-3: Get file from Files API with fallback/re-upload handling
            file_data_part = self.files_api.create_file_data_part(file_id)

            # Step 4: M->>G: generateContent with file_data + edit_prompt
            contents = [file_data_part, edit_prompt]
            response = self.gemini_client.generate_content(contents)

            # Step 5: G-->>M: inline edited image
            edited_images = self.gemini_client.extract_images(response)

            if not edited_images:
                raise ValueError("No edited images returned from Gemini API")

            # Process each edited image through the full workflow
            all_thumbnail_images = []
            all_metadata = []

            for i, image_bytes in enumerate(edited_images):
                # Steps 6-9: Process edited image through full workflow
                thumbnail_image, metadata = self._process_edited_image(
                    image_bytes, edit_prompt, file_id, i + 1
                )

                all_thumbnail_images.append(thumbnail_image)
                all_metadata.append(metadata)

            self.logger.info(
                f"Successfully edited image, generated {len(all_thumbnail_images)} result(s)"
            )
            return all_thumbnail_images, all_metadata

        except Exception as e:
            self.logger.error(f"Image editing failed for {file_id}: {e}")
            raise

    def edit_image_by_path(
        self, instruction: str, file_path: str
    ) -> Tuple[List[MCPImage], List[Dict[str, Any]]]:
        """
        Edit image from local file path following workflows.md pattern for path-based editing.

        This handles editing images directly from the local filesystem without base64 encoding.

        Args:
            instruction: Natural language editing instruction
            file_path: Local path to the source image file

        Returns:
            Tuple of (thumbnail_images, metadata_list)
        """
        try:
            self.logger.info(
                f"Editing image from path: {file_path}, instruction: '{instruction[:50]}...'"
            )

            # Validate file exists and is readable
            if not os.path.exists(file_path):
                raise ValueError(f"Image file not found: {file_path}")

            # Read image file as bytes
            with open(file_path, "rb") as f:
                image_bytes = f.read()

            # Detect MIME type from file extension or content
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type or not mime_type.startswith("image/"):
                # Fallback to PNG if detection fails
                mime_type = "image/png"

            # Validate image format
            validate_image_format(mime_type)

            # Convert to base64 for Gemini API (only internally, not in tool interface)
            base_image_b64 = base64.b64encode(image_bytes).decode("utf-8")

            # Create parts for Gemini API
            image_parts = self.gemini_client.create_image_parts([base_image_b64], [mime_type])
            contents = image_parts + [instruction]

            # Generate edited image
            response = self.gemini_client.generate_content(contents)
            edited_images = self.gemini_client.extract_images(response)

            if not edited_images:
                raise ValueError("No edited images returned from Gemini API")

            # Process each edited image
            all_thumbnail_images = []
            all_metadata = []

            for i, edited_image_bytes in enumerate(edited_images):
                try:
                    thumbnail_image, metadata = self._process_edited_image(
                        edited_image_bytes, instruction, parent_file_id=None, edit_index=i + 1
                    )

                    all_thumbnail_images.append(thumbnail_image)
                    all_metadata.append(metadata)
                except Exception as e:
                    self.logger.error(f"Failed to process edited image {i + 1}: {e}")
                    # Continue with other images rather than failing completely
                    continue

            self.logger.info(
                f"Successfully edited image from path, generated {len(all_thumbnail_images)} result(s)"
            )
            return all_thumbnail_images, all_metadata

        except Exception as e:
            self.logger.error(f"Path-based image editing failed for {file_path}: {e}")
            raise

    def _process_generated_image(
        self,
        image_bytes: bytes,
        response_index: int,
        image_index: int,
        prompt: str,
        negative_prompt: Optional[str],
        system_instruction: Optional[str],
        aspect_ratio: Optional[str],
    ) -> Tuple[MCPImage, Dict[str, Any]]:
        """
        Process a generated image through the complete workflow.

        Steps 3-8 from workflows.md generation sequence.
        """
        # Step 3: M->>FS: save full-res image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_hash = hashlib.md5(image_bytes).hexdigest()[:8]
        filename = f"gen_{timestamp}_{response_index}_{image_index}_{image_hash}"

        full_path = os.path.join(self.out_dir, f"{filename}.{self.config.default_image_format}")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write image file atomically using temporary file
        temp_path = f"{full_path}{TEMP_FILE_SUFFIX}"
        try:
            with open(temp_path, "wb") as f:
                f.write(image_bytes)
            os.rename(temp_path, full_path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise ValueError(f"Failed to save image: {e}")

        # Get image dimensions directly from bytes to avoid extra file I/O
        try:
            with PILImage.open(BytesIO(image_bytes)) as img:
                width, height = img.size
        except Exception as e:
            # Fallback to file-based approach if bytes approach fails
            self.logger.warning(f"Using fallback image dimension detection: {e}")
            with PILImage.open(full_path) as img:
                width, height = img.size

        # Step 4: M->>FS: create thumbnail (JPEG)
        thumb_path = os.path.join(self.out_dir, f"{filename}_thumb.jpeg")
        create_thumbnail(full_path, thumb_path, size=THUMBNAIL_SIZE)

        # Step 5-6: M->>F: files.upload -> F-->>M: { name:file_id, uri:file_uri }
        try:
            file_id, file_uri = self.files_api.upload_and_track(
                full_path, display_name=f"Generated: {prompt[:30]}..."
            )
        except Exception as e:
            self.logger.warning(f"Failed to upload to Files API: {e}")
            file_id, file_uri = None, None

        # Step 7: M->>D: upsert database record
        generation_metadata = {
            "type": "generation",
            "response_index": response_index,
            "image_index": image_index,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "system_instruction": system_instruction,
            "aspect_ratio": aspect_ratio,
            "synthid_watermark": True,
        }

        record_id = self.db_service.upsert_image(
            path=full_path,
            thumb_path=thumb_path,
            mime_type=f"image/{self.config.default_image_format}",
            width=width,
            height=height,
            size_bytes=len(image_bytes),
            file_id=file_id,
            file_uri=file_uri,
            parent_file_id=None,
            metadata=generation_metadata,
        )

        # Step 8: Create thumbnail MCP image for response
        with open(thumb_path, "rb") as f:
            thumb_data = f.read()

        thumbnail_image = MCPImage(data=thumb_data, format="jpeg")

        # Build complete metadata response
        metadata = {
            **generation_metadata,
            "database_id": record_id,
            "full_path": full_path,
            "thumb_path": thumb_path,
            "width": width,
            "height": height,
            "size_bytes": len(image_bytes),
            "files_api": {"name": file_id, "uri": file_uri} if file_id else None,
        }

        return thumbnail_image, metadata

    def _process_edited_image(
        self, image_bytes: bytes, instruction: str, parent_file_id: Optional[str], edit_index: int
    ) -> Tuple[MCPImage, Dict[str, Any]]:
        """
        Process an edited image through the complete workflow.

        Steps 6-9 from workflows.md editing sequence.
        """
        # Step 6: M->>FS: save new full-res image + new thumbnail
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_hash = hashlib.md5(image_bytes).hexdigest()[:8]
        filename = f"edit_{timestamp}_{edit_index}_{image_hash}"

        full_path = os.path.join(self.out_dir, f"{filename}.{self.config.default_image_format}")
        with open(full_path, "wb") as f:
            f.write(image_bytes)

        # Get image dimensions
        with PILImage.open(full_path) as img:
            width, height = img.size

        # Create 256px thumbnail (JPEG)
        thumb_path = os.path.join(self.out_dir, f"{filename}_thumb.jpeg")
        create_thumbnail(full_path, thumb_path, size=256)

        # Step 7-8: M->>F: files.upload -> F-->>M: { name:new_file_id, uri:new_file_uri }
        try:
            new_file_id, new_file_uri = self.files_api.upload_and_track(
                full_path, display_name=f"Edited: {instruction[:30]}..."
            )
        except Exception as e:
            self.logger.warning(f"Failed to upload edited image to Files API: {e}")
            new_file_id, new_file_uri = None, None

        # Step 9: M->>D: upsert database record with parent_file_id
        edit_metadata = {
            "type": "edit",
            "instruction": instruction,
            "edit_index": edit_index,
            "parent_file_id": parent_file_id,
            "synthid_watermark": True,
        }

        record_id = self.db_service.upsert_image(
            path=full_path,
            thumb_path=thumb_path,
            mime_type=f"image/{self.config.default_image_format}",
            width=width,
            height=height,
            size_bytes=len(image_bytes),
            file_id=new_file_id,
            file_uri=new_file_uri,
            parent_file_id=parent_file_id,
            metadata=edit_metadata,
        )

        # Create thumbnail MCP image for response
        with open(thumb_path, "rb") as f:
            thumb_data = f.read()

        thumbnail_image = MCPImage(data=thumb_data, format="jpeg")

        # Build complete metadata response
        metadata = {
            **edit_metadata,
            "database_id": record_id,
            "full_path": full_path,
            "thumb_path": thumb_path,
            "width": width,
            "height": height,
            "size_bytes": len(image_bytes),
            "files_api": {"name": new_file_id, "uri": new_file_uri} if new_file_id else None,
        }

        return thumbnail_image, metadata
