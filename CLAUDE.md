# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a production-ready **Nano Banana MCP Server** - an AI-powered image generation and editing server that leverages Google's Gemini models through the FastMCP framework. The codebase implements a complete MCP (Model Context Protocol) server with modular architecture, comprehensive error handling, and production-ready features.

### ⭐ NEW: Nano Banana Pro Integration

The server now supports **Gemini 3 Pro Image** (Google's latest and most advanced image generation model) alongside the existing Gemini 2.5 Flash Image model:

**Key Capabilities**:
- 🏆 **4K Resolution**: Up to 3840px professional-grade outputs
- 🌐 **Google Search Grounding**: Real-world knowledge integration for factual accuracy
- 🧠 **Advanced Reasoning**: Configurable thinking levels (LOW/HIGH) for complex compositions
- 📐 **Media Resolution Control**: Fine-grained vision processing tuning
- 🤖 **Intelligent Model Selection**: Automatic routing based on prompt analysis

**Architecture Enhancement**:
- `ModelSelector`: New service for intelligent model routing and selection logic
- `ProImageService`: Dedicated service for Gemini 3 Pro Image operations
- Multi-tier configuration: `ModelSelectionConfig`, `ProImageConfig` alongside existing `GeminiConfig`

## Development Commands

### Environment Setup
```bash
# Using uv (recommended)
uv sync

# Set up environment
cp .env.example .env
# Edit .env to add your GEMINI_API_KEY
```

### Running the Server
```bash
# FastMCP CLI (recommended for development)
# Note: Use mcp_dev.py wrapper to resolve relative import issues
fastmcp dev mcp_dev.py:app

# Direct Python execution
python -m nanobanana_mcp_server.server

# HTTP transport mode
FASTMCP_TRANSPORT=http python -m nanobanana_mcp_server.server
```

### Development Workflow
```bash
# Start development server (clean startup)
./scripts/cleanup-ports.sh && fastmcp dev nanobanana_mcp_server.server:create_app

# Code formatting and linting
ruff format .
ruff check .

# Type checking
mypy .

# Run tests
pytest
pytest --cov=. --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
```

## Architecture & Implementation

### Core Architecture Pattern

The codebase follows a **layered architecture** with clear separation of concerns:

1. **Entry Point Layer** (`server.py`) - Application factory and main entry point
2. **Core Layer** (`core/`) - FastMCP server setup and fundamental components
3. **Service Layer** (`services/`) - Business logic and external API integration
4. **Tool Layer** (`tools/`) - MCP tool implementations (generate_image, edit_image, upload_file)
5. **Resource Layer** (`resources/`) - MCP resource implementations (file metadata, templates)
6. **Prompt Layer** (`prompts/`) - Reusable prompt templates organized by category
7. **Configuration Layer** (`config/`) - Settings management and environment handling
8. **Utilities Layer** (`utils/`) - Shared utilities and helper functions

### Key Components

**Server Factory Pattern** (`server.py:create_app()`):
- Factory function used by FastMCP CLI: `fastmcp dev server:create_app`
- Handles configuration loading, service initialization, and dependency injection
- Returns configured `NanoBananaMCP` instance ready to run

**Service Layer Architecture**:
- `GeminiClient`: Low-level API wrapper with error handling and retry logic
- `ImageService`: High-level image operations for Flash model (generation, editing, processing)
- **`ProImageService`** ⭐: Specialized service for Gemini 3 Pro Image with 4K support and grounding
- **`ModelSelector`** ⭐: Intelligent routing between Flash and Pro models based on prompt analysis
- `ImageStorageService`: Image persistence with thumbnail generation and resource management
- `FileService`: File management and Gemini Files API integration
- `TemplateService`: Prompt template management and parameterization

**MCP Component Registration**:
- Tools: Registered via `register_*_tool()` functions in each tool module
- Resources: Registered via `register_*_resource()` functions
- Prompts: Organized by category (photography, design, editing) with registration functions

### Configuration Management

**Environment-Based Configuration** (`config/settings.py`):
- `ServerConfig`: Server transport, host, port, error masking
- `GeminiConfig`: Flash model settings, image limits, timeouts
- **`ProImageConfig`** ⭐: Pro model settings (4K resolution, thinking levels, media resolution, grounding)
- **`ModelSelectionConfig`** ⭐: Automatic model selection strategy (quality/speed keywords, default tier)
- Loads from `.env` file or environment variables
- Validates required auth credentials (API Key or Vertex AI settings) at startup

**Authentication Configuration**:
- `auth_method` (`auto`/`api_key`/`vertex_ai`): Controls authentication strategy
- `gemini_api_key`: For API Key auth
- `gcp_project_id` & `gcp_region`: For Vertex AI auth

**Model Tier Enum** (`ModelTier`):
- `FLASH`: Gemini 2.5 Flash Image (fast, 1024px)
- `PRO`: Gemini 3 Pro Image (quality, 4K)
- `AUTO`: Intelligent automatic selection (default)

**Configuration Priority**:
1. Environment variables
2. `.env` file values
3. Default values in dataclass definitions

### Dependency Management

**Key Dependencies**:
- `fastmcp>=2.11.0`: MCP server framework
- `google-genai>=0.3.0`: Gemini API integration
- `pillow>=10.4.0`: Image processing utilities
- `pydantic>=2.0.0`: Data validation and serialization

**Development Dependencies**:
- `ruff`: Fast Python linter and formatter
- `mypy`: Static type checker
- `pytest`: Testing framework with async support
- `pytest-cov`: Coverage reporting

### Error Handling Strategy

**Layered Error Handling**:
1. **Configuration Errors**: Fail fast at startup with clear messages
2. **Validation Errors**: Input validation with detailed error context
3. **API Errors**: Graceful handling of Gemini API failures with retries
4. **Runtime Errors**: Structured logging with error context preservation

**Custom Exception Hierarchy** (`core/exceptions.py`):
- Base exception classes for different error categories
- Context preservation for debugging
- User-friendly error messages vs internal logging

### Image Processing Pipeline

**Generation Flow with Model Selection** ⭐:
1. Input validation and sanitization (`core/validation.py`)
2. **Model selection via `ModelSelector`**: Analyzes prompt/params → selects Flash or Pro
3. Prompt template application and enhancement (`prompts/` modules)
4. Service-specific processing:
   - **Flash path**: `ImageService.generate_images()` → fast 1024px generation
   - **Pro path**: `ProImageService.generate_images()` → 4K with grounding/reasoning
5. Gemini API call via `GeminiClient` with model-specific config
6. Response processing and image extraction
7. Optional storage via `ImageStorageService` (thumbnails + full images)
8. Metadata generation (includes model tier, thinking level, resolution)
9. FastMCP `Image` object creation for MCP transport

**Pro Model Enhancement Features**:
- **Thinking Levels**: `LOW` (fast) or `HIGH` (enhanced reasoning) via `ThinkingLevel` enum
- **Media Resolution**: `LOW`, `MEDIUM`, `HIGH`, `AUTO` for vision processing detail
- **Search Grounding**: Optional Google Search integration for factual accuracy
- **Prompt Enhancement**: Automatic narrative expansion for better Pro model understanding
- **4K Support**: Resolution parameters `4k`, `high`, `2k`, `1k`

**Editing Flow**:
1. Base64 image decoding and validation
2. Instruction processing and prompt enhancement
3. **Model selection** (Pro model preferred for quality edits)
4. Multi-modal Gemini API call (text + image) with model-specific config
5. Response processing maintaining image context
6. Optional storage with thumbnails
7. Result packaging with edit metadata (includes model tier)

### Model Selection Logic ⭐

**Intelligent Routing** (`services/model_selector.py`):

The `ModelSelector` service provides automatic model selection based on multi-factor analysis:

**Selection Factors**:
1. **Explicit Tier**: User-specified `model_tier` parameter takes precedence
2. **Quality Keywords**: Detects "4K", "professional", "production", "high-res", "HD" in prompt
3. **Speed Keywords**: Detects "quick", "draft", "sketch", "rapid" in prompt
4. **Resolution Requirements**: `resolution="4k"` forces Pro model
5. **Feature Flags**: `enable_grounding=True` favors Pro model
6. **Batch Size**: `n > 2` favors Flash for speed
7. **Multi-image Conditioning**: Multiple input images favor Pro for better context
8. **Thinking Level**: `thinking_level="HIGH"` favors Pro model

**Decision Algorithm**:
- Calculates quality_score and speed_score based on weighted factors
- Strong quality indicators (4K, professional) have 2x weight
- Pro model selected when quality_score > speed_score
- Flash model selected otherwise (default for speed)

**Usage in Tools**:
```python
# In generate_image tool
selector = ModelSelector(flash_service, pro_service, config)
service, tier = selector.select_model(
    prompt=user_prompt,
    requested_tier=model_tier,  # "flash", "pro", or "auto"
    n=n,
    resolution=resolution,
    enable_grounding=enable_grounding,
    thinking_level=thinking_level
)
# Use selected service for generation
images, metadata = service.generate_images(...)
```

**Model Information API**:
- `get_model_info(tier)`: Returns detailed model capabilities and metadata
- Used for logging and user feedback

### Testing Architecture

**Test Categories** (configured in `pyproject.toml`):
- `unit`: Fast, isolated unit tests
- `integration`: Service integration tests
- `network`: Tests requiring API access
- `slow`: Long-running performance tests

**Coverage Requirements**:
- Minimum 80% coverage (`fail_under = 80`)
- Excludes test files, `__init__.py`, and debugging code
- HTML coverage reports generated in `htmlcov/`

### FastMCP Integration Patterns

**Tool Registration Pattern**:
```python
def register_generate_image_tool(server: FastMCP):
    @server.tool()
    def generate_image(...) -> ToolResult:
        # Implementation with mixed content return
        return ToolResult(content=[text_content, image_content])
```

**Resource Registration Pattern**:
```python
def register_file_metadata_resource(server: FastMCP):
    @server.resource("gemini://files/{name}")
    def get_file_metadata(name: str) -> dict:
        # Returns dict auto-converted to JSON
```

**Prompt Template Pattern**:
```python
def register_photography_prompts(server: FastMCP):
    @server.prompt()
    def photorealistic_shot(subject: str, ...) -> str:
        # Returns parameterized prompt string
```

## Production Considerations

### Logging Configuration
- Structured logging with configurable formats (standard/json/detailed)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Request correlation and performance timing
- Sensitive data filtering (API keys, user content)

### Security Features
- Input validation and sanitization
- API key protection in logs and error messages
- File size limits and type validation
- Error message masking for production (`mask_error_details`)

### Performance Optimizations
- Async/await patterns for I/O operations
- Connection pooling and reuse
- Image processing optimizations
- Memory management for large files

### Deployment Support
- Docker containerization ready
- Environment-based configuration
- Process management compatibility (systemd, PM2)
- Health check endpoints (when using HTTP transport)

## Common Issues & Troubleshooting

### FastMCP Development Issues

**Port Conflicts**:
```bash
# Quick fix: Use the cleanup script
./scripts/cleanup-ports.sh

# Then run normally
fastmcp dev nanobanana_mcp_server.server:create_app

# Alternative: Specify different ports if cleanup doesn't work
fastmcp dev nanobanana_mcp_server.server:create_app --ui-port 6275 --server-port 6278

# Manual cleanup if needed
pkill -f "@modelcontextprotocol/inspector"
pkill -f "fastmcp.*nanobanana_mcp_server.server"
```

**JSON Parsing Errors in STDIO**:
- **Fixed**: All logging now correctly uses `stderr` instead of `stdout`
- MCP STDIO transport requires `stdout` to be reserved for JSON-RPC messages only
- All application logs go to `stderr` to avoid interfering with MCP communication

**Deprecation Warnings**:
- **Fixed**: Updated FastMCP imports from `fastmcp.Image` to `fastmcp.utilities.types.Image`
- **Fixed**: Updated Pydantic field constraints from `max_items` to `max_length`

### Runtime Configuration

**API Key Setup**:
```bash
# Required environment variable
export GEMINI_API_KEY=your_api_key_here
# Alternative name also supported
export GOOGLE_API_KEY=your_api_key_here
```

**Timeout Configuration**:
- Default timeout increased to 60 seconds for image generation
- Configurable via `GeminiConfig.request_timeout` in `config/settings.py`
- MCP client-side timeouts may need adjustment for long operations

**Logging Levels**:
```bash
# Debug mode for development
LOG_LEVEL=DEBUG fastmcp dev nanobanana_mcp_server.server:create_app

# Production logging with JSON format
LOG_LEVEL=INFO LOG_FORMAT=json python -m nanobanana_mcp_server.server
```