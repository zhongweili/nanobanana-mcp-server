"""Template service for managing prompt templates."""

from typing import Dict, Any, List
import logging


class TemplateService:
    """Service for managing and providing prompt templates."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_template_catalog(self) -> Dict[str, Any]:
        """Get the complete template catalog."""
        return {
            "photorealistic_shot": {
                "description": "High-fidelity photography template.",
                "parameters": ["subject", "composition", "lighting", "camera", "aspect_hint"],
                "category": "photography",
                "use_cases": ["portraits", "landscapes", "product photography"],
            },
            "logo_text": {
                "description": "Accurate text rendering in a clean logo.",
                "parameters": ["brand", "text", "font_style", "style_desc", "color_scheme"],
                "category": "design",
                "use_cases": ["branding", "marketing", "corporate identity"],
            },
            "product_shot": {
                "description": "Studio product mockup for e-commerce.",
                "parameters": ["product", "background", "lighting_setup", "angle", "aspect_hint"],
                "category": "commercial",
                "use_cases": ["e-commerce", "catalog", "advertising"],
            },
            "sticker_flat": {
                "description": "Kawaii/flat sticker with bold lines and white background.",
                "parameters": ["character", "accessory", "palette"],
                "category": "illustration",
                "use_cases": ["messaging apps", "social media", "gaming"],
            },
            "iterative_edit_instruction": {
                "description": "Concise edit instruction phrasing for image modifications.",
                "parameters": ["what_to_change", "how_it_should_blend"],
                "category": "editing",
                "use_cases": ["photo retouching", "creative editing", "corrections"],
            },
            "composition_and_style_transfer": {
                "description": "Blend multiple images and transfer artistic styles.",
                "parameters": ["target_subject", "style_reference", "style_desc"],
                "category": "artistic",
                "use_cases": ["artistic rendering", "style exploration", "creative projects"],
            },
        }

    def get_template_by_name(self, name: str) -> Dict[str, Any]:
        """Get a specific template by name."""
        catalog = self.get_template_catalog()
        if name not in catalog:
            raise ValueError(f"Template '{name}' not found")
        return catalog[name]

    def get_templates_by_category(self, category: str) -> Dict[str, Any]:
        """Get all templates in a specific category."""
        catalog = self.get_template_catalog()
        return {
            name: template
            for name, template in catalog.items()
            if template.get("category") == category
        }

    def list_categories(self) -> List[str]:
        """Get all available template categories."""
        catalog = self.get_template_catalog()
        categories = set()
        for template in catalog.values():
            if "category" in template:
                categories.add(template["category"])
        return sorted(list(categories))
