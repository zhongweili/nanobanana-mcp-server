import os
from typing import Annotated, Optional
from pydantic import Field
from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult
from ..core.exceptions import ValidationError, FileOperationError
from ..utils.client_errors import client_safe_message
from ..utils.concurrency_limit import limit_tool_concurrency
import logging


def register_upload_file_tool(server: FastMCP):
    """Register the upload_file tool with the FastMCP server."""

    @server.tool(
        annotations={
            "title": "Upload file to Gemini Files API",
            "readOnlyHint": False,
            "openWorldHint": True,
        }
    )
    @limit_tool_concurrency
    def upload_file(
        path: Annotated[
            str,
            Field(
                description="Server-accessible file path to upload to Gemini Files API.",
                min_length=1,
                max_length=512,
            ),
        ],
        display_name: Annotated[
            Optional[str],
            Field(description="Optional display name for the uploaded file.", max_length=256),
        ] = None,
        ctx: Context = None,
    ) -> ToolResult:
        """
        Upload a local file through the Gemini Files API and return its URI & metadata.
        Useful when the image is larger than 20MB or reused across prompts.
        """
        logger = logging.getLogger(__name__)

        try:
            logger.info(
                "Upload file request: basename=%s, display_name=%s",
                os.path.basename(path),
                display_name,
            )

            # Get service (would be injected in real implementation)
            file_service = _get_file_service()

            # Upload file
            metadata = file_service.upload_file(path, display_name)

            # Create response
            summary = f"Successfully uploaded file: {metadata['name']}"

            # Return as structured content (not image blocks)
            logger.info(f"Successfully uploaded file: {metadata['name']}")

            return ToolResult(
                content=[summary], structured_content={"success": True, "file": metadata}
            )

        except ValidationError as e:
            logger.error(f"Validation error in upload_file: {e}")
            return ToolResult(
                content=[f"Validation error: {e}"],
                structured_content={"error": "validation_error", "message": str(e)},
            )
        except FileOperationError as e:
            logger.error(f"File operation error in upload_file: {e}")
            safe = client_safe_message(str(e))
            return ToolResult(
                content=[f"File upload failed: {safe}"],
                structured_content={"error": "file_operation_error", "message": safe},
            )
        except Exception as e:
            logger.error(f"Unexpected error in upload_file: {e}")
            raise


def _get_file_service():
    """Get the file service instance."""
    from ..services import get_file_service

    return get_file_service()
