from fastmcp import FastMCP
import logging
from ..config.settings import ServerConfig


class NanoBananaMCP:
    """Main FastMCP server class."""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize FastMCP server
        self.server = FastMCP(
            name=config.server_name,
            instructions=self._get_server_instructions(),
            mask_error_details=config.mask_error_details,
        )

        # Register components
        self._register_tools()
        self._register_resources()
        self._register_prompts()

    def _get_server_instructions(self) -> str:
        """Get server description and instructions."""
        return (
            "This server exposes image generation & editing powered by "
            "Gemini 2.5 Flash Image (aka 'nano banana'). It returns images "
            "as real MCP image content blocks, and also provides structured "
            "JSON with metadata and reproducibility hints."
        )

    def _register_tools(self):
        """Register all tools with the server."""
        from ..tools.generate_image import register_generate_image_tool
        from ..tools.upload_file import register_upload_file_tool
        from ..tools.output_stats import register_output_stats_tool
        from ..tools.maintenance import register_maintenance_tool

        register_generate_image_tool(self.server)
        register_upload_file_tool(self.server)
        register_output_stats_tool(self.server)
        register_maintenance_tool(self.server)

    def _register_resources(self):
        """Register all resources with the server."""
        from ..resources.file_metadata import register_file_metadata_resource
        from ..resources.template_catalog import register_template_catalog_resource
        from ..resources.operation_status import register_operation_status_resources

        register_file_metadata_resource(self.server)
        register_template_catalog_resource(self.server)
        register_operation_status_resources(self.server)

    def _register_prompts(self):
        """Register all prompts with the server."""
        from ..prompts.photography import register_photography_prompts
        from ..prompts.design import register_design_prompts
        from ..prompts.editing import register_editing_prompts

        register_photography_prompts(self.server)
        register_design_prompts(self.server)
        register_editing_prompts(self.server)

    def run(self):
        """Start the server."""
        if self.config.transport == "http":
            self.server.run(transport="http", host=self.config.host, port=self.config.port)
        else:
            self.server.run()
