from typing import Literal
from fastmcp import FastMCP
from ..config.constants import ASPECT_RATIOS
import logging


def register_photography_prompts(server: FastMCP):
    """Register photography-related prompts with the FastMCP server."""

    @server.prompt
    def photorealistic_shot(
        subject: str,
        composition: str,
        lighting: str,
        camera: str,
        aspect_hint: Literal[
            "Square image", "Portrait", "Landscape", "16:9", "4:3"
        ] = "Square image",
    ) -> str:
        """Generate a prompt for high-quality photorealistic images."""
        logger = logging.getLogger(__name__)

        try:
            # Validate aspect hint
            if aspect_hint not in ASPECT_RATIOS:
                logger.warning(f"Invalid aspect hint: {aspect_hint}, using default")
                aspect_hint = "Square image"

            prompt = (
                f"A photorealistic {subject}. Composition: {composition}. "
                f"Lighting: {lighting}. Camera: {camera}. {aspect_hint}."
            )

            logger.debug(f"Generated photorealistic_shot prompt: {prompt[:100]}...")
            return prompt

        except Exception as e:
            logger.error(f"Error generating photorealistic_shot prompt: {e}")
            # Return a basic fallback prompt
            return f"A photorealistic {subject}. {aspect_hint}."
