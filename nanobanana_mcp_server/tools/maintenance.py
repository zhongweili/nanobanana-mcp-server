"""
Maintenance Tool - Implements cleanup and hygiene workflows from workflows.md.

Provides tools for:
- Files API expiration cleanup (~48h TTL)
- Local filesystem LRU/age-based cleanup
- Project storage budget management
- Database hygiene and consistency checks
"""

from typing import Annotated, Optional
from pydantic import Field
from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from ..core.exceptions import ValidationError
import logging


def register_maintenance_tool(server: FastMCP):
    """Register the maintenance tool with the FastMCP server."""

    @server.tool(
        annotations={
            "title": "Maintenance and cleanup operations",
            "readOnlyHint": True,
            "openWorldHint": True,
        }
    )
    def maintenance(
        operation: Annotated[
            str,
            Field(
                description="Maintenance operation to perform: "
                "'cleanup_expired', 'cleanup_local', 'check_quota', 'database_hygiene', 'full_cleanup'"
            ),
        ],
        dry_run: Annotated[
            bool,
            Field(description="If true, only report what would be done without making changes"),
        ] = True,
        max_age_hours: Annotated[
            Optional[int],
            Field(
                description="For local cleanup: maximum age in hours (default: 168 = 1 week)",
                ge=1,
                le=8760,
            ),
        ] = None,
        keep_count: Annotated[
            Optional[int],
            Field(
                description="For local cleanup: minimum number of recent files to keep",
                ge=1,
                le=1000,
            ),
        ] = None,
        ctx: Context = None,
    ) -> ToolResult:
        """
        Perform maintenance operations following workflows.md patterns.

        Available operations:
        - cleanup_expired: Remove expired Files API entries from database
        - cleanup_local: Clean old local files based on age/LRU
        - check_quota: Check Files API storage usage vs. ~20GB budget
        - database_hygiene: Clean up database inconsistencies
        - full_cleanup: Run all cleanup operations in sequence
        """
        logger = logging.getLogger(__name__)

        try:
            logger.info(f"Maintenance operation: {operation}, dry_run={dry_run}")

            # Get services (would be injected in real implementation)
            maintenance_service = _get_maintenance_service()

            # Validate operation
            valid_operations = [
                "cleanup_expired",
                "cleanup_local",
                "check_quota",
                "database_hygiene",
                "full_cleanup",
            ]

            if operation not in valid_operations:
                raise ValidationError(
                    f"Invalid operation. Must be one of: {', '.join(valid_operations)}"
                )

            # Execute maintenance operation
            if operation == "cleanup_expired":
                result = maintenance_service.cleanup_expired_files(dry_run=dry_run)
                summary = _format_expired_cleanup_summary(result, dry_run)

            elif operation == "cleanup_local":
                result = maintenance_service.cleanup_local_files(
                    dry_run=dry_run,
                    max_age_hours=max_age_hours or 168,  # 1 week default
                    keep_count=keep_count or 10,  # Keep at least 10 recent files
                )
                summary = _format_local_cleanup_summary(result, dry_run)

            elif operation == "check_quota":
                result = maintenance_service.check_storage_quota()
                summary = _format_quota_summary(result)

            elif operation == "database_hygiene":
                result = maintenance_service.database_hygiene(dry_run=dry_run)
                summary = _format_database_hygiene_summary(result, dry_run)

            elif operation == "full_cleanup":
                result = maintenance_service.full_maintenance_cycle(
                    dry_run=dry_run, max_age_hours=max_age_hours or 168, keep_count=keep_count or 10
                )
                summary = _format_full_cleanup_summary(result, dry_run)

            else:
                # This shouldn't happen due to validation above
                raise ValidationError(f"Unhandled operation: {operation}")

            content = [TextContent(type="text", text=summary)]

            structured_content = {
                "operation": operation,
                "dry_run": dry_run,
                "workflow": "workflows.md_maintenance_sequence",
                "result": result,
                "parameters": {"max_age_hours": max_age_hours, "keep_count": keep_count},
            }

            logger.info(f"Maintenance operation {operation} completed successfully")

            return ToolResult(content=content, structured_content=structured_content)

        except ValidationError as e:
            logger.error(f"Validation error in maintenance: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in maintenance: {e}")
            raise


