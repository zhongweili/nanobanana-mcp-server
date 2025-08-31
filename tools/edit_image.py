from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult
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
            
            # Edit image
            mcp_images, count = image_service.edit_image(
                instruction=instruction,
                base_image_b64=base_image_b64,
                mime_type=mime_type
            )
            
            # Create response
            summary = f"Applied edit: {instruction}"
            
            structured_content = {
                "returned": count,
                "synthid_watermark": True,
                "instruction_applied": instruction
            }
            
            logger.info(f"Successfully edited image, generated {count} result(s)")
            
            return ToolResult(
                content=[summary] + mcp_images,
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