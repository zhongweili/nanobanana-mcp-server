# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a production-ready **Nano Banana MCP Server** - an AI-powered image generation and editing server that leverages Google's Gemini 2.5 Flash Image model through the FastMCP framework. The codebase implements a complete MCP (Model Context Protocol) server with modular architecture, comprehensive error handling, and production-ready features.

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
fastmcp dev nanobanana_mcp_server.server:create_app

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
- `ImageService`: High-level image operations (generation, editing, processing)
- `FileService`: File management and Gemini Files API integration
- `TemplateService`: Prompt template management and parameterization

**MCP Component Registration**:
- Tools: Registered via `register_*_tool()` functions in each tool module
- Resources: Registered via `register_*_resource()` functions
- Prompts: Organized by category (photography, design, editing) with registration functions

### Configuration Management

**Environment-Based Configuration** (`config/settings.py`):
- `ServerConfig`: Server transport, host, port, error masking
- `GeminiConfig`: Model settings, image limits, timeouts
- Loads from `.env` file or environment variables
- Validates required API keys at startup

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

**Generation Flow**:
1. Input validation and sanitization (`core/validation.py`)
2. Prompt template application (`prompts/` modules)
3. Gemini API call via `GeminiClient`
4. Response processing and image extraction (`ImageService`)
5. Metadata generation and SynthID tracking
6. FastMCP `Image` object creation for MCP transport

**Editing Flow**:
1. Base64 image decoding and validation
2. Instruction processing and prompt enhancement
3. Multi-modal Gemini API call (text + image)
4. Response processing maintaining image context
5. Result packaging with edit metadata

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