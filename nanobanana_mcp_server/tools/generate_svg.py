import logging
import os
import re
from typing import Annotated

from fastmcp import Context, FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from pydantic import Field

from ..utils.validation_utils import validate_output_path

def register_generate_svg_tool(server: FastMCP):
    """Register the generate_svg tool with the FastMCP server."""

    @server.tool(
        annotations={
            "title": "Generate SVG vector icons and graphics",
            "readOnlyHint": True,
            "openWorldHint": True,
        }
    )
    def generate_svg(
        prompt: Annotated[
            str,
            Field(
                description="Describe the SVG icon or graphic you want to generate. "
                "Specify style, colors, stroke weight (e.g., 2px), and any branding constraints.",
                min_length=1,
                max_length=4096,
            ),
        ],
        output_path: Annotated[
            str | None,
            Field(
                description="Output path for the generated SVG file. "
                "If None, uses IMAGE_OUTPUT_DIR environment variable."
            ),
        ] = None,
        style_context: Annotated[
            str | None,
            Field(description="Optional additional style context or brand rules."),
        ] = None,
        _ctx: Context | None = None,
    ) -> ToolResult:
        """
        Generate SVG vector code based on a natural language description.
        
        This tool uses a text-to-code approach to produce clean, usable SVG files
        suitable for icons, logos, and UI elements.
        """
        logger = logging.getLogger(__name__)

        try:
            logger.info(f"Generate SVG request: prompt='{prompt[:50]}...', output_path={output_path}")

            # Validate output_path if provided
            if output_path:
                validate_output_path(output_path)

            from ..services import get_gemini_client
            client_wrapper = get_gemini_client()

            # Prepare the system instruction for SVG generation
            system_instruction = (
                "You are an expert SVG designer and frontend engineer. "
                "Generate ONLY clean, valid, production-ready SVG code. "
                "Do not include any explanations, markdown code blocks, or preamble. "
                "Output ONLY the SVG tag and its contents. "
                "Ensure the SVG is responsive (use viewBox, not fixed width/height where appropriate). "
                "Use modern design principles: minimalist, consistent stroke weights, and clean paths. "
                "For PetPals, use soft rounded corners and $radius.4 style if applicable in path data."
            )
            
            if style_context:
                system_instruction += f"\n\nStyle Context: {style_context}"

            # Call Gemini via the client wrapper's client property
            # We use gemini-2.0-flash for high-quality code generation
            response = client_wrapper.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt],
                config={
                    "system_instruction": system_instruction,
                    "response_mime_type": "text/plain",
                }
            )

            svg_code = response.text.strip()
            
            # Clean up potential markdown wrapper
            if svg_code.startswith("```"):
                # Use regex to strip any markdown block wrappers including the language tag
                svg_code = re.sub(r"^```[a-z]*\n", "", svg_code)
                svg_code = re.sub(r"\n```$", "", svg_code)
                svg_code = svg_code.strip()

            # Ensure it actually starts with <svg
            if not svg_code.startswith("<svg"):
                # If it's just path data or something, wrap it? 
                # Better to just return what we got if we can't be sure
                pass

            # Finalize output path
            final_output_path = output_path
            if not final_output_path:
                from ..services import get_server_config
                output_dir = get_server_config().image_output_dir
                
                # Create a filename from the prompt
                slug = re.sub(r'[^a-z0-9]+', '_', prompt[:30].lower()).strip('_')
                if not slug:
                    slug = "generated_icon"
                
                filename = f"petpals_{slug}.svg"
                final_output_path = os.path.join(output_dir, filename)

            # Ensure directory exists
            os.makedirs(os.path.dirname(final_output_path), exist_ok=True)

            # Save to file
            with open(final_output_path, "w", encoding="utf-8") as f:
                f.write(svg_code)

            summary = (
                f"✅ Successfully generated SVG graphic.\n"
                f"📁 **Saved to**: `{final_output_path}`\n\n"
                f"```svg\n{svg_code[:1000]}{'...' if len(svg_code) > 1000 else ''}\n```"
            )

            content = [TextContent(type="text", text=summary)]
            structured_content = {
                "success": True,
                "output_path": final_output_path,
                "svg_code": svg_code,
                "prompt": prompt,
                "model": "gemini-2.0-flash"
            }

            return ToolResult(content=content, structured_content=structured_content)

        except Exception as e:
            logger.error(f"Error in generate_svg: {e}")
            raise
