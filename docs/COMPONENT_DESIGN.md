# Nano Banana MCP Server - Component Design

## Overview

This document defines the detailed component architecture for the Nano Banana MCP Server, providing a modular, maintainable, and extensible codebase structure.

## Directory Structure

```
nanobanana-mcp-server/
├── server.py                 # Main server entry point
├── pyproject.toml            # uv dependencies and project config
├── ruff.toml                 # Ruff linting and formatting config
├── .env.example             # Environment template
├── config/
│   ├── __init__.py
│   ├── settings.py          # Configuration management
│   └── constants.py         # Application constants
├── core/
│   ├── __init__.py
│   ├── server.py            # FastMCP server setup
│   ├── exceptions.py        # Custom exceptions
│   └── validation.py        # Input validation utilities
├── services/
│   ├── __init__.py
│   ├── gemini_client.py     # Gemini API client wrapper
│   ├── image_service.py     # Image processing service
│   ├── file_service.py      # File management service
│   └── template_service.py  # Prompt template service
├── tools/
│   ├── __init__.py
│   ├── generate_image.py    # Image generation tool
│   ├── edit_image.py        # Image editing tool
│   └── upload_file.py       # File upload tool
├── resources/
│   ├── __init__.py
│   ├── file_metadata.py     # File metadata resource
│   └── template_catalog.py  # Template catalog resource
├── prompts/
│   ├── __init__.py
│   ├── photography.py       # Photography-related prompts
│   ├── design.py           # Design-related prompts
│   └── editing.py          # Editing-related prompts
├── utils/
│   ├── __init__.py
│   ├── image_utils.py       # Image processing utilities
│   ├── validation_utils.py  # Validation helpers
│   └── logging_utils.py     # Logging configuration
├── tests/
│   ├── __init__.py
│   ├── test_tools.py
│   ├── test_services.py
│   └── test_utils.py
└── docs/
    ├── fastmcp-skeleton.md
    ├── mcp-server-design-01.md
    ├── SYSTEM_DESIGN.md
    ├── API_SPECIFICATION.md
    └── COMPONENT_DESIGN.md
```

## Core Components

### 1. Configuration Management

**File**: `config/settings.py`

```python
from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

@dataclass
class ServerConfig:
    """Server configuration settings."""
    gemini_api_key: str
    server_name: str = "nanobanana-mcp-server"
    transport: str = "stdio"  # stdio or http
    host: str = "127.0.0.1"
    port: int = 9000
    mask_error_details: bool = False
    max_concurrent_requests: int = 10
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load configuration from environment variables."""
        load_dotenv()
        
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY must be set")
        
        return cls(
            gemini_api_key=api_key,
            transport=os.getenv("FASTMCP_TRANSPORT", "stdio"),
            host=os.getenv("FASTMCP_HOST", "127.0.0.1"),
            port=int(os.getenv("FASTMCP_PORT", "9000")),
            mask_error_details=os.getenv("FASTMCP_MASK_ERRORS", "false").lower() == "true",
        )

@dataclass
class GeminiConfig:
    """Gemini API specific configuration."""
    model_name: str = "gemini-2.5-flash-image"
    max_images_per_request: int = 4
    max_inline_image_size: int = 20 * 1024 * 1024  # 20MB
    default_image_format: str = "png"
    request_timeout: int = 30  # seconds
```

### 2. FastMCP Server Core

**File**: `core/server.py`

```python
from fastmcp import FastMCP
from typing import Dict, Any
import logging
from config.settings import ServerConfig

class NanoBananaMCP:
    """Main FastMCP server class."""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize FastMCP server
        self.server = FastMCP(
            name=config.server_name,
            instructions=self._get_server_instructions(),
            mask_error_details=config.mask_error_details
        )
        
        # Register components
        self._register_tools()
        self._register_resources()
        self._register_prompts()
    
    def _get_server_instructions(self) -> str:
        """Get server description and instructions."""
        return (
            "This server exposes image generation & editing powered by "
            "Gemini 2.5 Flash Image (aka 'nano banana'). It returns images "
            "as real MCP image content blocks, and also provides structured "
            "JSON with metadata and reproducibility hints."
        )
    
    def _register_tools(self):
        """Register all tools with the server."""
        from tools.generate_image import register_generate_image_tool
        from tools.edit_image import register_edit_image_tool
        from tools.upload_file import register_upload_file_tool
        
        register_generate_image_tool(self.server)
        register_edit_image_tool(self.server)
        register_upload_file_tool(self.server)
    
    def _register_resources(self):
        """Register all resources with the server."""
        from resources.file_metadata import register_file_metadata_resource
        from resources.template_catalog import register_template_catalog_resource
        
        register_file_metadata_resource(self.server)
        register_template_catalog_resource(self.server)
    
    def _register_prompts(self):
        """Register all prompts with the server."""
        from prompts.photography import register_photography_prompts
        from prompts.design import register_design_prompts
        from prompts.editing import register_editing_prompts
        
        register_photography_prompts(self.server)
        register_design_prompts(self.server)
        register_editing_prompts(self.server)
    
    def run(self):
        """Start the server."""
        if self.config.transport == "http":
            self.server.run(
                transport="http",
                host=self.config.host,
                port=self.config.port
            )
        else:
            self.server.run()
```

