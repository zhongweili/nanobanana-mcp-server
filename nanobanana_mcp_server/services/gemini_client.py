import base64
import logging
from typing import Any

from google import genai
from google.genai import types as gx

from ..config.settings import (
    AuthMethod,
    BaseModelConfig,
    FlashImageConfig,
    GeminiConfig,
    ProImageConfig,
    ServerConfig,
)
from ..core.exceptions import AuthenticationError


class GeminiClient:
    """Wrapper for Google Gemini API client with multi-model support."""

    def __init__(
        self,
        config: ServerConfig,
        gemini_config: GeminiConfig | BaseModelConfig | FlashImageConfig | ProImageConfig
    ):
        self.config = config
        self.gemini_config = gemini_config
        self.logger = logging.getLogger(__name__)
        self._client = None

    @property
    def client(self) -> genai.Client:
        """Lazy initialization of Gemini client."""
        if self._client is None:
            if self.config.auth_method == AuthMethod.API_KEY:
                if not self.config.gemini_api_key:
                    raise AuthenticationError("API key is required for API_KEY auth method")
                self._client = genai.Client(api_key=self.config.gemini_api_key)
                self._log_auth_method("API Key (Developer API)")
            else:  # VERTEX_AI
                self._client = genai.Client(
                    vertexai=True,
                    project=self.config.gcp_project_id,
                    location=self.config.gcp_region
                )
                self._log_auth_method(f"ADC (Vertex AI - {self.config.gcp_region})")
        return self._client

    def _log_auth_method(self, method: str):
        """Log the authentication method in use."""
        self.logger.info(f"Authentication method: {method}")

    def validate_auth(self) -> bool:
        """Validate authentication credentials (optional).

        Note: This makes an API call, so use sparingly.
        """
        try:
            # Lightweight API call
            _ = self.client.models.list()
            return True
        except Exception as e:
            self.logger.error(f"Authentication validation failed: {e}")
            return False

    def create_image_parts(self, images_b64: list[str], mime_types: list[str]) -> list[gx.Part]:
        """Convert base64 images to Gemini Part objects."""
        if not images_b64 or not mime_types:
            return []

        if len(images_b64) != len(mime_types):
            raise ValueError(f"Images and MIME types count mismatch: {len(images_b64)} vs {len(mime_types)}")

        parts = []
        for i, (b64, mime_type) in enumerate(zip(images_b64, mime_types, strict=False)):
            if not b64 or not mime_type:
                self.logger.warning(f"Skipping empty image or MIME type at index {i}")
                continue

            try:
                raw_data = base64.b64decode(b64)
                if len(raw_data) == 0:
                    self.logger.warning(f"Skipping empty image data at index {i}")
                    continue

                part = gx.Part.from_bytes(data=raw_data, mime_type=mime_type)
                parts.append(part)
            except Exception as e:
                self.logger.error(f"Failed to process image at index {i}: {e}")
                raise ValueError(f"Invalid image data at index {i}: {e}") from e
        return parts

    def generate_content(
        self,
        contents: list,
        config: dict[str, Any] | None = None,
        aspect_ratio: str | None = None,
        **kwargs
    ) -> any:
        """
        Generate content using Gemini API with model-aware parameter handling.

        Args:
            contents: Content list (text, images, etc.)
            config: Generation configuration dict (model-specific parameters)
            aspect_ratio: Optional aspect ratio string (e.g., "16:9")
            **kwargs: Additional parameters

        Returns:
            API response object
        """
        try:
            # Remove unsupported request_options parameter
            kwargs.pop("request_options", None)

            # Check for config conflict
            config_obj = kwargs.pop("config", None)
            if config_obj is not None:
                if aspect_ratio or config:
                    self.logger.warning(
                        "Custom 'config' kwarg provided; ignoring aspect_ratio and config parameters"
                    )
                kwargs["config"] = config_obj
            else:
                # Filter parameters based on model capabilities
                filtered_config = self._filter_parameters(config or {})

                # Build generation config
                config_kwargs = {
                    "response_modalities": ["Image"],  # Force image-only responses
                }

                # Add aspect ratio if provided
                if aspect_ratio:
                    config_kwargs["image_config"] = gx.ImageConfig(aspect_ratio=aspect_ratio)

                # Merge filtered config parameters
                config_kwargs.update(filtered_config)

                kwargs["config"] = gx.GenerateContentConfig(**config_kwargs)

            # Prepare kwargs
            api_kwargs = {
                "model": self.gemini_config.model_name,
                "contents": contents,
            }

            # Merge additional kwargs
            api_kwargs.update(kwargs)

            self.logger.debug(
                f"Calling Gemini API: model={self.gemini_config.model_name}, "
                f"config={api_kwargs.get('config')}"
            )

            response = self.client.models.generate_content(**api_kwargs)
            return response

        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            raise

    def _filter_parameters(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Filter configuration parameters based on model capabilities.

        Ensures we only send parameters that the current model supports,
        preventing API errors from unsupported parameters.

        Args:
            config: Raw configuration dictionary

        Returns:
            Filtered configuration with only supported parameters
        """
        if not config:
            return {}

        filtered = {}

        # Common parameters (supported by all models)
        for param in ["temperature", "top_p", "top_k", "max_output_tokens"]:
            if param in config:
                filtered[param] = config[param]

        # Pro-specific parameters
        if isinstance(self.gemini_config, ProImageConfig):
            # Thinking level (Pro only)
            if "thinking_level" in config:
                filtered["thinking_level"] = config["thinking_level"]

            # Media resolution (Pro only)
            if "media_resolution" in config:
                filtered["media_resolution"] = config["media_resolution"]

            # Output resolution hints (may not be directly supported by API)
            if "output_resolution" in config:
                # This might need to be encoded in the prompt instead
                self.logger.debug(
                    f"Output resolution requested: {config['output_resolution']}"
                )

            # Note: enable_grounding may be controlled via system instructions
            # rather than as a direct API parameter in some SDK versions

        else:
            # Flash model - warn if Pro parameters are used
            pro_params = ["thinking_level", "media_resolution", "output_resolution"]
            used_pro_params = [p for p in pro_params if p in config]
            if used_pro_params:
                self.logger.warning(
                    f"Pro-only parameters ignored for Flash model: {used_pro_params}"
                )

        return filtered

    def extract_images(self, response) -> list[bytes]:
        """Extract image bytes from Gemini response."""
        images = []
        candidates = getattr(response, "candidates", None)
        if not candidates or len(candidates) == 0:
            return images

        first_candidate = candidates[0]
        if not hasattr(first_candidate, "content") or not first_candidate.content:
            return images

        content_parts = getattr(first_candidate.content, "parts", [])
        for part in content_parts:
            inline_data = getattr(part, "inline_data", None)
            if inline_data and hasattr(inline_data, "data") and inline_data.data:
                images.append(inline_data.data)

        return images

    def upload_file(self, file_path: str, _display_name: str | None = None):
        """Upload file to Gemini Files API.

        Note: display_name is kept for API compatibility but ignored as the
        Gemini Files API does not support display_name parameter in upload.
        """
        try:
            # Gemini Files API only accepts file parameter
            return self.client.files.upload(file=file_path)
        except Exception as e:
            self.logger.error(f"File upload error: {e}")
            raise

    def get_file_metadata(self, file_name: str):
        """Get file metadata from Gemini Files API."""
        try:
            return self.client.files.get(name=file_name)
        except Exception as e:
            self.logger.error(f"File metadata error: {e}")
            raise
