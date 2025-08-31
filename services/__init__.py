"""Service registry for dependency injection."""

from typing import Optional
from services.gemini_client import GeminiClient
from services.file_image_service import FileImageService
from services.file_service import FileService
from config.settings import ServerConfig, GeminiConfig

# Global service instances (initialized by the server)
_gemini_client: Optional[GeminiClient] = None
_file_image_service: Optional[FileImageService] = None
_file_service: Optional[FileService] = None

def initialize_services(server_config: ServerConfig, gemini_config: GeminiConfig):
    """Initialize all services with configurations."""
    global _gemini_client, _file_image_service, _file_service
    
    _gemini_client = GeminiClient(server_config, gemini_config)
    _file_image_service = FileImageService(_gemini_client, gemini_config, server_config)
    _file_service = FileService(_gemini_client)

def get_image_service() -> FileImageService:
    """Get the image service instance."""
    if _file_image_service is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return _file_image_service

def get_file_service() -> FileService:
    """Get the file service instance."""
    if _file_service is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return _file_service

def get_gemini_client() -> GeminiClient:
    """Get the Gemini client instance."""
    if _gemini_client is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return _gemini_client

def get_file_image_service() -> FileImageService:
    """Get the file image service instance."""
    if _file_image_service is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return _file_image_service