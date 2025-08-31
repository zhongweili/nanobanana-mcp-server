"""Resources module for FastMCP server."""

from .file_metadata import register_file_metadata_resource
from .template_catalog import register_template_catalog_resource
from .operation_status import register_operation_status_resources

__all__ = [
    "register_file_metadata_resource",
    "register_template_catalog_resource",
    "register_operation_status_resources",
]
