"""
Resource handler for monitoring operation progress and status.
Provides real-time progress updates for long-running operations.
"""

from fastmcp import FastMCP
from typing import Dict, Any
import logging

from ..core.progress_tracker import get_progress_tracker, OperationStatus
from ..core.exceptions import ValidationError


def register_operation_status_resources(server: FastMCP):
    """Register operation status resources with the FastMCP server."""

    @server.resource("progress://operations/{operation_id}")
    def get_operation_progress(operation_id: str) -> Dict[str, Any]:
        """
        Get real-time progress information for a specific operation.

        Args:
            operation_id: Unique operation identifier

        Returns:
            Resource dict with current operation status and progress updates
        """
        logger = logging.getLogger(__name__)

        try:
            logger.debug(f"Getting progress for operation: {operation_id}")

            tracker = get_progress_tracker()
            operation = tracker.get_operation(operation_id)

            if not operation:
                return {
                    "error": "operation_not_found",
                    "message": f"Operation {operation_id} not found",
                    "operation_id": operation_id,
                }

            # Format progress updates for display
            formatted_updates = []
            for update in operation.updates[-10:]:  # Show last 10 updates
                from datetime import datetime

                timestamp_str = datetime.fromtimestamp(update.timestamp).strftime("%H:%M:%S")

                formatted_updates.append(
                    {
                        "timestamp": update.timestamp,
                        "time_str": timestamp_str,
                        "status": update.status.value,
                        "progress_percent": update.progress_percent,
                        "message": update.message,
                        "details": update.details,
                    }
                )

            return {
                "operation_id": operation.operation_id,
                "operation_type": operation.operation_type,
                "status": operation.status.value,
                "progress_percent": operation.progress_percent,
                "current_message": operation.current_message,
                "created_at": operation.created_at,
                "metadata": operation.metadata,
                "recent_updates": formatted_updates,
                "update_count": len(operation.updates),
                "is_active": operation.status in [OperationStatus.PENDING, OperationStatus.RUNNING],
            }

        except ValidationError as e:
            logger.error(f"Validation error getting progress for {operation_id}: {e}")
            return {"error": "validation_error", "message": str(e), "operation_id": operation_id}
        except Exception as e:
            logger.error(f"Error getting progress for {operation_id}: {e}")
            return {"error": "server_error", "message": str(e), "operation_id": operation_id}

    @server.resource("progress://operations/list")
    def list_operations() -> Dict[str, Any]:
        """
        List all tracked operations.

        Returns:
            Dict with list of operations and summary statistics
        """
        logger = logging.getLogger(__name__)

        try:
            tracker = get_progress_tracker()

            # Get all operations
            operations = tracker.list_operations()

            # Calculate summary statistics
            status_counts = {}
            type_counts = {}

            for op in operations:
                # Count by status
                status = op["status"]
                status_counts[status] = status_counts.get(status, 0) + 1

                # Count by type
                op_type = op["operation_type"]
                type_counts[op_type] = type_counts.get(op_type, 0) + 1

            # Format operations for display
            formatted_operations = []
            for op in operations[:20]:  # Limit to most recent 20
                from datetime import datetime

                created_str = datetime.fromtimestamp(op["created_at"]).strftime("%Y-%m-%d %H:%M:%S")

                formatted_operations.append(
                    {
                        **op,
                        "created_str": created_str,
                        "progress_uri": f"progress://operations/{op['operation_id']}",
                    }
                )

            return {
                "operations": formatted_operations,
                "total_count": len(operations),
                "shown_count": len(formatted_operations),
                "summary": {"status_counts": status_counts, "type_counts": type_counts},
                "filters": {"operation_type": None, "status": None},
            }

        except Exception as e:
            logger.error(f"Error listing operations: {e}")
            return {"error": "server_error", "message": str(e), "operations": []}
