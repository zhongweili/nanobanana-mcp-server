from fastmcp import FastMCP
from typing import Dict, Any
from ..config.constants import TEMPLATE_CATEGORIES
import logging


def register_template_catalog_resource(server: FastMCP):
    """Register the template catalog resource with the FastMCP server."""

    @server.resource("nano-banana://prompt-templates")
    def prompt_templates_catalog() -> Dict[str, Any]:
        """
        A compact catalog of prompt templates (same schemas as the @mcp.prompt items).
        """
        logger = logging.getLogger(__name__)

        try:
            logger.debug("Generating prompt templates catalog")

            catalog = {
                "photorealistic_shot": {
                    "description": "High-fidelity photography template.",
                    "parameters": ["subject", "composition", "lighting", "camera", "aspect_hint"],
                    "category": "photography",
                    "use_cases": ["portraits", "landscapes", "product photography"],
                    "example_prompt": "A photorealistic mountain landscape. Composition: wide angle. Lighting: golden hour. Camera: DSLR with 24-70mm lens. Landscape.",
                },
                "logo_text": {
                    "description": "Accurate text rendering in a clean logo.",
                    "parameters": ["brand", "text", "font_style", "style_desc", "color_scheme"],
                    "category": "design",
                    "use_cases": ["branding", "marketing", "corporate identity"],
                    "example_prompt": "Create a modern, minimalist logo for TechCorp. The text should read 'TechCorp' in a sans-serif font. The design should be clean and professional. Color scheme: blue and white.",
                },
                "product_shot": {
                    "description": "Studio product mockup for e-commerce.",
                    "parameters": [
                        "product",
                        "background",
                        "lighting_setup",
                        "angle",
                        "aspect_hint",
                    ],
                    "category": "commercial",
                    "use_cases": ["e-commerce", "catalog", "advertising"],
                    "example_prompt": "A high-resolution, studio-lit product photograph of wireless headphones on white background. Lighting: soft box lighting. Camera angle: 45 degrees. Ultra-realistic. Square image.",
                },
                "sticker_flat": {
                    "description": "Kawaii/flat sticker with bold lines and white background.",
                    "parameters": ["character", "accessory", "palette"],
                    "category": "illustration",
                    "use_cases": ["messaging apps", "social media", "gaming"],
                    "example_prompt": "A kawaii-style sticker of a cute cat with a wizard hat. Bold, clean outlines, simple cel-shading, vibrant palette (purple, pink, yellow). Background must be white.",
                },
                "iterative_edit_instruction": {
                    "description": "Concise edit instruction phrasing for image modifications.",
                    "parameters": ["what_to_change", "how_it_should_blend"],
                    "category": "editing",
                    "use_cases": ["photo retouching", "creative editing", "corrections"],
                    "example_prompt": "Using the provided image, add a subtle vignette effect. Ensure the change blends naturally and matches the original style, lighting, and perspective.",
                },
                "composition_and_style_transfer": {
                    "description": "Blend multiple images and transfer artistic styles.",
                    "parameters": ["target_subject", "style_reference", "style_desc"],
                    "category": "artistic",
                    "use_cases": ["artistic rendering", "style exploration", "creative projects"],
                    "example_prompt": "Transform the provided photograph of the city skyline into the style of Van Gogh's Starry Night. Preserve composition; render with swirling brushstrokes and vibrant colors.",
                },
            }

            # Add category information
            for template_name, template_info in catalog.items():
                category = template_info.get("category", "general")
                if category in TEMPLATE_CATEGORIES:
                    template_info["category_description"] = TEMPLATE_CATEGORIES[category]

            # Add summary information
            summary = {
                "total_templates": len(catalog),
                "categories": list(TEMPLATE_CATEGORIES.keys()),
                "templates": catalog,
            }

            logger.debug(f"Generated catalog with {len(catalog)} templates")
            return summary

        except Exception as e:
            logger.error(f"Error generating template catalog: {e}")
            return {"error": "catalog_generation_error", "message": str(e), "templates": {}}
