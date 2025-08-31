from typing import List, Optional, Tuple, Dict, Any
from fastmcp import Image as MCPImage
from services.gemini_client import GeminiClient
from utils.image_utils import validate_image_format, optimize_image_size
from config.settings import GeminiConfig
import logging

class ImageService:
    """Service for image generation and editing operations."""
    
    def __init__(self, gemini_client: GeminiClient, config: GeminiConfig):
        self.gemini_client = gemini_client
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def generate_images(
        self,
        prompt: str,
        n: int = 1,
        negative_prompt: Optional[str] = None,
        system_instruction: Optional[str] = None,
        input_images: Optional[List[Tuple[str, str]]] = None
    ) -> Tuple[List[MCPImage], List[Dict[str, Any]]]:
        """
        Generate images using Gemini API.
        
        Args:
            prompt: Main generation prompt
            n: Number of images to generate
            negative_prompt: Optional negative prompt
            system_instruction: Optional system instruction
            input_images: List of (base64, mime_type) tuples for input images
        
        Returns:
            Tuple of (image_blocks, metadata_list)
        """
        # Build content list
        contents = []
        if system_instruction:
            contents.append(system_instruction)
        
        # Add negative prompt constraints
        full_prompt = prompt
        if negative_prompt:
            full_prompt += f"\n\nConstraints (avoid): {negative_prompt}"
        contents.append(full_prompt)
        
        # Add input images if provided
        if input_images:
            images_b64, mime_types = zip(*input_images)
            image_parts = self.gemini_client.create_image_parts(
                list(images_b64), list(mime_types)
            )
            contents = image_parts + contents
        
        # Generate images
        all_images = []
        all_metadata = []
        
        for i in range(n):
            try:
                response = self.gemini_client.generate_content(contents)
                images = self.gemini_client.extract_images(response)
                
                for j, image_bytes in enumerate(images):
                    mcp_image = MCPImage(
                        data=image_bytes,
                        format=self.config.default_image_format
                    )
                    all_images.append(mcp_image)
                    
                    metadata = {
                        "response_index": i + 1,
                        "image_index": j + 1,
                        "mime_type": f"image/{self.config.default_image_format}",
                        "synthid_watermark": True,
                    }
                    all_metadata.append(metadata)
                    
            except Exception as e:
                self.logger.error(f"Failed to generate image {i+1}: {e}")
                # Continue with other images rather than failing completely
                continue
        
        return all_images, all_metadata
    
    def edit_image(
        self,
        instruction: str,
        base_image_b64: str,
        mime_type: str = "image/png"
    ) -> Tuple[List[MCPImage], int]:
        """
        Edit an image using conversational instructions.
        
        Args:
            instruction: Natural language editing instruction
            base_image_b64: Base64 encoded source image
            mime_type: MIME type of source image
        
        Returns:
            Tuple of (edited_images, count)
        """
        try:
            # Validate and prepare image
            validate_image_format(mime_type)
            
            # Create parts for Gemini API
            image_parts = self.gemini_client.create_image_parts([base_image_b64], [mime_type])
            contents = image_parts + [instruction]
            
            # Generate edited image
            response = self.gemini_client.generate_content(contents)
            image_bytes_list = self.gemini_client.extract_images(response)
            
            # Convert to MCP images
            mcp_images = []
            for image_bytes in image_bytes_list:
                mcp_image = MCPImage(
                    data=image_bytes,
                    format=self.config.default_image_format
                )
                mcp_images.append(mcp_image)
            
            return mcp_images, len(mcp_images)
            
        except Exception as e:
            self.logger.error(f"Failed to edit image: {e}")
            raise