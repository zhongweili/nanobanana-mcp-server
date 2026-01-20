"""Application constants."""

# Supported image formats
SUPPORTED_IMAGE_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"]

# Default aspect ratio options
ASPECT_RATIOS = ["Square image", "Portrait", "Landscape", "16:9", "4:3"]

# File processing constants
THUMBNAIL_SIZE = 256
TEMP_FILE_SUFFIX = ".tmp"
MAX_INPUT_IMAGES = 3

# Image processing defaults
DEFAULT_IMAGE_FORMAT = "png"
THUMBNAIL_FORMAT = "jpeg"

# Resolution presets (static values)
RESOLUTION_PRESETS = {
    "4k": (3840, 3840),
    "uhd": (3840, 2160),
    "2k": (2048, 2048),
    "fhd": (1920, 1080),
    "1080p": (1920, 1080),
    "hd": (1280, 720),
    "720p": (1280, 720),
    "480p": (854, 480),
    "square_lg": (1024, 1024),
    "square_md": (512, 512),
    "square_sm": (256, 256),
    "portrait_4k": (2160, 3840),
    "portrait_fhd": (1080, 1920),
    "landscape_4k": (3840, 2160),
    "landscape_fhd": (1920, 1080),
}

# Memory constants
MEMORY_LIMIT_MB_DEFAULT = 2048
MEMORY_BUFFER_PERCENT = 0.2  # 20% safety buffer
BYTES_PER_PIXEL_RGBA = 4
IMAGE_OVERHEAD_MULTIPLIER = 1.5  # Account for processing overhead

# Compression quality profiles
COMPRESSION_PROFILES = {
    "thumbnail": 70,
    "preview": 80,
    "display": 85,
    "original": 95,
    "lossless": 100,
}

# Model resolution limits
MODEL_RESOLUTION_LIMITS = {
    "flash": 2048,
    "pro": 3840,
}

# Aspect ratio limits (tightened for better usability)
MIN_ASPECT_RATIO = 0.25  # 1:4 ratio
MAX_ASPECT_RATIO = 4.0  # 4:1 ratio

# Template categories
TEMPLATE_CATEGORIES = {
    "photography": "High-quality photographic images",
    "design": "Logos, branding, and graphic design",
    "commercial": "Product shots and commercial photography",
    "illustration": "Artistic illustrations and drawings",
    "editing": "Photo editing and retouching",
    "artistic": "Creative and artistic rendering",
}

# Error messages
ERROR_MESSAGES = {
    "missing_api_key": "GEMINI_API_KEY or GOOGLE_API_KEY must be set in environment",
    "invalid_image_format": "Unsupported image format. Supported types: {types}",
    "image_too_large": "Image size ({size}) exceeds maximum limit ({limit})",
    "validation_error": "Parameter validation failed: {details}",
    "api_error": "Gemini API error: {details}",
    "unknown_error": "An unexpected error occurred: {details}",
}

# Authentication error messages
AUTH_ERROR_MESSAGES = {
    "vertex_ai_project_required": (
        "Vertex AI authentication requires GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT to be set."
    ),
    "api_key_required": (
        "API Key authentication requires GEMINI_API_KEY or GOOGLE_API_KEY to be set."
    ),
    "no_auth_configured": (
        "No valid authentication configuration found.\n"
        "API Key: Set GEMINI_API_KEY or GOOGLE_API_KEY\n"
        "Vertex AI: Set GCP_PROJECT_ID (and optionally GCP_REGION)"
    ),
}
