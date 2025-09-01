"""
Progress tracking system for long-running operations like image generation.
Provides real-time progress updates via structured logging and optional SSE support.
"""

import time
import uuid
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging


class OperationStatus(Enum):
    """Status of a tracked operation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProgressUpdate:
    """Single progress update."""

    operation_id: str
    timestamp: float
    status: OperationStatus
    progress_percent: int  # 0-100
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass
class TrackedOperation:
    """Information about a tracked operation."""

    operation_id: str
    operation_type: str
    created_at: float
    status: OperationStatus
    progress_percent: int
    current_message: str
    updates: List[ProgressUpdate]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["status"] = self.status.value
        data["updates"] = [update.to_dict() for update in self.updates]
        return data


class ProgressTracker:
    """Thread-safe progress tracking for long-running operations."""

    def __init__(self):
        self.operations: Dict[str, TrackedOperation] = {}
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

        # Optional callback for real-time updates (e.g., SSE)
        self.update_callback: Optional[Callable[[ProgressUpdate], None]] = None

    def set_update_callback(self, callback: Callable[[ProgressUpdate], None]) -> None:
        """Set callback function for real-time progress updates."""
        self.update_callback = callback

    def start_operation(
        self,
        operation_type: str,
        initial_message: str = "Starting...",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Start tracking a new operation.

        Args:
            operation_type: Type of operation (e.g., "image_generation")
            initial_message: Initial status message
            metadata: Additional operation metadata

        Returns:
            Unique operation ID
        """
        operation_id = str(uuid.uuid4())

        with self.lock:
            operation = TrackedOperation(
                operation_id=operation_id,
                operation_type=operation_type,
                created_at=time.time(),
                status=OperationStatus.PENDING,
                progress_percent=0,
                current_message=initial_message,
                updates=[],
                metadata=metadata or {},
            )

            self.operations[operation_id] = operation

            # Create initial update
            self._add_update(operation, OperationStatus.PENDING, 0, initial_message)

            self.logger.info(f"Started tracking operation {operation_id}: {operation_type}")
            return operation_id

    def update_progress(
        self,
        operation_id: str,
        progress_percent: int,
        message: str,
        status: Optional[OperationStatus] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update operation progress.

        Args:
            operation_id: Operation to update
            progress_percent: Progress percentage (0-100)
            message: Status message
            status: Optional status change
            details: Optional additional details

        Returns:
            True if update was successful, False if operation not found
        """
        with self.lock:
            operation = self.operations.get(operation_id)
            if not operation:
                self.logger.warning(f"Attempted to update unknown operation: {operation_id}")
                return False

            # Update operation
            operation.progress_percent = max(0, min(100, progress_percent))
            operation.current_message = message
            if status:
                operation.status = status

            # Add progress update
            effective_status = status or operation.status
            self._add_update(operation, effective_status, progress_percent, message, details)

            return True

    def complete_operation(
        self,
        operation_id: str,
        message: str = "Completed successfully",
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Mark operation as completed."""
        return self.update_progress(operation_id, 100, message, OperationStatus.COMPLETED, details)

    def fail_operation(
        self, operation_id: str, error_message: str, details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mark operation as failed."""
        return self.update_progress(
            operation_id, -1, error_message, OperationStatus.FAILED, details
        )

    def cancel_operation(self, operation_id: str, message: str = "Operation cancelled") -> bool:
        """Cancel an operation."""
        return self.update_progress(operation_id, -1, message, OperationStatus.CANCELLED)

    def get_operation(self, operation_id: str) -> Optional[TrackedOperation]:
        """Get operation details."""
        with self.lock:
            return self.operations.get(operation_id)

    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get current operation status as dict."""
        operation = self.get_operation(operation_id)
        if operation:
            return {
                "operation_id": operation.operation_id,
                "operation_type": operation.operation_type,
                "status": operation.status.value,
                "progress_percent": operation.progress_percent,
                "message": operation.current_message,
                "created_at": operation.created_at,
                "metadata": operation.metadata,
            }
        return None

    def list_operations(
        self, operation_type: Optional[str] = None, status: Optional[OperationStatus] = None
    ) -> List[Dict[str, Any]]:
        """List operations, optionally filtered by type and status."""
        with self.lock:
            operations = []
            for op in self.operations.values():
                if operation_type and op.operation_type != operation_type:
                    continue
                if status and op.status != status:
                    continue
                operations.append(op.to_dict())

            return sorted(operations, key=lambda x: x["created_at"], reverse=True)

    def cleanup_old_operations(self, max_age_seconds: int = 3600) -> int:
        """Remove old completed/failed operations."""
        cutoff_time = time.time() - max_age_seconds

        with self.lock:
            to_remove = []
            for op_id, operation in self.operations.items():
                if operation.created_at < cutoff_time and operation.status in [
                    OperationStatus.COMPLETED,
                    OperationStatus.FAILED,
                    OperationStatus.CANCELLED,
                ]:
                    to_remove.append(op_id)

            for op_id in to_remove:
                del self.operations[op_id]

            if to_remove:
                self.logger.info(f"Cleaned up {len(to_remove)} old operations")

            return len(to_remove)

    def _add_update(
        self,
        operation: TrackedOperation,
        status: OperationStatus,
        progress_percent: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a progress update to an operation (internal method)."""
        update = ProgressUpdate(
            operation_id=operation.operation_id,
            timestamp=time.time(),
            status=status,
            progress_percent=progress_percent,
            message=message,
            details=details,
        )

        operation.updates.append(update)

        # Log the progress update
        self.logger.info(f"Progress [{operation.operation_id}]: {progress_percent}% - {message}")

        # Call update callback if set (for real-time updates)
        if self.update_callback:
            try:
                self.update_callback(update)
            except Exception as e:
                self.logger.error(f"Error in progress update callback: {e}")


# Global progress tracker instance
_progress_tracker: Optional[ProgressTracker] = None


def get_progress_tracker() -> ProgressTracker:
    """Get the global progress tracker instance."""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker


class ProgressContext:
    """Context manager for tracking operation progress."""

    def __init__(
        self,
        operation_type: str,
        initial_message: str = "Starting...",
        metadata: Optional[Dict[str, Any]] = None,
        tracker: Optional[ProgressTracker] = None,
    ):
        self.operation_type = operation_type
        self.initial_message = initial_message
        self.metadata = metadata
        self.tracker = tracker or get_progress_tracker()
        self.operation_id: Optional[str] = None

    def __enter__(self) -> "ProgressContext":
        """Start progress tracking."""
        self.operation_id = self.tracker.start_operation(
            self.operation_type, self.initial_message, self.metadata
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete or fail progress tracking."""
        if not self.operation_id:
            return

        if exc_type is not None:
            # Operation failed
            error_msg = f"Failed: {str(exc_val)}" if exc_val else "Operation failed"
            self.tracker.fail_operation(self.operation_id, error_msg)
        else:
            # Operation completed successfully
            self.tracker.complete_operation(self.operation_id)

    def update(
        self, progress_percent: int, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update progress."""
        if self.operation_id:
            self.tracker.update_progress(
                self.operation_id, progress_percent, message, OperationStatus.RUNNING, details
            )
