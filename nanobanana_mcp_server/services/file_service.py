from typing import Optional, Dict, Any
from .gemini_client import GeminiClient
from ..core.exceptions import FileOperationError, ValidationError
from ..core.validation import validate_file_path
import logging
import os


class FileService:
    """Service for file management operations."""

    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        self.logger = logging.getLogger(__name__)

    def upload_file(self, file_path: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a file to Gemini Files API.

        Args:
            file_path: Path to the file to upload
            display_name: Optional display name for the file

        Returns:
            Dictionary with file metadata
        """
        try:
            # Validate file path
            validate_file_path(file_path)

            self.logger.info(f"Uploading file: {file_path}")

            # Check file size
            file_size = os.path.getsize(file_path)
            max_size = 100 * 1024 * 1024  # 100MB limit for Files API

            if file_size > max_size:
                raise ValidationError(
                    f"File size ({file_size} bytes) exceeds maximum ({max_size} bytes)"
                )

            # Upload file
            file_obj = self.gemini_client.upload_file(file_path, display_name)

            # Extract metadata
            metadata = {
                "uri": file_obj.uri,
                "name": file_obj.name,
                "mime_type": getattr(file_obj, "mime_type", None),
                "size_bytes": getattr(file_obj, "size_bytes", file_size),
                "display_name": display_name or os.path.basename(file_path),
                "original_path": file_path,
            }

            self.logger.info(f"Successfully uploaded file: {file_obj.name}")
            return metadata

        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            self.logger.error(f"Failed to upload file {file_path}: {e}")
            raise FileOperationError(f"File upload failed: {e}")

    def get_file_metadata(self, file_name: str) -> Dict[str, Any]:
        """
        Get metadata for a file from Gemini Files API.

        Args:
            file_name: Name of the file (e.g., 'files/abc123')

        Returns:
            Dictionary with file metadata
        """
        try:
            if not file_name or not file_name.strip():
                raise ValidationError("File name cannot be empty")

            self.logger.debug(f"Getting metadata for file: {file_name}")

            file_obj = self.gemini_client.get_file_metadata(file_name)

            # Extract metadata
            metadata = {
                "name": file_obj.name,
                "uri": file_obj.uri,
                "mime_type": getattr(file_obj, "mime_type", None),
                "size_bytes": getattr(file_obj, "size_bytes", None),
                "create_time": getattr(file_obj, "create_time", None),
                "update_time": getattr(file_obj, "update_time", None),
                "display_name": getattr(file_obj, "display_name", None),
                "state": getattr(file_obj, "state", None),
            }

            self.logger.debug(f"Retrieved metadata for: {file_obj.name}")
            return metadata

        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            self.logger.error(f"Failed to get file metadata for {file_name}: {e}")
            raise FileOperationError(f"Failed to get file metadata: {e}")

    def list_files(self) -> Dict[str, Any]:
        """
        List files in Gemini Files API.

        Returns:
            Dictionary with file list and summary
        """
        try:
            self.logger.debug("Listing files from Gemini Files API")

            # This would require implementing the list files functionality
            # in the GeminiClient if available in the API
            files = self.gemini_client.client.files.list()

            file_list = []
            total_size = 0

            for file_obj in files:
                file_info = {
                    "name": file_obj.name,
                    "uri": file_obj.uri,
                    "mime_type": getattr(file_obj, "mime_type", None),
                    "size_bytes": getattr(file_obj, "size_bytes", 0),
                    "display_name": getattr(file_obj, "display_name", None),
                }
                file_list.append(file_info)
                total_size += file_info["size_bytes"]

            summary = {"files": file_list, "count": len(file_list), "total_size_bytes": total_size}

            self.logger.debug(f"Found {len(file_list)} files, total size: {total_size} bytes")
            return summary

        except Exception as e:
            self.logger.error(f"Failed to list files: {e}")
            raise FileOperationError(f"Failed to list files: {e}")

    def delete_file(self, file_name: str) -> bool:
        """
        Delete a file from Gemini Files API.

        Args:
            file_name: Name of the file to delete

        Returns:
            True if deletion was successful
        """
        try:
            if not file_name or not file_name.strip():
                raise ValidationError("File name cannot be empty")

            self.logger.info(f"Deleting file: {file_name}")

            # This would require implementing delete functionality
            # in the GeminiClient if available in the API
            self.gemini_client.client.files.delete(name=file_name)

            self.logger.info(f"Successfully deleted file: {file_name}")
            return True

        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            self.logger.error(f"Failed to delete file {file_name}: {e}")
            raise FileOperationError(f"Failed to delete file: {e}")

    def get_file_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for uploaded files.

        Returns:
            Dictionary with usage statistics
        """
        try:
            files_info = self.list_files()

            stats = {
                "total_files": files_info["count"],
                "total_size_bytes": files_info["total_size_bytes"],
                "total_size_mb": round(files_info["total_size_bytes"] / (1024 * 1024), 2),
                "file_types": {},
            }

            # Analyze file types
            for file_info in files_info["files"]:
                mime_type = file_info.get("mime_type", "unknown")
                if mime_type not in stats["file_types"]:
                    stats["file_types"][mime_type] = {"count": 0, "total_size_bytes": 0}
                stats["file_types"][mime_type]["count"] += 1
                stats["file_types"][mime_type]["total_size_bytes"] += file_info["size_bytes"]

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get usage stats: {e}")
            raise FileOperationError(f"Failed to get usage stats: {e}")
