"""
Tool for getting output directory statistics.
"""

from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from ..services import get_file_image_service
import logging


def register_output_stats_tool(server: FastMCP):
    """Register output statistics tool with the FastMCP server."""

    @server.tool(
        annotations={
            "title": "Show output directory stats",
            "description": "Show statistics about the IMAGE_OUTPUT_DIR and recently generated images",
            "readOnlyHint": True,
        }
    )
    def show_output_stats(
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
                    content=[
                        TextContent(
                            type="text", text=f"❌ Error getting output stats: {stats['error']}"
                        )
                    ],
                    structured_content=stats,
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
                content=[TextContent(type="text", text=summary)], structured_content=stats
            )

        except Exception as e:
            logger.error(f"Failed to get output stats: {e}")
            raise
