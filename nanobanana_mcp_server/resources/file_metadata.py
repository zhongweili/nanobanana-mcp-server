from fastmcp import FastMCP
from typing import Dict, Any
from ..services import get_file_service
from ..core.exceptions import FileOperationError, ValidationError
import logging


def register_file_metadata_resource(server: FastMCP):
    """Register the file metadata resource with the FastMCP server."""

    @server.resource("gemini://files/{name}")
    def file_metadata(name: str) -> Dict[str, Any]:
        """
        Fetch Files API metadata by file 'name' (like 'files/abc123').
        """
        logger = logging.getLogger(__name__)

        try:
            logger.debug(f"Fetching metadata for file: {name}")

            # Get service
            file_service = get_file_service()

            # Get file metadata
            metadata = file_service.get_file_metadata(name)

            logger.debug(f"Successfully retrieved metadata for: {name}")
            return metadata

        except ValidationError as e:
            logger.error(f"Validation error in file_metadata: {e}")
            return {"error": "validation_error", "message": str(e), "name": name}
        except FileOperationError as e:
            logger.error(f"File operation error in file_metadata: {e}")
            return {"error": "file_operation_error", "message": str(e), "name": name}
        except Exception as e:
            logger.error(f"Unexpected error in file_metadata: {e}")
            return {"error": "unexpected_error", "message": str(e), "name": name}
