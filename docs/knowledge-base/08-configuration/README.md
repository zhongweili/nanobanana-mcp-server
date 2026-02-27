# Configuration

All configuration is environment-variable based. Copy `.env.example` → `.env` for local dev.

## Environment Variables

### Authentication (Required — one method must be set)

| Variable | Description | Example |
|----------|-------------|---------|
| `NANOBANANA_AUTH_METHOD` | `auto` \| `api_key` \| `vertex_ai` | `auto` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIza...` |
| `GOOGLE_API_KEY` | Alternative API key name | `AIza...` |
| `GCP_PROJECT_ID` | GCP project for Vertex AI | `my-project-123` |
| `GCP_REGION` | GCP region (**must be `global` for Pro model**) | `global` |

### Model Selection

| Variable | Default | Options |
|----------|---------|---------|
| `NANOBANANA_MODEL` | `auto` | `auto`, `flash`, `nb2`, `pro` |

### Output & Response

| Variable | Default | Description |
|----------|---------|-------------|
| `IMAGE_OUTPUT_DIR` | `~/nanobanana-images` | Base directory for saved images |
| `RETURN_FULL_IMAGE` | `false` | Return full resolution in MCP response instead of thumbnails |

### Server Transport

| Variable | Default | Description |
|----------|---------|-------------|
| `FASTMCP_TRANSPORT` | `stdio` | `stdio` or `http` |
| `FASTMCP_HOST` | `127.0.0.1` | HTTP mode only |
| `FASTMCP_PORT` | `9000` | HTTP mode only |
| `FASTMCP_MASK_ERRORS` | `true` | Hide internal error details from users |

### Logging

| Variable | Default | Options |
|----------|---------|---------|
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | `standard` | `standard`, `json`, `detailed` |

### Pro Model (Optional Tuning)

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_PRO_THINKING_LEVEL` | `high` | `low`, `high` |
| `GEMINI_PRO_ENABLE_GROUNDING` | `true` | Enable Google Search grounding |

## Configuration Classes

File: `nanobanana_mcp_server/config/settings.py`

| Class | Purpose |
|-------|---------|
| `ServerConfig` | Transport, host, port, auth method, error masking |
| `GeminiConfig` | Legacy Flash model settings |
| `FlashImageConfig` | Flash model: timeouts, image limits |
| `ProImageConfig` | Pro model: resolution, thinking level, grounding, media resolution |
| `NanoBanana2Config` | NB2 model: extends `ProImageConfig`, overrides model name + timeout, `supports_thinking=False` |
| `ModelSelectionConfig` | Auto-selection: quality/speed keywords, default tier |

**Loading priority:** env vars → `.env` file → dataclass defaults

## Enums

```python
class ModelTier(str, Enum):
    FLASH = "flash"   # gemini-2.5-flash-image (legacy, 1024px)
    PRO = "pro"       # gemini-3-pro-image-preview (max reasoning, 4K)
    NB2 = "nb2"       # gemini-3.1-flash-image-preview (default: Flash speed + 4K)
    AUTO = "auto"     # intelligent routing → NB2 or PRO

class AuthMethod(Enum):
    API_KEY = "api_key"
    VERTEX_AI = "vertex_ai"
    AUTO = "auto"     # try API key first, then Vertex AI

class ThinkingLevel(str, Enum):
    LOW = "low"
    HIGH = "high"

class MediaResolution(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    AUTO = "auto"
```

## Startup Validation

`ServerConfig.from_env()` validates at startup and raises `ConfigurationError` if:
- Neither `GEMINI_API_KEY`/`GOOGLE_API_KEY` nor `GCP_PROJECT_ID` is set
- `auth_method=api_key` but no API key present
- `auth_method=vertex_ai` but no `GCP_PROJECT_ID` present
