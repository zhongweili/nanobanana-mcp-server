from fastmcp import FastMCP
import logging


def register_editing_prompts(server: FastMCP):
    """Register editing-related prompts with the FastMCP server."""

    @server.prompt
    def iterative_edit_instruction(what_to_change: str, how_it_should_blend: str) -> str:
        """Generate an instruction for precise image editing."""
        logger = logging.getLogger(__name__)

        try:
            prompt = (
                f"Using the provided image, {what_to_change}. "
                f"Ensure the change {how_it_should_blend} and matches the original style, lighting, and perspective."
            )

            logger.debug("Generated iterative_edit_instruction (%d chars)", len(prompt))
            return prompt

        except Exception as e:
            logger.error(f"Error generating iterative_edit_instruction: {e}")
            # Return a basic fallback prompt
            return f"Using the provided image, {what_to_change}."

    @server.prompt
    def composition_and_style_transfer(
        target_subject: str, style_reference: str, style_desc: str
    ) -> str:
        """Generate an instruction for style transfer and composition blending."""
        logger = logging.getLogger(__name__)

        try:
            prompt = (
                f"Transform the provided photograph of {target_subject} into the style of {style_reference}. "
                f"Preserve composition; render with {style_desc}."
            )

            logger.debug("Generated composition_and_style_transfer (%d chars)", len(prompt))
            return prompt

        except Exception as e:
            logger.error(f"Error generating composition_and_style_transfer: {e}")
            # Return a basic fallback prompt
            return f"Transform the provided photograph of {target_subject} into the style of {style_reference}."