### 3. Gemini API Client Service

**File**: `services/gemini_client.py`

```python
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
```

### 4. Image Service

**File**: `services/image_service.py`

```python
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
```

### 5. Tool Implementation

**File**: `tools/generate_image.py`

```python
from typing import Annotated, Optional, List
from pydantic import Field
from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult
from services.image_service import ImageService
from core.exceptions import ValidationError
import logging

def register_generate_image_tool(server: FastMCP):
    """Register the generate_image tool with the FastMCP server."""
    
    @server.tool(
        annotations={
            "title": "Generate image (Gemini 2.5 Flash Image)",
            "readOnlyHint": True,
            "openWorldHint": True,
        }
    )
    def generate_image(
        prompt: Annotated[str, Field(
            description="Clear, detailed image prompt. Include subject, composition, "
                       "action, location, style, and any text to render. Add 'Square image' "
                       "or '16:9' in the text to influence aspect ratio.",
            min_length=1,
            max_length=8192
        )],
        n: Annotated[int, Field(
            description="Requested image count (model may return fewer).",
            ge=1,
            le=4
        )] = 1,
        negative_prompt: Annotated[Optional[str], Field(
            description="Things to avoid (style, objects, text).",
            max_length=1024
        )] = None,
        system_instruction: Annotated[Optional[str], Field(
            description="Optional system tone/style guidance.",
            max_length=512
        )] = None,
        images_b64: Annotated[Optional[List[str]], Field(
            description="Inline base64 input images for composition/editing.",
            max_length=4
        )] = None,
        mime_types: Annotated[Optional[List[str]], Field(
            description="MIME types matching images_b64."
        )] = None,
        ctx: Context = None,
    ) -> ToolResult:
        """
        Generate one or more images from a text prompt, optionally conditioned on input images.
        Returns both MCP image content blocks and structured JSON with metadata.
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Validation
            if images_b64 and mime_types:
                if len(images_b64) != len(mime_types):
                    raise ValidationError("images_b64 and mime_types must have same length")
            
            # Get services (would be injected in real implementation)
            image_service = _get_image_service()
            
            # Prepare input images
            input_images = None
            if images_b64 and mime_types:
                input_images = list(zip(images_b64, mime_types))
            
            # Generate images
            mcp_images, metadata = image_service.generate_images(
                prompt=prompt,
                n=n,
                negative_prompt=negative_prompt,
                system_instruction=system_instruction,
                input_images=input_images
            )
            
            # Create response
            summary = (
                f"Generated {len(mcp_images)} image(s) with Gemini 2.5 Flash Image from your prompt."
            )
            if input_images:
                summary += " Included edits/conditioning from provided image(s)."
            
            return ToolResult(
                content=[summary] + mcp_images,
                structured_content={
                    "requested": n,
                    "returned": len(mcp_images),
                    "negative_prompt_applied": bool(negative_prompt),
                    "used_inline_images": bool(images_b64),
                    "images": metadata,
                }
            )
            
        except ValidationError as e:
            logger.error(f"Validation error in generate_image: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in generate_image: {e}")
            raise

def _get_image_service() -> ImageService:
    """Get the image service instance (would be dependency injection in real app)."""
    # This would be properly injected in a real implementation
    pass
```

### 6. Resource Implementation

**File**: `resources/template_catalog.py`

```python
from fastmcp import FastMCP
from typing import Dict, Any
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
            return {
                "photorealistic_shot": {
                    "description": "High-fidelity photography template.",
                    "parameters": ["subject", "composition", "lighting", "camera", "aspect_hint"],
                    "category": "photography",
                    "use_cases": ["portraits", "landscapes", "product photography"]
                },
                "logo_text": {
                    "description": "Accurate text rendering in a clean logo.",
                    "parameters": ["brand", "text", "font_style", "style_desc", "color_scheme"],
                    "category": "design",
                    "use_cases": ["branding", "marketing", "corporate identity"]
                },
                "product_shot": {
                    "description": "Studio product mockup for e-commerce.",
                    "parameters": ["product", "background", "lighting_setup", "angle", "aspect_hint"],
                    "category": "commercial",
                    "use_cases": ["e-commerce", "catalog", "advertising"]
                },
                "sticker_flat": {
                    "description": "Kawaii/flat sticker with bold lines and white background.",
                    "parameters": ["character", "accessory", "palette"],
                    "category": "illustration",
                    "use_cases": ["messaging apps", "social media", "gaming"]
                },
                "iterative_edit_instruction": {
                    "description": "Concise edit instruction phrasing for image modifications.",
                    "parameters": ["what_to_change", "how_it_should_blend"],
                    "category": "editing",
                    "use_cases": ["photo retouching", "creative editing", "corrections"]
                },
                "composition_and_style_transfer": {
                    "description": "Blend multiple images and transfer artistic styles.",
                    "parameters": ["target_subject", "style_reference", "style_desc"],
                    "category": "artistic",
                    "use_cases": ["artistic rendering", "style exploration", "creative projects"]
                },
            }
            
        except Exception as e:
            logger.error(f"Error generating template catalog: {e}")
            raise
```

