from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult
from mcp.types import ResourceLink, TextContent
from core.exceptions import ValidationError
import logging

def register_edit_image_tool(server: FastMCP):
    """Register the edit_image tool with the FastMCP server."""
    
    @server.tool(
        annotations={
            "title": "Edit image (conversational)",
            "readOnlyHint": True,
            "openWorldHint": True
        }
    )
    def edit_image(
        instruction: Annotated[str, Field(
            description="Conversational edit instruction. "
                       "e.g., 'Add a knitted wizard hat to the cat.'",
            min_length=1,
            max_length=2048
        )],
        base_image_b64: Annotated[str, Field(
            description="Base64 image to edit."
        )],
        mime_type: Annotated[str, Field(
            description="MIME type, e.g., image/png or image/jpeg"
        )] = "image/png",
        ctx: Context = None,
    ) -> ToolResult:
        """
        Perform a precise, style-preserving edit on a single input image using a natural-language instruction.
        """
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Edit image request: instruction='{instruction[:50]}...', mime_type={mime_type}")
            
            # Get service (would be injected in real implementation)
            image_service = _get_image_service()
            
            # Edit image and save to file system
            thumbnail_images, metadata = image_service.edit_image(
                instruction=instruction,
                base_image_b64=base_image_b64,
                mime_type=mime_type
            )
            
            # Create response with file paths and thumbnails
            if metadata:
                # Build summary with file information
                summary_lines = [
                    f"✅ Applied edit: '{instruction}'"
                ]
                
                # Add file information
                summary_lines.append("\n📁 **Edited Images:**")
                for i, meta in enumerate(metadata, 1):
                    size_mb = round(meta['size_bytes'] / (1024 * 1024), 1)
                    summary_lines.append(
                        f"  {i}. `{meta['full_path']}`\n"
                        f"     📏 {meta['width']}×{meta['height']} • 💾 {size_mb}MB"
                    )
                
                summary_lines.append(f"\n🖼️ **Thumbnail preview shown below** (actual image saved to disk)")
                full_summary = "\n".join(summary_lines)
                
                content = [TextContent(type="text", text=full_summary)] + thumbnail_images
            else:
                # Fallback if no images generated
                summary = f"❌ Failed to edit image: {instruction}. Please check the logs for details."
                content = [TextContent(type="text", text=summary)]
            
            structured_content = {
                "returned": len(thumbnail_images),
                "synthid_watermark": True,
                "instruction_applied": instruction,
                "output_method": "file_system",
                "images": metadata,
                "file_paths": [m.get('full_path') for m in metadata if m.get('full_path')],
                "total_size_mb": round(sum(m.get('size_bytes', 0) for m in metadata) / (1024 * 1024), 2)
            }
            
            logger.info(f"Successfully edited image, generated {len(thumbnail_images)} result(s)")
            
            return ToolResult(
                content=content,
                structured_content=structured_content
            )
            
        except ValidationError as e:
            logger.error(f"Validation error in edit_image: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in edit_image: {e}")
            raise

def _get_image_service():
    """Get the image service instance (would be dependency injection in real app)."""
    # This would be properly injected in a real implementation
    from services import get_image_service
    return get_image_service()