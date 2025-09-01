"""
Maintenance Service - Implements the cleanup and hygiene workflows from workflows.md.

Handles:
- Files API expiration cleanup (~48h TTL)
- Local filesystem LRU/age-based cleanup
- Project storage budget management (~20GB Files API)
- Database hygiene and consistency checks
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path
from .files_api_service import FilesAPIService
from .image_database_service import ImageDatabaseService


class MaintenanceService:
    """Service for maintenance and cleanup operations following workflows.md patterns."""

    def __init__(
        self, files_api_service: FilesAPIService, db_service: ImageDatabaseService, out_dir: str
    ):
        """
        Initialize maintenance service.

        Args:
            files_api_service: Files API service
            db_service: Database service
            out_dir: Output directory path
        """
        self.files_api = files_api_service
        self.db_service = db_service
        self.out_dir = out_dir
        self.logger = logging.getLogger(__name__)

    def cleanup_expired_files(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up expired Files API entries from database.

        Implements: "Scan DB for Files API expirations (~48h TTL)"

        Args:
            dry_run: If True, only report what would be cleaned

        Returns:
            Dictionary with cleanup statistics
        """
        try:
            self.logger.info(f"Starting expired Files API cleanup (dry_run={dry_run})")

            # Delegate to FilesAPIService
            result = self.files_api.cleanup_expired_files(dry_run=dry_run)

            self.logger.info(f"Expired cleanup complete: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Expired files cleanup failed: {e}")
            return {"expired_count": 0, "cleared_count": 0, "errors": [str(e)]}

    def cleanup_local_files(
        self,
        dry_run: bool = True,
        max_age_hours: int = 168,  # 1 week
        keep_count: int = 10,
    ) -> Dict[str, Any]:
        """
        Clean up old local files based on age and LRU policy.

        Implements: "Local LRU/age-based cleanup of OUT_DIR"

        Args:
            dry_run: If True, only report what would be cleaned
            max_age_hours: Files older than this are candidates for removal
            keep_count: Always keep at least this many recent files

        Returns:
            Dictionary with cleanup statistics
        """
        try:
            self.logger.info(
                f"Starting local file cleanup (dry_run={dry_run}, "
                f"max_age_hours={max_age_hours}, keep_count={keep_count})"
            )

            stats = {
                "total_files": 0,
                "removed_count": 0,
                "kept_count": 0,
                "freed_mb": 0.0,
                "errors": [],
            }

            # Get all image files in output directory
            image_files = []
            for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
                image_files.extend(Path(self.out_dir).glob(f"**/{ext}"))

            # Sort by modification time (newest first)
            image_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            stats["total_files"] = len(image_files)

            # Cutoff time for old files
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cutoff_timestamp = cutoff_time.timestamp()

            removed_count = 0
            freed_bytes = 0

            for i, file_path in enumerate(image_files):
                try:
                    file_stat = file_path.stat()

                    # Always keep the most recent files
                    if i < keep_count:
                        continue

                    # Check if file is old enough to remove
                    if file_stat.st_mtime > cutoff_timestamp:
                        continue

                    # Check if file is still referenced in database
                    db_record = self.db_service.get_by_path(str(file_path))
                    if db_record and db_record.file_id:
                        # File is still referenced in Files API, keep it
                        self.logger.debug(f"Keeping referenced file: {file_path}")
                        continue

                    # File is eligible for removal
                    file_size = file_stat.st_size

                    if not dry_run:
                        file_path.unlink()

                        # Also remove corresponding thumbnail if it exists
                        thumb_path = file_path.with_name(file_path.stem + "_thumb.jpeg")
                        if thumb_path.exists():
                            thumb_size = thumb_path.stat().st_size
                            thumb_path.unlink()
                            file_size += thumb_size

                    removed_count += 1
                    freed_bytes += file_size

                    self.logger.debug(f"{'Would remove' if dry_run else 'Removed'}: {file_path}")

                except Exception as e:
                    error_msg = f"Error processing {file_path}: {e}"
                    stats["errors"].append(error_msg)
                    self.logger.error(error_msg)

            stats["removed_count"] = removed_count
            stats["kept_count"] = stats["total_files"] - removed_count
            stats["freed_mb"] = freed_bytes / (1024 * 1024)

            self.logger.info(f"Local cleanup complete: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Local files cleanup failed: {e}")
            return {
                "total_files": 0,
                "removed_count": 0,
                "kept_count": 0,
                "freed_mb": 0.0,
                "errors": [str(e)],
            }

    def check_storage_quota(self) -> Dict[str, Any]:
        """
        Check Files API storage usage vs. ~20GB budget.

        Implements: "Check project storage budget (Files API ~20GB)"

        Returns:
            Dictionary with quota information
        """
        try:
            self.logger.info("Checking Files API storage quota")

            # Get usage statistics from Files API service
            stats = self.files_api.get_usage_stats()

            self.logger.info(f"Storage quota check: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Storage quota check failed: {e}")
            return {
                "error": str(e),
                "total_images": 0,
                "total_size_bytes": 0,
                "estimated_usage_gb": 0.0,
                "files_api_quota_gb": 20,
                "usage_percentage": 0.0,
            }

    def database_hygiene(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up database inconsistencies and broken references.

        Args:
            dry_run: If True, only report what would be fixed

        Returns:
            Dictionary with hygiene statistics
        """
        try:
            self.logger.info(f"Starting database hygiene check (dry_run={dry_run})")

            stats = {
                "total_records": 0,
                "missing_files_removed": 0,
                "broken_references_fixed": 0,
                "consistent_records": 0,
                "warnings": [],
            }

            # Get database usage stats
            db_stats = self.db_service.get_usage_stats()
            stats["total_records"] = db_stats["total_images"]

            # Clean up records for missing files
            if not dry_run:
                missing_count = self.db_service.cleanup_missing_files()
                stats["missing_files_removed"] = missing_count
            else:
                # Simulate cleanup to get count
                # This would require a dry_run parameter in cleanup_missing_files
                stats["missing_files_removed"] = 0  # Would need to implement dry run

            # Check for other inconsistencies (could be expanded)
            stats["broken_references_fixed"] = 0
            stats["consistent_records"] = stats["total_records"] - stats["missing_files_removed"]

            self.logger.info(f"Database hygiene complete: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Database hygiene check failed: {e}")
            return {
                "total_records": 0,
                "missing_files_removed": 0,
                "broken_references_fixed": 0,
                "consistent_records": 0,
                "warnings": [str(e)],
            }

    def full_maintenance_cycle(
        self, dry_run: bool = True, max_age_hours: int = 168, keep_count: int = 10
    ) -> Dict[str, Any]:
        """
        Run complete maintenance cycle with all operations.

        Args:
            dry_run: If True, only report what would be done
            max_age_hours: For local cleanup
            keep_count: For local cleanup

        Returns:
            Dictionary with results from all operations
        """
        try:
            self.logger.info(f"Starting full maintenance cycle (dry_run={dry_run})")

            results = {}

            # 1. Clean up expired Files API entries
            results["expired_cleanup"] = self.cleanup_expired_files(dry_run=dry_run)

            # 2. Clean up old local files
            results["local_cleanup"] = self.cleanup_local_files(
                dry_run=dry_run, max_age_hours=max_age_hours, keep_count=keep_count
            )

            # 3. Check storage quota
            results["quota_check"] = self.check_storage_quota()

            # 4. Database hygiene
            results["database_hygiene"] = self.database_hygiene(dry_run=dry_run)

            self.logger.info(f"Full maintenance cycle complete")
            return results

        except Exception as e:
            self.logger.error(f"Full maintenance cycle failed: {e}")
            return {"error": str(e)}
