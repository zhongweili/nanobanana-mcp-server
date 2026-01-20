"""Resources module for FastMCP server."""

from .file_metadata import register_file_metadata_resource
from .operation_status import register_operation_status_resources
from .template_catalog import register_template_catalog_resource

__all__ = [
    "register_file_metadata_resource",
    "register_operation_status_resources",
    "register_template_catalog_resource",
]
