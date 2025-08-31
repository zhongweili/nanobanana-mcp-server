from google import genai
from google.genai import types as gx
from typing import List, Optional
import base64
from io import BytesIO
import logging
from config.settings import GeminiConfig, ServerConfig

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
        parts = []
        for b64, mime_type in zip(images_b64, mime_types):
            try:
                raw_data = base64.b64decode(b64)
                part = gx.Part.from_bytes(data=raw_data, mime_type=mime_type)
                parts.append(part)
            except Exception as e:
                self.logger.error(f"Failed to process image: {e}")
                raise ValueError(f"Invalid image data: {e}")
        return parts
    
    def generate_content(self, contents: List, **kwargs) -> any:
        """Generate content using Gemini API with error handling."""
        try:
            response = self.client.models.generate_content(
                model=self.gemini_config.model_name,
                contents=contents,
                **kwargs
            )
            return response
        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            raise
    
    def extract_images(self, response) -> List[bytes]:
        """Extract image bytes from Gemini response."""
        images = []
        candidates = getattr(response, "candidates", None)
        if not candidates:
            return images
        
        for part in candidates[0].content.parts:
            inline_data = getattr(part, "inline_data", None)
            if inline_data and hasattr(inline_data, "data"):
                images.append(inline_data.data)
        
        return images
    
    def upload_file(self, file_path: str, display_name: Optional[str] = None):
        """Upload file to Gemini Files API."""
        try:
            if display_name:
                return self.client.files.upload(file=file_path, display_name=display_name)
            else:
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