"""
Tools for managing stored images - listing, deleting, and getting statistics.
"""

from typing import Annotated, Optional, List, Dict, Any
from pydantic import Field
from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from core.exceptions import ValidationError
from services import get_file_image_service
import logging


def register_image_management_tools(server: FastMCP):
    """Register image management tools with the FastMCP server."""
    
    @server.tool(
        annotations={
            "title": "List output directory stats",
            "description": "Show statistics about the output directory and recent images",
            "readOnlyHint": True
        }
    )
    def list_output_stats(
        ctx: Context = None,
    ) -> ToolResult:
        """
        Show statistics about the output directory and recently generated images.
        """
        logger = logging.getLogger(__name__)
        
        try:
            logger.info("Getting output directory stats")
            
            file_service = get_file_image_service()
            stats = file_service.get_output_stats()
            
            if "error" in stats:
                return ToolResult(
                    content=[TextContent(type="text", text=f"❌ Error getting output stats: {stats['error']}")],
                    structured_content=stats
                )
            
            if stats["total_images"] == 0:
                summary = (
                    f"📁 **Output Directory:** `{stats['output_directory']}`\n\n"
                    f"📊 **Stats:** No images found in output directory."
                )
            else:
                summary = (
                    f"📁 **Output Directory:** `{stats['output_directory']}`\n\n"
                    f"📊 **Stats:**\n"
                    f"- Total images: {stats['total_images']}\n"
                    f"- Total size: {stats['total_size_mb']} MB\n\n"
                    f"🕒 **Recent Images:**\n"
                )
                
                for filename in stats.get("recent_images", []):
                    summary += f"- `{filename}`\n"
            
            return ToolResult(
                content=[TextContent(type="text", text=summary)],
                structured_content=stats
            )
            
        except Exception as e:
            logger.error(f"Failed to get output stats: {e}")
            raise
    
    @server.tool(
        annotations={
            "title": "Delete stored image",
            "description": "Delete a stored image and its thumbnail by ID"
        }
    )
    def delete_stored_image(
        image_id: Annotated[str, Field(
            description="ID of the image to delete",
            min_length=1
        )],
        ctx: Context = None,
    ) -> ToolResult:
        """
        Delete a stored image and its thumbnail by ID.
        This will remove the image files and free up storage space.
        """
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Deleting stored image: {image_id}")
            
            storage_service = get_image_storage_service()
            
            # Get image info first
            info = storage_service.get_image_info(image_id)
            if not info:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Image '{image_id}' not found or already expired.")],
                    structured_content={
                        "success": False,
                        "image_id": image_id,
                        "error": "image_not_found"
                    }
                )
            
            # Delete the image
            success = storage_service.delete_image(image_id)
            
            if success:
                size_mb = round(info.size_bytes / (1024 * 1024), 2)
                return ToolResult(
                    content=[TextContent(type="text", text=f"Successfully deleted image '{image_id}' ({size_mb}MB) and its thumbnail.")],
                    structured_content={
                        "success": True,
                        "image_id": image_id,
                        "freed_bytes": info.size_bytes + info.thumbnail_size_bytes
                    }
                )
            else:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Failed to delete image '{image_id}'. Check logs for details.")],
                    structured_content={
                        "success": False,
                        "image_id": image_id,
                        "error": "deletion_failed"
                    }
                )
            
        except ValidationError as e:
            logger.error(f"Validation error deleting image {image_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to delete image {image_id}: {e}")
            raise
    
    @server.tool(
        annotations={
            "title": "Cleanup expired images", 
            "description": "Remove all expired images to free up storage space",
            "readOnlyHint": False
        }
    )
    def cleanup_expired_images(
        ctx: Context = None,
    ) -> ToolResult:
        """
        Remove all expired images to free up storage space.
        This is automatically done during normal operations, but can be triggered manually.
        """
        logger = logging.getLogger(__name__)
        
        try:
            logger.info("Cleaning up expired images")
            
            storage_service = get_image_storage_service()
            
            # Get stats before cleanup
            before_stats = storage_service.get_storage_stats()
            before_count = before_stats['total_images']
            before_size_mb = before_stats['total_size_mb']
            
            # Force cleanup (this is normally done automatically)
            storage_service._cleanup_expired()
            
            # Get stats after cleanup
            after_stats = storage_service.get_storage_stats()
            after_count = after_stats['total_images'] 
            after_size_mb = after_stats['total_size_mb']
            
            cleaned_count = before_count - after_count
            freed_mb = before_size_mb - after_size_mb
            
            if cleaned_count > 0:
                summary = (
                    f"Cleaned up {cleaned_count} expired image(s), "
                    f"freed {freed_mb:.2f}MB of storage space.\n\n"
                    f"Remaining: {after_count} images ({after_size_mb:.2f}MB)"
                )
            else:
                summary = f"No expired images found. Current: {after_count} images ({after_size_mb:.2f}MB)"
            
            return ToolResult(
                content=[TextContent(type="text", text=summary)],
                structured_content={
                    "cleaned_count": cleaned_count,
                    "freed_mb": freed_mb,
                    "remaining_count": after_count,
                    "remaining_size_mb": after_size_mb,
                    "storage_stats": after_stats
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired images: {e}")
            raise