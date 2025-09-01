"""Service registry for dependency injection."""

from typing import Optional
import os
from .gemini_client import GeminiClient
from .file_image_service import FileImageService
from .file_service import FileService
from .enhanced_image_service import EnhancedImageService
from .files_api_service import FilesAPIService
from .image_database_service import ImageDatabaseService
from .image_storage_service import ImageStorageService
from .maintenance_service import MaintenanceService
from ..config.settings import ServerConfig, GeminiConfig

# Global service instances (initialized by the server)
_gemini_client: Optional[GeminiClient] = None
_file_image_service: Optional[FileImageService] = None
_file_service: Optional[FileService] = None
_enhanced_image_service: Optional[EnhancedImageService] = None
_files_api_service: Optional[FilesAPIService] = None
_image_database_service: Optional[ImageDatabaseService] = None
_image_storage_service: Optional[ImageStorageService] = None
_maintenance_service: Optional[MaintenanceService] = None


def initialize_services(server_config: ServerConfig, gemini_config: GeminiConfig):
    """Initialize all services with configurations."""
    global \
        _gemini_client, \
        _file_image_service, \
        _file_service, \
        _enhanced_image_service, \
        _files_api_service, \
        _image_database_service, \
        _image_storage_service, \
        _maintenance_service

    # Initialize core services
    _gemini_client = GeminiClient(server_config, gemini_config)
    _file_image_service = FileImageService(_gemini_client, gemini_config, server_config)
    _file_service = FileService(_gemini_client)

    # Initialize enhanced services for workflows.md implementation
    out_dir = server_config.image_output_dir
    _image_database_service = ImageDatabaseService(db_path=os.path.join(out_dir, "images.db"))
    # Use a subdirectory within the configured output directory for temp images
    temp_images_dir = os.path.join(out_dir, "temp_images")
    _image_storage_service = ImageStorageService(gemini_config, temp_images_dir)
    _files_api_service = FilesAPIService(_gemini_client, _image_database_service)
    _enhanced_image_service = EnhancedImageService(
        _gemini_client, _files_api_service, _image_database_service, gemini_config, out_dir
    )
    _maintenance_service = MaintenanceService(_files_api_service, _image_database_service, out_dir)


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


def get_enhanced_image_service() -> EnhancedImageService:
    """Get the enhanced image service instance (workflows.md implementation)."""
    if _enhanced_image_service is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return _enhanced_image_service


def get_files_api_service() -> FilesAPIService:
    """Get the Files API service instance."""
    if _files_api_service is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return _files_api_service


def get_image_database_service() -> ImageDatabaseService:
    """Get the image database service instance."""
    if _image_database_service is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return _image_database_service


def get_maintenance_service() -> MaintenanceService:
    """Get the maintenance service instance."""
    if _maintenance_service is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return _maintenance_service


def get_image_storage_service() -> ImageStorageService:
    """Get the image storage service instance."""
    if _image_storage_service is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return _image_storage_service
