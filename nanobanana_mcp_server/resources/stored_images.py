"""
Resource handler for serving stored images via file:// URIs.
Provides both full resolution and thumbnail access.
"""

from fastmcp import FastMCP
from typing import Dict, Any
import logging
import base64

from ..services import get_image_storage_service
from ..core.exceptions import ValidationError


def register_stored_image_resources(server: FastMCP):
    """Register stored image resources with the FastMCP server."""

    @server.resource("file://images/{image_id}")
    def get_stored_image(image_id: str) -> Dict[str, Any]:
        """
        Serve full resolution stored images.

        Args:
            image_id: Unique image identifier

        Returns:
            Resource dict with image data, mime type, and metadata
        """
        logger = logging.getLogger(__name__)

        try:
            logger.debug(f"Serving full image: {image_id}")

            storage_service = get_image_storage_service()

            # Get image info
            info = storage_service.get_image_info(image_id)
            if not info:
                return {
                    "error": "image_not_found",
                    "message": f"Image {image_id} not found or expired",
                    "image_id": image_id,
                }

            # Get image bytes
            image_bytes = storage_service.get_image_bytes(image_id, thumbnail=False)
            if not image_bytes:
                return {
                    "error": "image_read_error",
                    "message": f"Failed to read image {image_id}",
                    "image_id": image_id,
                }

            # Return resource data
            return {
                "mimeType": info.mime_type,
                "size": info.size_bytes,
                "data": base64.b64encode(image_bytes).decode(),
                "metadata": {
                    "width": info.width,
                    "height": info.height,
                    "created_at": info.created_at,
                    "expires_at": info.expires_at,
                    "generation_metadata": info.metadata,
                },
            }

        except ValidationError as e:
            logger.error(f"Validation error serving image {image_id}: {e}")
            return {"error": "validation_error", "message": str(e), "image_id": image_id}
        except Exception as e:
            logger.error(f"Error serving image {image_id}: {e}")
            return {"error": "server_error", "message": str(e), "image_id": image_id}

    @server.resource("file://images/{image_id}/thumbnail")
    def get_stored_thumbnail(image_id: str) -> Dict[str, Any]:
        """
        Serve thumbnail version of stored images.

        Args:
            image_id: Unique image identifier

        Returns:
            Resource dict with thumbnail data and metadata
        """
        logger = logging.getLogger(__name__)

        try:
            logger.debug(f"Serving thumbnail: {image_id}")

            storage_service = get_image_storage_service()

            # Get image info
            info = storage_service.get_image_info(image_id)
            if not info:
                return {
                    "error": "image_not_found",
                    "message": f"Image {image_id} not found or expired",
                    "image_id": image_id,
                }

            # Get thumbnail bytes
            thumbnail_bytes = storage_service.get_image_bytes(image_id, thumbnail=True)
            if not thumbnail_bytes:
                return {
                    "error": "thumbnail_read_error",
                    "message": f"Failed to read thumbnail for {image_id}",
                    "image_id": image_id,
                }

            # Return thumbnail resource data
            return {
                "mimeType": "image/jpeg",  # Thumbnails are always JPEG
                "size": info.thumbnail_size_bytes,
                "data": base64.b64encode(thumbnail_bytes).decode(),
                "metadata": {
                    "width": info.thumbnail_width,
                    "height": info.thumbnail_height,
                    "original_width": info.width,
                    "original_height": info.height,
                    "is_thumbnail": True,
                    "full_image_uri": f"file://images/{image_id}",
                },
            }

        except ValidationError as e:
            logger.error(f"Validation error serving thumbnail {image_id}: {e}")
            return {"error": "validation_error", "message": str(e), "image_id": image_id}
        except Exception as e:
            logger.error(f"Error serving thumbnail {image_id}: {e}")
            return {"error": "server_error", "message": str(e), "image_id": image_id}

    @server.resource("file://images")
    def list_stored_images() -> Dict[str, Any]:
        """
        List all currently stored images with metadata.

        Returns:
            Dict with image list and storage statistics
        """
        logger = logging.getLogger(__name__)

        try:
            storage_service = get_image_storage_service()

            # Get all images
            images = storage_service.list_images(include_expired=False)

            # Get storage stats
            stats = storage_service.get_storage_stats()

            # Format image list
            image_list = []
            for info in images:
                image_list.append(
                    {
                        "id": info.id,
                        "filename": info.filename,
                        "mime_type": info.mime_type,
                        "size_bytes": info.size_bytes,
                        "width": info.width,
                        "height": info.height,
                        "created_at": info.created_at,
                        "expires_at": info.expires_at,
                        "full_uri": f"file://images/{info.id}",
                        "thumbnail_uri": f"file://images/{info.id}/thumbnail",
                        "metadata": info.metadata,
                    }
                )

            return {"images": image_list, "count": len(image_list), "storage_stats": stats}

        except Exception as e:
            logger.error(f"Error listing images: {e}")
            return {"error": "server_error", "message": str(e), "images": [], "count": 0}