def _format_expired_cleanup_summary(result: dict, dry_run: bool) -> str:
    """Format summary for expired Files API cleanup."""
    action_verb = "Would clear" if dry_run else "Cleared"
    mode_text = "[DRY RUN] " if dry_run else ""

    summary_lines = [
        f"{mode_text}🧹 **Files API Expired Entries Cleanup**",
        f"📊 Found {result['expired_count']} expired entries",
        f"✅ {action_verb} {result['cleared_count']} entries",
    ]

    if result.get("errors"):
        summary_lines.append(f"❌ Errors: {len(result['errors'])}")
        for error in result["errors"][:3]:  # Show first 3 errors
            summary_lines.append(f"   • {error}")
        if len(result["errors"]) > 3:
            summary_lines.append(f"   • ... and {len(result['errors']) - 3} more")

    return "\\n".join(summary_lines)


def _format_local_cleanup_summary(result: dict, dry_run: bool) -> str:
    """Format summary for local file cleanup."""
    action_verb = "Would remove" if dry_run else "Removed"
    mode_text = "[DRY RUN] " if dry_run else ""

    summary_lines = [
        f"{mode_text}🧹 **Local File Cleanup (LRU/Age-based)**",
        f"📊 Scanned {result['total_files']} files",
        f"📁 {action_verb} {result['removed_count']} old files",
        f"💾 Freed {result['freed_mb']:.1f} MB of disk space",
        f"📋 Kept {result['kept_count']} recent/referenced files",
    ]

    if result.get("errors"):
        summary_lines.append(f"❌ Errors: {len(result['errors'])}")

    return "\\n".join(summary_lines)


def _format_quota_summary(result: dict) -> str:
    """Format summary for storage quota check."""
    usage_percent = result["usage_percentage"]
    status_emoji = "🟢" if usage_percent < 75 else "🟡" if usage_percent < 90 else "🔴"

    summary_lines = [
        "📊 **Files API Storage Quota Check**",
        f"{status_emoji} Usage: {result['estimated_usage_gb']:.2f} GB / {result['files_api_quota_gb']} GB ({usage_percent:.1f}%)",
        f"📁 Total images: {result['total_images']}",
        f"☁️ Uploaded to Files API: {result['uploaded_to_files_api']}",
        f"✅ Active Files API entries: {result['files_api_active']}",
        f"⏰ Expired Files API entries: {result['files_api_expired']}",
    ]

    if usage_percent > 90:
        summary_lines.append(
            "⚠️ **WARNING**: Storage usage is high. Consider running cleanup operations."
        )
    elif usage_percent > 75:
        summary_lines.append(
            "ℹ️ **INFO**: Storage usage is moderate. Monitor for future cleanup needs."
        )

    return "\\n".join(summary_lines)


def _format_database_hygiene_summary(result: dict, dry_run: bool) -> str:
    """Format summary for database hygiene check."""
    action_verb = "Would fix" if dry_run else "Fixed"
    mode_text = "[DRY RUN] " if dry_run else ""

    summary_lines = [
        f"{mode_text}🧹 **Database Hygiene Check**",
        f"📊 Total records: {result['total_records']}",
        f"🗑️ {action_verb} {result['missing_files_removed']} records with missing files",
        f"🔗 {action_verb} {result['broken_references_fixed']} broken file references",
        f"✅ Consistent records: {result['consistent_records']}",
    ]

    if result.get("warnings"):
        summary_lines.append(f"⚠️ Warnings: {len(result['warnings'])}")

    return "\\n".join(summary_lines)


def _format_full_cleanup_summary(result: dict, dry_run: bool) -> str:
    """Format summary for full cleanup cycle."""
    mode_text = "[DRY RUN] " if dry_run else ""

    summary_lines = [
        f"{mode_text}🧹 **Full Maintenance Cycle**",
        "",
        "📋 **Operations Performed:**",
    ]

    # Add summaries for each operation
    for operation, op_result in result.items():
        if operation == "expired_cleanup":
            summary_lines.append(
                f"   • Files API Cleanup: {op_result['cleared_count']} expired entries"
            )
        elif operation == "local_cleanup":
            summary_lines.append(
                f"   • Local File Cleanup: {op_result['removed_count']} files, {op_result['freed_mb']:.1f} MB"
            )
        elif operation == "quota_check":
            summary_lines.append(f"   • Quota Check: {op_result['usage_percentage']:.1f}% used")
        elif operation == "database_hygiene":
            summary_lines.append(
                f"   • Database Hygiene: {op_result['missing_files_removed']} records cleaned"
            )

    summary_lines.append("")
    summary_lines.append("✅ Full maintenance cycle completed")

    return "\\n".join(summary_lines)


def _get_maintenance_service():
    """Get the maintenance service instance."""
    from ..services import get_maintenance_service
    return get_maintenance_service()
