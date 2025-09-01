from dataclasses import dataclass
import os
from pathlib import Path
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
    image_output_dir: str = ""

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load configuration from environment variables."""
        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY must be set")

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
            transport=os.getenv("FASTMCP_TRANSPORT", "stdio"),
            host=os.getenv("FASTMCP_HOST", "127.0.0.1"),
            port=int(os.getenv("FASTMCP_PORT", "9000")),
            mask_error_details=os.getenv("FASTMCP_MASK_ERRORS", "false").lower() == "true",
            image_output_dir=str(output_path),
        )


@dataclass
class GeminiConfig:
    """Gemini API specific configuration."""

    model_name: str = "gemini-2.5-flash-image-preview"
    max_images_per_request: int = 4
    max_inline_image_size: int = 20 * 1024 * 1024  # 20MB
    default_image_format: str = "png"
    request_timeout: int = 60  # seconds - increased for image generation
