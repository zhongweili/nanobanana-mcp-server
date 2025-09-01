"""
Image Database Service for tracking generated images with Files API integration.

Implements the DB/Index layer shown in workflows.md for tracking:
- Local file paths and thumbnails
- Files API metadata (file_id, file_uri, expires_at)
- Parent/child relationships for edits
- Generation and editing metadata
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, NamedTuple
import logging


class ImageRecord(NamedTuple):
    """Represents a stored image record from the database."""

    id: int
    path: str
    thumb_path: str
    mime_type: str
    width: int
    height: int
    size_bytes: int
    file_id: Optional[str]
    file_uri: Optional[str]
    expires_at: Optional[datetime]
    parent_file_id: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ImageDatabaseService:
    """Database service for tracking image metadata and Files API integration."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database service.

        Args:
            db_path: Path to SQLite database file. Defaults to OUT_DIR/images.db
        """
        self.db_path = db_path or os.path.join("output", "images.db")
        self.logger = logging.getLogger(__name__)

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,
                    thumb_path TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    file_id TEXT,
                    file_uri TEXT,
                    expires_at TIMESTAMP,
                    parent_file_id TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for efficient lookups
            conn.execute("CREATE INDEX IF NOT EXISTS idx_file_id ON images(file_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_parent_file_id ON images(parent_file_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON images(expires_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_path ON images(path)")

            conn.commit()
            self.logger.info(f"Database initialized at {self.db_path}")

    def upsert_image(
        self,
        path: str,
        thumb_path: str,
        mime_type: str,
        width: int,
        height: int,
        size_bytes: int,
        file_id: Optional[str] = None,
        file_uri: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        parent_file_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Insert or update image record.

        Args:
            path: Local file path to full-resolution image
            thumb_path: Local file path to thumbnail
            mime_type: MIME type of the image
            width: Image width in pixels
            height: Image height in pixels
            size_bytes: File size in bytes
            file_id: Gemini Files API file ID (e.g., 'files/abc123')
            file_uri: Gemini Files API file URI
            expires_at: When the Files API entry expires (~48h from upload)
            parent_file_id: For edits, the file_id of the original image
            metadata: Additional metadata as JSON

        Returns:
            Database ID of the inserted/updated record
        """
        metadata_json = json.dumps(metadata or {})
        now = datetime.now()

        # Default expires_at to 48 hours from now if file_id is provided
        if file_id and expires_at is None:
            expires_at = now + timedelta(hours=48)

        with sqlite3.connect(self.db_path) as conn:
            # Check if record already exists by path
            existing = conn.execute("SELECT id FROM images WHERE path = ?", (path,)).fetchone()

            if existing:
                # Update existing record
                conn.execute(
                    """
                    UPDATE images 
                    SET thumb_path = ?, mime_type = ?, width = ?, height = ?, 
                        size_bytes = ?, file_id = ?, file_uri = ?, expires_at = ?,
                        parent_file_id = ?, metadata = ?, updated_at = ?
                    WHERE id = ?
                """,
                    (
                        thumb_path,
                        mime_type,
                        width,
                        height,
                        size_bytes,
                        file_id,
                        file_uri,
                        expires_at,
                        parent_file_id,
                        metadata_json,
                        now,
                        existing[0],
                    ),
                )
                record_id = existing[0]
                self.logger.debug(f"Updated image record {record_id} for {path}")
            else:
                # Insert new record
                cursor = conn.execute(
                    """
                    INSERT INTO images 
                    (path, thumb_path, mime_type, width, height, size_bytes,
                     file_id, file_uri, expires_at, parent_file_id, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        path,
                        thumb_path,
                        mime_type,
                        width,
                        height,
                        size_bytes,
                        file_id,
                        file_uri,
                        expires_at,
                        parent_file_id,
                        metadata_json,
                        now,
                        now,
                    ),
                )
                record_id = cursor.lastrowid
                self.logger.info(f"Inserted new image record {record_id} for {path}")

            conn.commit()
            return record_id

    def get_by_file_id(self, file_id: str) -> Optional[ImageRecord]:
        """Get image record by Files API file_id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM images WHERE file_id = ?", (file_id,)).fetchone()

            if row:
                return self._row_to_record(row)
            return None

    def get_by_path(self, path: str) -> Optional[ImageRecord]:
        """Get image record by local file path."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM images WHERE path = ?", (path,)).fetchone()

            if row:
                return self._row_to_record(row)
            return None

    def get_by_id(self, record_id: int) -> Optional[ImageRecord]:
        """Get image record by database ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM images WHERE id = ?", (record_id,)).fetchone()

            if row:
                return self._row_to_record(row)
            return None

    def list_expired_files(self, buffer_minutes: int = 30) -> List[ImageRecord]:
        """
        List Files API entries that are expired or will expire soon.

        Args:
            buffer_minutes: Consider files expiring within this many minutes

        Returns:
            List of image records with expired or soon-to-expire Files API entries
        """
        cutoff_time = datetime.now() + timedelta(minutes=buffer_minutes)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM images 
                WHERE file_id IS NOT NULL 
                  AND expires_at IS NOT NULL 
                  AND expires_at <= ?
                ORDER BY expires_at ASC
            """,
                (cutoff_time,),
            ).fetchall()

            return [self._row_to_record(row) for row in rows]

    def update_files_api_info(
        self, record_id: int, file_id: str, file_uri: str, expires_at: Optional[datetime] = None
    ) -> bool:
        """
        Update Files API information for an existing record.

        Args:
            record_id: Database record ID
            file_id: New Files API file ID
            file_uri: New Files API file URI
            expires_at: New expiration time (defaults to 48h from now)

        Returns:
            True if update was successful
        """
        if expires_at is None:
            expires_at = datetime.now() + timedelta(hours=48)

        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                """
                UPDATE images 
                SET file_id = ?, file_uri = ?, expires_at = ?, updated_at = ?
                WHERE id = ?
            """,
                (file_id, file_uri, expires_at, datetime.now(), record_id),
            )

            conn.commit()
            success = result.rowcount > 0

            if success:
                self.logger.debug(f"Updated Files API info for record {record_id}")
            else:
                self.logger.warning(f"No record found with ID {record_id}")

            return success

    def clear_files_api_info(self, record_id: int) -> bool:
        """
        Clear Files API information when file expires or is deleted.

        Args:
            record_id: Database record ID

        Returns:
            True if update was successful
        """
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                """
                UPDATE images 
                SET file_id = NULL, file_uri = NULL, expires_at = NULL, updated_at = ?
                WHERE id = ?
            """,
                (datetime.now(), record_id),
            )

            conn.commit()
            success = result.rowcount > 0

            if success:
                self.logger.debug(f"Cleared Files API info for record {record_id}")

            return success

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get database usage statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Total records and sizes
            stats_row = conn.execute("""
                SELECT 
                    COUNT(*) as total_images,
                    SUM(size_bytes) as total_size_bytes,
                    COUNT(CASE WHEN file_id IS NOT NULL THEN 1 END) as uploaded_to_files_api,
                    COUNT(CASE WHEN parent_file_id IS NOT NULL THEN 1 END) as edited_images
                FROM images
            """).fetchone()

            # Files API expiration status
            now = datetime.now()
            expiration_row = conn.execute(
                """
                SELECT 
                    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at <= ? THEN 1 END) as expired,
                    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at > ? THEN 1 END) as active
                FROM images
            """,
                (now, now),
            ).fetchone()

            return {
                "total_images": stats_row[0],
                "total_size_bytes": stats_row[1] or 0,
                "total_size_mb": round((stats_row[1] or 0) / (1024 * 1024), 2),
                "uploaded_to_files_api": stats_row[2],
                "edited_images": stats_row[3],
                "files_api_expired": expiration_row[0],
                "files_api_active": expiration_row[1],
            }

    def cleanup_missing_files(self) -> int:
        """
        Remove database records for files that no longer exist on disk.

        Returns:
            Number of records removed
        """
        removed_count = 0

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            all_records = conn.execute("SELECT * FROM images").fetchall()

            for row in all_records:
                record = self._row_to_record(row)

                # Check if both main file and thumbnail exist
                main_exists = os.path.exists(record.path)
                thumb_exists = os.path.exists(record.thumb_path)

                if not main_exists or not thumb_exists:
                    conn.execute("DELETE FROM images WHERE id = ?", (record.id,))
                    removed_count += 1
                    self.logger.info(
                        f"Removed record {record.id}: main={main_exists}, thumb={thumb_exists}"
                    )

            conn.commit()

        if removed_count > 0:
            self.logger.info(f"Cleaned up {removed_count} missing file records")

        return removed_count

    def _row_to_record(self, row: sqlite3.Row) -> ImageRecord:
        """Convert database row to ImageRecord."""
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}

        # Parse timestamps
        created_at = datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        updated_at = datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
        expires_at = datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None

        return ImageRecord(
            id=row["id"],
            path=row["path"],
            thumb_path=row["thumb_path"],
            mime_type=row["mime_type"],
            width=row["width"],
            height=row["height"],
            size_bytes=row["size_bytes"],
            file_id=row["file_id"],
            file_uri=row["file_uri"],
            expires_at=expires_at,
            parent_file_id=row["parent_file_id"],
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at,
        )
