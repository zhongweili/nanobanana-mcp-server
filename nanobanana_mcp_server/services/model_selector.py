"""Intelligent model selection service for routing requests to optimal models."""

import logging

from ..config.settings import ModelSelectionConfig, ModelTier
from .image_service import ImageService
from .pro_image_service import ProImageService


class ModelSelector:
    """
    Intelligent model selection and routing service.

    Routes image generation/editing requests to the appropriate model
    (Flash or Pro) based on prompt analysis, explicit user preference,
    or automatic selection logic.
    """

    def __init__(
        self,
        flash_service: ImageService,
        pro_service: ProImageService,
        selection_config: ModelSelectionConfig
    ):
        """
        Initialize model selector.

        Args:
            flash_service: Gemini 2.5 Flash Image service (speed-optimized)
            pro_service: Gemini 3 Pro Image service (quality-optimized)
            selection_config: Selection strategy configuration
        """
        self.flash_service = flash_service
        self.pro_service = pro_service
        self.config = selection_config
        self.logger = logging.getLogger(__name__)

    def select_model(
        self,
        prompt: str,
        requested_tier: ModelTier | None = None,
        **kwargs
    ) -> tuple[ImageService | ProImageService, ModelTier]:
        """
        Select appropriate model based on requirements.

        Args:
            prompt: User's image generation/edit prompt
            requested_tier: Explicit model tier request (or None for auto)
            **kwargs: Additional context (n, resolution, input_images, etc.)

        Returns:
            Tuple of (selected_service, selected_tier)
        """
        # Explicit selection takes precedence
        if requested_tier == ModelTier.FLASH:
            self.logger.info("Explicit Flash model selection")
            return self.flash_service, ModelTier.FLASH

        if requested_tier == ModelTier.PRO:
            self.logger.info("Explicit Pro model selection")
            return self.pro_service, ModelTier.PRO

        # Auto selection logic
        if requested_tier == ModelTier.AUTO or requested_tier is None:
            tier = self._auto_select(prompt, **kwargs)
            service = (
                self.pro_service if tier == ModelTier.PRO
                else self.flash_service
            )
            self.logger.info(
                f"Auto-selected {tier.value.upper()} model for prompt: '{prompt[:50]}...'"
            )
            return service, tier

        # Fallback to Flash for unknown values
        self.logger.warning(
            f"Unknown model tier '{requested_tier}', falling back to Flash"
        )
        return self.flash_service, ModelTier.FLASH

    def _auto_select(self, prompt: str, **kwargs) -> ModelTier:
        """
        Automatic model selection based on prompt and context analysis.

        Decision factors:
        1. Quality keywords in prompt (4k, professional, etc.)
        2. Speed keywords in prompt (quick, draft, etc.)
        3. Resolution requirements
        4. Multi-image conditioning
        5. Batch size

        Args:
            prompt: User's prompt text
            **kwargs: Additional context

        Returns:
            Selected ModelTier (FLASH or PRO)
        """
        quality_score = 0
        speed_score = 0

        prompt_lower = prompt.lower()

        # Analyze prompt for quality indicators
        quality_score = sum(
            1 for keyword in self.config.auto_quality_keywords
            if keyword in prompt_lower
        )

        # Analyze prompt for speed indicators
        speed_score = sum(
            1 for keyword in self.config.auto_speed_keywords
            if keyword in prompt_lower
        )

        # Strong quality indicators (weighted heavily)
        strong_quality_keywords = ["4k", "professional", "production", "high-res", "hd"]
        strong_quality_matches = sum(
            1 for keyword in strong_quality_keywords
            if keyword in prompt_lower
        )
        quality_score += strong_quality_matches * 2  # Double weight

        # Resolution parameter analysis
        resolution = kwargs.get("resolution", "").lower()
        
        # Parse resolution to determine requirements
        if resolution:
            # 4K explicitly requires Pro model
            if "4k" in resolution or "3840" in resolution or "4096" in resolution:
                self.logger.info("4K resolution requested - Pro model required")
                return ModelTier.PRO
            
            # 2K and high resolutions favor Pro
            elif "2k" in resolution or "2048" in resolution:
                quality_score += 2
                self.logger.debug("2K resolution requested, favoring Pro model")
            
            # High resolution favors quality
            elif resolution in ["high", "hd", "full"]:
                quality_score += 1
            
            # Check for specific dimensions
            elif "x" in resolution:
                try:
                    width, height = resolution.split("x")
                    max_dim = max(int(width), int(height))
                    
                    if max_dim >= 3840:
                        # 4K dimensions require Pro
                        self.logger.info(f"Resolution {resolution} requires Pro model (4K)")
                        return ModelTier.PRO
                    elif max_dim >= 2048:
                        # 2K dimensions favor Pro
                        quality_score += 2
                        self.logger.debug(f"Resolution {resolution} favors Pro model (2K)")
                    elif max_dim >= 1920:
                        # Full HD favors quality
                        quality_score += 1
                except:
                    pass  # Invalid format, ignore
        
# Batch size consideration
        n = kwargs.get("n", 1)
        if n > 2:
            # Multiple images favor speed
            speed_score += 1
            self.logger.debug(f"Multiple images requested (n={n}), favoring speed")

        # Multi-image conditioning
        input_images = kwargs.get("input_images")
        if input_images and len(input_images) > 1:
            # Pro model handles multi-image conditioning better
            quality_score += 1
            self.logger.debug(
                f"Multi-image conditioning ({len(input_images)} images), favoring quality"
            )

        # Thinking level hint
        thinking_level = kwargs.get("thinking_level", "").lower()
        if thinking_level == "high":
            quality_score += 1

        # Enable grounding hint
        enable_grounding = kwargs.get("enable_grounding", False)
        if enable_grounding:
            quality_score += 2  # Grounding is Pro-only feature
            self.logger.debug("Grounding requested - favoring Pro model")

        # Decision logic
        self.logger.debug(
            f"Model selection scores - Quality: {quality_score}, Speed: {speed_score}"
        )

        if quality_score > speed_score:
            self.logger.info(
                f"Selected PRO model (quality_score={quality_score} > speed_score={speed_score})"
            )
            return ModelTier.PRO
        else:
            self.logger.info(
                f"Selected FLASH model (speed_score={speed_score} >= quality_score={quality_score})"
            )
            return ModelTier.FLASH

    def get_model_info(self, tier: ModelTier) -> dict:
        """
        Get information about a specific model tier.

        Args:
            tier: Model tier to query

        Returns:
            Dictionary with model information
        """
        if tier == ModelTier.PRO:
            return {
                "tier": "pro",
                "name": "Gemini 3 Pro Image",
                "model_id": "gemini-3-pro-image-preview",
                "max_resolution": "4K (3840px)",
                "supported_resolutions": ["1k", "2k", "4k", "high", "3840x2160", "custom up to 4K"],
                "features": [
                    "4K resolution",
                    "Google Search grounding",
                    "Advanced reasoning",
                    "High-quality text rendering"
                ],
                "best_for": "Professional assets, production-ready images",
                "emoji": "🏆"
            }
        else:  # FLASH
            return {
                "tier": "flash",
                "name": "Gemini 2.5 Flash Image",
                "model_id": "gemini-2.5-flash-image",
                "max_resolution": "2048px (2K)",
                "supported_resolutions": ["1k", "2k", "1024x1024", "2048x2048", "custom up to 2K"],
                "features": [
                    "Very fast generation",
                    "Low latency",
                    "High-volume support"
                ],
                "best_for": "Rapid prototyping, quick iterations",
                "emoji": "⚡"
            }
