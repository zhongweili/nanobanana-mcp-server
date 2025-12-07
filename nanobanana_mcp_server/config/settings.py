from dataclasses import dataclass, field
from enum import Enum
import os
from pathlib import Path

from dotenv import load_dotenv

from ..core.exceptions import ADCConfigurationError
from .constants import AUTH_ERROR_MESSAGES


class ModelTier(str, Enum):
    """Model selection options."""
    FLASH = "flash"  # Speed-optimized (Gemini 2.5 Flash)
    PRO = "pro"      # Quality-optimized (Gemini 3 Pro)
    AUTO = "auto"    # Automatic selection


class AuthMethod(Enum):
    """Authentication method options."""
    API_KEY = "api_key"      # Developer API + API Key
    VERTEX_AI = "vertex_ai"  # Vertex AI API + ADC
    AUTO = "auto"            # Auto-detect


class ThinkingLevel(str, Enum):
    """Gemini 3 thinking levels for advanced reasoning."""
    LOW = "low"      # Minimal latency, less reasoning
    HIGH = "high"    # Maximum reasoning (default for Pro)


class MediaResolution(str, Enum):
    """Media resolution for vision processing."""
    LOW = "low"      # Faster, less detail
    MEDIUM = "medium"  # Balanced
    HIGH = "high"    # Maximum detail


@dataclass
class ServerConfig:
    """Server configuration settings."""

    gemini_api_key: str | None = None
    server_name: str = "nanobanana-mcp-server"
    transport: str = "stdio"  # stdio or http
    host: str = "127.0.0.1"
    port: int = 9000
    mask_error_details: bool = False
    max_concurrent_requests: int = 10
    image_output_dir: str = ""
    auth_method: AuthMethod = AuthMethod.AUTO
    gcp_project_id: str | None = None
    gcp_region: str = "us-central1"

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load configuration from environment variables."""
        load_dotenv()

        # Auth method
        auth_method_str = os.getenv("NANOBANANA_AUTH_METHOD", "auto").lower()
        try:
            auth_method = AuthMethod(auth_method_str)
        except ValueError:
            auth_method = AuthMethod.AUTO

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        gcp_project = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
        gcp_region = os.getenv("GCP_REGION") or os.getenv("GOOGLE_CLOUD_LOCATION") or "us-central1"

        # Validation logic
        if auth_method == AuthMethod.API_KEY:
            if not api_key:
                raise ValueError(AUTH_ERROR_MESSAGES["api_key_required"])
        
        elif auth_method == AuthMethod.VERTEX_AI:
            if not gcp_project:
                raise ADCConfigurationError(AUTH_ERROR_MESSAGES["vertex_ai_project_required"])
        
        else:  # AUTO
            if not api_key:
                if not gcp_project:
                    raise ValueError(AUTH_ERROR_MESSAGES["no_auth_configured"])
                auth_method = AuthMethod.VERTEX_AI
            else:
                auth_method = AuthMethod.API_KEY

        # Handle image output directory
        output_dir = os.getenv("IMAGE_OUTPUT_DIR", "").strip()
        if not output_dir:
            # Default to ~/nanobanana-images in user's home directory for better compatibility
            output_dir = str(Path.home() / "nanobanana-images")

        # Convert to absolute path and ensure it exists
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)

        return cls(
            gemini_api_key=api_key,
            auth_method=auth_method,
            gcp_project_id=gcp_project,
            gcp_region=gcp_region,
            transport=os.getenv("FASTMCP_TRANSPORT", "stdio"),
            host=os.getenv("FASTMCP_HOST", "127.0.0.1"),
            port=int(os.getenv("FASTMCP_PORT", "9000")),
            mask_error_details=os.getenv("FASTMCP_MASK_ERRORS", "false").lower() == "true",
            image_output_dir=str(output_path),
        )


@dataclass
class BaseModelConfig:
    """Shared base configuration for all models."""
    max_images_per_request: int = 4
    max_inline_image_size: int = 20 * 1024 * 1024  # 20MB
    default_image_format: str = "png"
    request_timeout: int = 60  # seconds


@dataclass
class FlashImageConfig(BaseModelConfig):
    """Gemini 2.5 Flash Image configuration (speed-optimized)."""
    model_name: str = "gemini-2.5-flash-image"
    max_resolution: int = 1024
    supports_thinking: bool = False
    supports_grounding: bool = False
    supports_media_resolution: bool = False


@dataclass
class ProImageConfig(BaseModelConfig):
    """Gemini 3 Pro Image configuration (quality-optimized)."""
    model_name: str = "gemini-3-pro-image-preview"
    max_resolution: int = 3840  # 4K
    default_resolution: str = "high"  # low/medium/high
    default_thinking_level: ThinkingLevel = ThinkingLevel.HIGH
    default_media_resolution: MediaResolution = MediaResolution.HIGH
    supports_thinking: bool = True
    supports_grounding: bool = True
    supports_media_resolution: bool = True
    enable_search_grounding: bool = True
    request_timeout: int = 90  # Pro model needs more time for 4K


@dataclass
class ModelSelectionConfig:
    """Configuration for intelligent model selection."""
    default_tier: ModelTier = ModelTier.AUTO
    auto_quality_keywords: list[str] = field(default_factory=lambda: [
        "4k", "high quality", "professional", "production",
        "high-res", "high resolution", "detailed", "sharp", "crisp",
        "hd", "ultra", "premium", "magazine", "print"
    ])
    auto_speed_keywords: list[str] = field(default_factory=lambda: [
        "quick", "fast", "draft", "prototype", "sketch",
        "rapid", "rough", "temporary", "test"
    ])

    @classmethod
    def from_env(cls) -> "ModelSelectionConfig":
        """Load model selection config from environment."""
        load_dotenv()

        model_tier_str = os.getenv("NANOBANANA_MODEL", "auto").lower()
        try:
            default_tier = ModelTier(model_tier_str)
        except ValueError:
            default_tier = ModelTier.AUTO

        return cls(default_tier=default_tier)


@dataclass
class GeminiConfig:
    """Legacy Gemini API configuration (backward compatibility)."""
    model_name: str = "gemini-2.5-flash-image"
    max_images_per_request: int = 4
    max_inline_image_size: int = 20 * 1024 * 1024  # 20MB
    default_image_format: str = "png"
    request_timeout: int = 60  # seconds - increased for image generation