### 7. Prompt Implementation

**File**: `prompts/photography.py`

```python
from typing import Literal
from fastmcp import FastMCP
import logging

def register_photography_prompts(server: FastMCP):
    """Register photography-related prompts with the FastMCP server."""
    
    @server.prompt
    def photorealistic_shot(
        subject: str,
        composition: str,
        lighting: str,
        camera: str,
        aspect_hint: Literal["Square image", "Portrait", "Landscape", "16:9", "4:3"] = "Square image",
    ) -> str:
        """Generate a prompt for high-quality photorealistic images."""
        logger = logging.getLogger(__name__)
        
        try:
            return (
                f"A photorealistic {subject}. Composition: {composition}. "
                f"Lighting: {lighting}. Camera: {camera}. {aspect_hint}."
            )
        except Exception as e:
            logger.error(f"Error generating photorealistic_shot prompt: {e}")
            raise
```

### 8. Utility Components

**File**: `utils/image_utils.py`

```python
from typing import Tuple
import base64
from PIL import Image
from io import BytesIO
import logging

def validate_image_format(mime_type: str) -> bool:
    """Validate that the MIME type is supported."""
    supported_types = [
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/webp",
        "image/gif"
    ]
    return mime_type.lower() in supported_types

def get_image_dimensions(image_b64: str) -> Tuple[int, int]:
    """Get image dimensions from base64 data."""
    try:
        image_data = base64.b64decode(image_b64)
        image = Image.open(BytesIO(image_data))
        return image.size
    except Exception as e:
        logging.error(f"Failed to get image dimensions: {e}")
        raise ValueError(f"Invalid image data: {e}")

def optimize_image_size(image_b64: str, max_size: int = 20 * 1024 * 1024) -> str:
    """Optimize image size if it exceeds the maximum limit."""
    image_data = base64.b64decode(image_b64)
    
    if len(image_data) <= max_size:
        return image_b64
    
    # Could implement compression logic here
    # For now, just raise an error
    raise ValueError(f"Image size {len(image_data)} exceeds maximum {max_size}")

def convert_image_format(image_b64: str, target_format: str = "PNG") -> str:
    """Convert image to specified format."""
    try:
        image_data = base64.b64decode(image_b64)
        image = Image.open(BytesIO(image_data))
        
        output = BytesIO()
        image.save(output, format=target_format)
        output.seek(0)
        
        return base64.b64encode(output.read()).decode()
    except Exception as e:
        logging.error(f"Failed to convert image format: {e}")
        raise ValueError(f"Image format conversion failed: {e}")
```

## Component Integration

### Dependency Injection Pattern

```python
# main.py or server.py
from config.settings import ServerConfig, GeminiConfig
from core.server import NanoBananaMCP
from services.gemini_client import GeminiClient
from services.image_service import ImageService

def create_app() -> NanoBananaMCP:
    """Application factory function."""
    # Load configuration
    server_config = ServerConfig.from_env()
    gemini_config = GeminiConfig()
    
    # Create services
    gemini_client = GeminiClient(server_config, gemini_config)
    image_service = ImageService(gemini_client, gemini_config)
    
    # Create and configure server
    app = NanoBananaMCP(server_config)
    
    # Inject dependencies (this would be done more elegantly with a DI container)
    app.image_service = image_service
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run()
```

## Testing Strategy

### Unit Test Structure

```python
# tests/test_image_service.py
import pytest
from unittest.mock import Mock, patch
from services.image_service import ImageService
from services.gemini_client import GeminiClient
from config.settings import GeminiConfig

class TestImageService:
    @pytest.fixture
    def mock_gemini_client(self):
        return Mock(spec=GeminiClient)
    
    @pytest.fixture
    def gemini_config(self):
        return GeminiConfig()
    
    @pytest.fixture
    def image_service(self, mock_gemini_client, gemini_config):
        return ImageService(mock_gemini_client, gemini_config)
    
    def test_generate_images_success(self, image_service, mock_gemini_client):
        # Setup mock
        mock_response = Mock()
        mock_gemini_client.generate_content.return_value = mock_response
        mock_gemini_client.extract_images.return_value = [b'fake_image_data']
        
        # Execute
        images, metadata = image_service.generate_images("test prompt", n=1)
        
        # Assert
        assert len(images) == 1
        assert len(metadata) == 1
        assert metadata[0]['synthid_watermark'] is True
```

## Performance Considerations

### Memory Management

1. **Stream Processing**: Large images processed in streams
2. **Lazy Loading**: Services initialized only when needed
3. **Resource Cleanup**: Proper cleanup of temporary data
4. **Connection Pooling**: Reuse HTTP connections for API calls

### Error Recovery

1. **Circuit Breaker**: Prevent cascading failures
2. **Retry Logic**: Exponential backoff for transient errors
3. **Graceful Degradation**: Partial results when possible
4. **Health Checks**: Monitor service availability

This component design provides a robust, maintainable architecture that supports the full functionality of the Nano Banana MCP Server while enabling easy testing, extension, and deployment.