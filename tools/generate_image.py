from typing import Annotated, Optional, List
from pydantic import Field
from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult
from mcp.types import ResourceLink, TextContent
from core.exceptions import ValidationError
import logging

def register_generate_image_tool(server: FastMCP):
    """Register the generate_image tool with the FastMCP server."""
    
    @server.tool(
        annotations={
            "title": "Generate image (Gemini 2.5 Flash Image)",
            "readOnlyHint": True,
            "openWorldHint": True,
        }
    )
    def generate_image(
        prompt: Annotated[str, Field(
            description="Clear, detailed image prompt. Include subject, composition, "
                       "action, location, style, and any text to render. Add 'Square image' "
                       "or '16:9' in the text to influence aspect ratio.",
            min_length=1,
            max_length=8192
        )],
        n: Annotated[int, Field(
            description="Requested image count (model may return fewer).",
            ge=1,
            le=4
        )] = 1,
        negative_prompt: Annotated[Optional[str], Field(
            description="Things to avoid (style, objects, text).",
            max_length=1024
        )] = None,
        system_instruction: Annotated[Optional[str], Field(
            description="Optional system tone/style guidance.",
            max_length=512
        )] = None,
        images_b64: Annotated[Optional[List[str]], Field(
            description="Inline base64 input images for composition/editing.",
            max_length=4
        )] = None,
        mime_types: Annotated[Optional[List[str]], Field(
            description="MIME types matching images_b64."
        )] = None,
        ctx: Context = None,
    ) -> ToolResult:
        """
        Generate one or more images from a text prompt, optionally conditioned on input images.
        Returns both MCP image content blocks and structured JSON with metadata.
        """
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Generate image request: prompt='{prompt[:50]}...', n={n}")
            
            # Validation
            if images_b64 and mime_types:
                if len(images_b64) != len(mime_types):
                    raise ValidationError("images_b64 and mime_types must have same length")
            elif images_b64 or mime_types:
                raise ValidationError("Both images_b64 and mime_types must be provided together")
            
            # Get services (would be injected in real implementation)
            image_service = _get_image_service()
            
            # Prepare input images
            input_images = None
            if images_b64 and mime_types:
                input_images = list(zip(images_b64, mime_types))
            
            # Generate images and save to file system
            thumbnail_images, metadata = image_service.generate_images(
                prompt=prompt,
                n=n,
                negative_prompt=negative_prompt,
                system_instruction=system_instruction,
                input_images=input_images
            )
            
            # Create response with file paths and thumbnails
            if metadata:
                # Build summary with file information
                summary_lines = [
                    f"✅ Generated {len(metadata)} image(s) with Gemini 2.5 Flash Image."
                ]
                
                if input_images:
                    summary_lines.append("🖼️ Included edits/conditioning from provided image(s).")
                
                # Add file information
                summary_lines.append("\n📁 **Saved Images:**")
                for i, meta in enumerate(metadata, 1):
                    size_mb = round(meta['size_bytes'] / (1024 * 1024), 1)
                    summary_lines.append(
                        f"  {i}. `{meta['full_path']}`\n"
                        f"     📏 {meta['width']}×{meta['height']} • 💾 {size_mb}MB"
                    )
                
                summary_lines.append(f"\n🖼️ **Thumbnail previews shown below** (actual images saved to disk)")
                full_summary = "\n".join(summary_lines)
                
                content = [TextContent(type="text", text=full_summary)] + thumbnail_images
            else:
                # Fallback if no images generated
                summary = "❌ No images were generated. Please check the logs for details."
                content = [TextContent(type="text", text=summary)]
            
            structured_content = {
                "requested": n,
                "returned": len(thumbnail_images),
                "negative_prompt_applied": bool(negative_prompt),
                "used_inline_images": bool(images_b64),
                "output_method": "file_system",
                "images": metadata,
                "file_paths": [m.get('full_path') for m in metadata if m.get('full_path')],
                "total_size_mb": round(sum(m.get('size_bytes', 0) for m in metadata) / (1024 * 1024), 2)
            }
            
            logger.info(f"Successfully generated {len(thumbnail_images)} images")
            
            return ToolResult(
                content=content,
                structured_content=structured_content
            )
            
        except ValidationError as e:
            logger.error(f"Validation error in generate_image: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in generate_image: {e}")
            raise

def _get_image_service():
    """Get the image service instance (would be dependency injection in real app)."""
    # This would be properly injected in a real implementation
    from services import get_image_service
    return get_image_service()