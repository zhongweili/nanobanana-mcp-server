"""
Files API Service - Enhanced integration with Gemini Files API.

Implements the Files API layer (F) shown in workflows.md:
- Upload full-resolution images to Files API
- Manage file expiration and re-upload workflows
- Handle file retrieval and validation
- Coordinate with database for metadata tracking
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import os
import logging
from .gemini_client import GeminiClient
from .image_database_service import ImageDatabaseService, ImageRecord
from ..core.exceptions import FileOperationError


class FilesAPIService:
    """Enhanced Files API service with database integration and expiration handling."""

    def __init__(self, gemini_client: GeminiClient, db_service: ImageDatabaseService):
        """
        Initialize Files API service.

        Args:
            gemini_client: Gemini client for API operations
            db_service: Database service for metadata tracking
        """
        self.gemini_client = gemini_client
        self.db_service = db_service
        self.logger = logging.getLogger(__name__)

    def upload_and_track(
        self, file_path: str, display_name: Optional[str] = None, record_id: Optional[int] = None
    ) -> Tuple[str, str]:
        """
        Upload file to Files API and update database tracking.

        Implements: M->>F: files.upload(full-res path) -> F-->>M: { name:file_id, uri:file_uri }

        Args:
            file_path: Local path to file to upload
            display_name: Optional display name for the file
            record_id: Optional database record ID to update with Files API info

        Returns:
            Tuple of (file_id, file_uri)
        """
        try:
            self.logger.info(f"Uploading {file_path} to Files API")

            # Validate file exists
            if not os.path.exists(file_path):
                raise FileOperationError(f"File not found: {file_path}")

            # Upload to Files API
            file_obj = self.gemini_client.upload_file(file_path, display_name)
            file_id = file_obj.name  # e.g., 'files/abc123'
            file_uri = file_obj.uri

            # Calculate expiration time (~48h from now)
            expires_at = datetime.now() + timedelta(hours=48)

            # Update database record if provided
            if record_id:
                success = self.db_service.update_files_api_info(
                    record_id, file_id, file_uri, expires_at
                )
                if not success:
                    self.logger.warning(f"Could not update database record {record_id}")

            self.logger.info(
                f"Successfully uploaded {file_path} -> {file_id} (expires: {expires_at})"
            )

            return file_id, file_uri

        except Exception as e:
            self.logger.error(f"Failed to upload {file_path}: {e}")
            raise FileOperationError(f"Files API upload failed: {e}")

    def get_file_with_fallback(self, file_id: str) -> Tuple[Optional[str], Optional[ImageRecord]]:
        """
        Get file from Files API with fallback to local re-upload.

        Implements the flowchart logic from workflows.md:
        - files.get(file_id)
        - If expired/not found -> Lookup local path by file_id in DB
        - If path found -> files.upload(path) -> new_file_id
        - If path missing -> Return error: artifact unavailable

        Args:
            file_id: Files API file ID (e.g., 'files/abc123')

        Returns:
            Tuple of (file_uri_or_none, database_record_or_none)
            - If successful: (file_uri, record)
            - If needs re-upload: (None, record_with_local_path)
            - If unavailable: (None, None)
        """
        try:
            self.logger.debug(f"Getting file {file_id} from Files API")

            # Try to get file from Files API
            try:
                file_obj = self.gemini_client.get_file_metadata(file_id)

                # Check if file is still valid (not expired or in error state)
                file_state = getattr(file_obj, "state", "ACTIVE")
                if file_state == "ACTIVE":
                    # File is still valid
                    record = self.db_service.get_by_file_id(file_id)
                    return file_obj.uri, record
                else:
                    self.logger.info(f"File {file_id} is in state: {file_state}")

            except Exception as api_error:
                self.logger.info(f"Files API error for {file_id}: {api_error}")

            # File is expired, not found, or in error state
            # Look up local path in database
            record = self.db_service.get_by_file_id(file_id)
            if not record:
                self.logger.warning(f"No database record found for file_id {file_id}")
                return None, None

            # Check if local file still exists
            if not os.path.exists(record.path):
                self.logger.error(f"Local file missing for {file_id}: {record.path}")
                # Clean up the database record
                self.db_service.clear_files_api_info(record.id)
                return None, None

            # File exists locally but needs re-upload
            self.logger.info(
                f"File {file_id} expired/unavailable, local file available: {record.path}"
            )
            return None, record

        except Exception as e:
            self.logger.error(f"Error in get_file_with_fallback for {file_id}: {e}")
            return None, None

    def ensure_file_available(self, file_id: str) -> Tuple[str, str]:
        """
        Ensure file is available in Files API, re-uploading if necessary.

        Args:
            file_id: Files API file ID

        Returns:
            Tuple of (current_file_id, file_uri)
            - May be different from input file_id if re-upload occurred

        Raises:
            FileOperationError: If file cannot be made available
        """
        file_uri, record = self.get_file_with_fallback(file_id)

        if file_uri:
            # File is already available
            return file_id, file_uri

        if not record:
            # File is completely unavailable
            raise FileOperationError(f"Artifact unavailable: {file_id}")

        # Re-upload the file
        try:
            new_file_id, new_file_uri = self.upload_and_track(
                record.path, display_name=f"Re-upload of {file_id}", record_id=record.id
            )

            self.logger.info(f"Re-uploaded {file_id} -> {new_file_id}")
            return new_file_id, new_file_uri

        except Exception as e:
            self.logger.error(f"Failed to re-upload {file_id}: {e}")
            raise FileOperationError(f"Failed to re-upload expired file: {e}")

    def create_file_data_part(self, file_id: str) -> Dict[str, Any]:
        """
        Create file_data part for Gemini API calls.

        Ensures file is available and creates the proper file_data structure:
        {file_data: {mime_type: "image/jpeg", uri: "https://..."}}

        Args:
            file_id: Files API file ID

        Returns:
            Dictionary with file_data structure for Gemini API

        Raises:
            FileOperationError: If file cannot be made available
        """
        try:
            # Ensure file is available (handles re-upload if needed)
            current_file_id, file_uri = self.ensure_file_available(file_id)

            # Get record for mime_type
            record = self.db_service.get_by_file_id(current_file_id)
            if not record:
                # Fallback to default mime type
                mime_type = "image/jpeg"
            else:
                mime_type = record.mime_type

            file_data_part = {"file_data": {"mime_type": mime_type, "uri": file_uri}}

            self.logger.debug(f"Created file_data part for {file_id} -> {current_file_id}")
            return file_data_part

        except Exception as e:
            self.logger.error(f"Failed to create file_data part for {file_id}: {e}")
            raise

    def cleanup_expired_files(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Clean up expired Files API entries.

        Args:
            dry_run: If True, only report what would be cleaned up

        Returns:
            Dictionary with cleanup statistics
        """
        try:
            # Get expired files from database
            expired_records = self.db_service.list_expired_files(buffer_minutes=0)

            cleanup_stats = {
                "expired_count": len(expired_records),
                "cleared_count": 0,
                "errors": [],
            }

            if not expired_records:
                self.logger.info("No expired Files API entries found")
                return cleanup_stats

            self.logger.info(f"Found {len(expired_records)} expired Files API entries")

            for record in expired_records:
                try:
                    if dry_run:
                        self.logger.info(f"Would clear: {record.file_id} (record {record.id})")
                    else:
                        # Clear Files API info from database
                        self.db_service.clear_files_api_info(record.id)
                        cleanup_stats["cleared_count"] += 1
                        self.logger.debug(f"Cleared expired entry: {record.file_id}")

                except Exception as e:
                    error_msg = f"Error processing {record.file_id}: {e}"
                    cleanup_stats["errors"].append(error_msg)
                    self.logger.error(error_msg)

            if not dry_run:
                self.logger.info(
                    f"Cleanup complete: cleared {cleanup_stats['cleared_count']} expired entries"
                )

            return cleanup_stats

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            raise

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get Files API usage statistics.

        Returns:
            Dictionary with usage statistics including database stats
        """
        try:
            # Get database statistics
            db_stats = self.db_service.get_usage_stats()

            # Try to get Files API quota information if available
            # Note: This would require additional API calls if supported

            stats = {
                **db_stats,
                "files_api_quota_gb": 20,  # Files API limit (~20GB)
                "estimated_usage_gb": round(db_stats["total_size_bytes"] / (1024**3), 3),
                "usage_percentage": round((db_stats["total_size_bytes"] / (1024**3)) / 20 * 100, 1),
            }

            return stats

        except Exception as e:
            self.logger.error(f"Error getting usage stats: {e}")
            return {"error": str(e)}
