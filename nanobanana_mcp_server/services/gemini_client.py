from google import genai
from google.genai import types as gx
from typing import List, Optional
import base64
import logging
from ..config.settings import GeminiConfig, ServerConfig


class GeminiClient:
    """Wrapper for Google Gemini API client with error handling."""

    def __init__(self, config: ServerConfig, gemini_config: GeminiConfig):
        self.config = config
        self.gemini_config = gemini_config
        self.logger = logging.getLogger(__name__)
        self._client = None

    @property
    def client(self) -> genai.Client:
        """Lazy initialization of Gemini client."""
        if self._client is None:
            self._client = genai.Client(api_key=self.config.gemini_api_key)
        return self._client

    def create_image_parts(self, images_b64: List[str], mime_types: List[str]) -> List[gx.Part]:
        """Convert base64 images to Gemini Part objects."""
        if not images_b64 or not mime_types:
            return []
        
        if len(images_b64) != len(mime_types):
            raise ValueError(f"Images and MIME types count mismatch: {len(images_b64)} vs {len(mime_types)}")
        
        parts = []
        for i, (b64, mime_type) in enumerate(zip(images_b64, mime_types)):
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
                raise ValueError(f"Invalid image data at index {i}: {e}")
        return parts

    def generate_content(self, contents: List, **kwargs) -> any:
        """Generate content using Gemini API with error handling."""
        try:
            # Remove unsupported request_options parameter
            kwargs.pop("request_options", None)

            response = self.client.models.generate_content(
                model=self.gemini_config.model_name, contents=contents, **kwargs
            )
            return response
        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            raise

    def extract_images(self, response) -> List[bytes]:
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

    def upload_file(self, file_path: str, display_name: Optional[str] = None):
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
