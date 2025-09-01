from typing import Literal
from fastmcp import FastMCP
from ..config.constants import ASPECT_RATIOS
import logging


def register_design_prompts(server: FastMCP):
    """Register design-related prompts with the FastMCP server."""

    @server.prompt
    def logo_text(
        brand: str,
        text: str,
        font_style: str,
        style_desc: str,
        color_scheme: str,
    ) -> str:
        """Generate a prompt for logo creation with accurate text rendering."""
        logger = logging.getLogger(__name__)

        try:
            prompt = (
                f"Create a modern, minimalist logo for {brand}. The text should read '{text}' "
                f"in a {font_style} font. The design should be {style_desc}. Color scheme: {color_scheme}."
            )

            logger.debug(f"Generated logo_text prompt: {prompt[:100]}...")
            return prompt

        except Exception as e:
            logger.error(f"Error generating logo_text prompt: {e}")
            # Return a basic fallback prompt
            return (
                f"Create a logo for {brand} with the text '{text}'. Color scheme: {color_scheme}."
            )

    @server.prompt
    def product_shot(
        product: str,
        background: str,
        lighting_setup: str,
        angle: str,
        aspect_hint: Literal[
            "Square image", "Portrait", "Landscape", "16:9", "4:3"
        ] = "Square image",
    ) -> str:
        """Generate a prompt for studio product photography."""
        logger = logging.getLogger(__name__)

        try:
            # Validate aspect hint
            if aspect_hint not in ASPECT_RATIOS:
                logger.warning(f"Invalid aspect hint: {aspect_hint}, using default")
                aspect_hint = "Square image"

            prompt = (
                f"A high-resolution, studio-lit product photograph of {product} on {background}. "
                f"Lighting: {lighting_setup}. Camera angle: {angle}. Ultra-realistic. {aspect_hint}."
            )

            logger.debug(f"Generated product_shot prompt: {prompt[:100]}...")
            return prompt

        except Exception as e:
            logger.error(f"Error generating product_shot prompt: {e}")
            # Return a basic fallback prompt
            return f"A product photograph of {product} on {background}. {aspect_hint}."

    @server.prompt
    def sticker_flat(character: str, accessory: str, palette: str) -> str:
        """Generate a prompt for flat/kawaii style stickers."""
        logger = logging.getLogger(__name__)

        try:
            prompt = (
                f"A kawaii-style sticker of {character} with {accessory}. "
                f"Bold, clean outlines, simple cel-shading, vibrant palette ({palette}). "
                f"Background must be white."
            )

            logger.debug(f"Generated sticker_flat prompt: {prompt[:100]}...")
            return prompt

        except Exception as e:
            logger.error(f"Error generating sticker_flat prompt: {e}")
            # Return a basic fallback prompt
            return f"A kawaii sticker of {character} with {accessory}. White background."
