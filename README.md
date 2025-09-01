# Nano Banana MCP Server 🍌

A production-ready **Model Context Protocol (MCP)** server that provides AI-powered image generation and editing capabilities through Google's **Gemini 2.5 Flash Image** model. Built with **FastMCP** for seamless integration with AI development tools like Claude Desktop, Cursor, and VS Code.

## ✨ Features

- 🎨 **Image Generation**: Create images from detailed text prompts
- ✏️ **Image Editing**: Conversational image editing with style preservation  
- 📁 **File Management**: Upload and manage large files via Gemini Files API
- 📋 **Template System**: Pre-built prompt templates for common use cases
- 🔍 **Resource Discovery**: Browse available templates and file metadata
- 🛡️ **Production Ready**: Comprehensive error handling, logging, and validation
- ⚡ **High Performance**: Modular architecture with optimized processing
- 🔒 **Security**: Input validation, sanitization, and safe error handling

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Google Gemini API Key** ([Get one here](https://makersuite.google.com/app/apikey))
- **FastMCP CLI** (for development)

### Installation

#### Option 1: FastMCP CLI (Recommended for Development)

```bash
# Install FastMCP CLI
pip install fastmcp

# Clone the repository
git clone https://github.com/nano-banana/mcp-server.git
cd nanobanana-mcp-server

# Install with development dependencies
pip install -e .[dev]

# Set up environment
cp .env.example .env
# Edit .env to add your GEMINI_API_KEY
```

#### Option 2: Traditional Python Setup

```bash
# Clone the repository
git clone https://github.com/nano-banana/mcp-server.git
cd nanobanana-mcp-server

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or with modern uv (faster)
pip install uv
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional configuration
LOG_LEVEL=INFO
LOG_FORMAT=standard
FASTMCP_TRANSPORT=stdio
```

### Run the Server

#### Using FastMCP CLI (Recommended)

```bash
# Install FastMCP CLI
pip install fastmcp

# Run with development mode (includes MCP Inspector)
fastmcp dev server:create_app

# Run in production mode
fastmcp run server:create_app

# Run with specific environment variables
GEMINI_API_KEY=your_key fastmcp dev server:create_app

# Run with HTTP transport
FASTMCP_TRANSPORT=http fastmcp run server:create_app
```

#### Direct Python Execution

```bash
# Standard mode (STDIO transport)
python server.py

# HTTP mode (for remote access)
FASTMCP_TRANSPORT=http FASTMCP_PORT=8000 python server.py

# With custom logging
LOG_LEVEL=DEBUG LOG_FORMAT=json python server.py
```

#### FastMCP CLI Advanced Usage

```bash
# Install server in MCP clients (Claude Desktop, etc.)
fastmcp install

# Inspect server capabilities
fastmcp inspect server:create_app

# Create persistent project environment
fastmcp project prepare fastmcp.json

# Run with additional dependencies
fastmcp dev server:create_app --with pillow==10.4.0

# Run with configuration file
fastmcp run --config fastmcp.json
```

## 🛠️ Usage

### Tools Available

#### 1. `generate_image`
Generate images from text prompts with optional input image conditioning.

```python
{
    "prompt": "A photorealistic mountain landscape at sunset",
    "n": 2,
    "aspect_hint": "16:9",
    "negative_prompt": "blurry, low quality"
}
```

#### 2. `edit_image` 
Edit existing images using natural language instructions.

```python
{
    "instruction": "Add a wizard hat to the cat",
    "base_image_b64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "mime_type": "image/png"
}
```

#### 3. `upload_file`
Upload files to Gemini Files API for reuse across prompts.

```python
{
    "path": "/path/to/image.jpg",
    "display_name": "Reference Image"
}
```

### Resources Available

#### 1. `gemini://files/{name}`
Access file metadata from Gemini Files API.

#### 2. `nano-banana://prompt-templates`
Browse available prompt templates with examples.

### Prompt Templates

The server includes 6 pre-built prompt templates:

1. **`photorealistic_shot`** - High-quality photography
2. **`logo_text`** - Logo design with text rendering
3. **`product_shot`** - E-commerce product photography
4. **`sticker_flat`** - Kawaii/flat sticker designs
5. **`iterative_edit_instruction`** - Precise image editing
6. **`composition_and_style_transfer`** - Artistic style transfer

### Example Usage in MCP Client

```python
# Generate a professional product shot
result = mcp_client.call_tool("generate_image", {
    "prompt": mcp_client.get_prompt("product_shot", {
        "product": "wireless headphones",
        "background": "gradient backdrop",
        "lighting_setup": "three-point lighting",
        "angle": "45-degree angle",
        "aspect_hint": "Square image"
    })
})
```

## 🧪 Development Workflow

### FastMCP CLI Development

The project is optimized for FastMCP CLI development workflow:

```bash
# 1. Clone and setup
git clone <repository-url>
cd nanobanana-mcp-server

# 2. Install FastMCP CLI
pip install fastmcp

# 3. Set up environment
cp .env.example .env
# Edit .env to add your GEMINI_API_KEY

# 4. Run in development mode (with MCP Inspector)
fastmcp dev server:create_app

# 5. Test tools interactively via MCP Inspector
# - Visit the Inspector URL shown in console
# - Test image generation tools
# - Inspect server capabilities

# 6. Install in Claude Desktop for production testing
fastmcp install
```

### Quick Development Commands

```bash
# Development with hot reload
fastmcp dev server:create_app --with-editable .

# Run with debug logging
LOG_LEVEL=DEBUG fastmcp dev server:create_app

# Test specific functionality
fastmcp inspect server:create_app

# Package for distribution
fastmcp project prepare fastmcp.json
```

## 📁 Project Structure

```
nanobanana-mcp-server/
├── server.py              # Main entry point & factory function
├── fastmcp.json           # FastMCP CLI configuration
├── pyproject.toml         # Project configuration
├── ruff.toml              # Ruff linting configuration
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── config/               # Configuration management
│   ├── settings.py       # Server & API settings
│   └── constants.py      # Application constants
├── core/                 # Core functionality
│   ├── server.py         # FastMCP server setup
│   ├── exceptions.py     # Custom exceptions
│   └── validation.py     # Input validation
├── services/             # Business logic services
│   ├── gemini_client.py  # Gemini API wrapper
│   ├── image_service.py  # Image processing
│   └── file_service.py   # File management
├── tools/                # MCP tools implementation
│   ├── generate_image.py # Image generation tool
│   ├── edit_image.py     # Image editing tool
│   └── upload_file.py    # File upload tool
├── resources/            # MCP resources
│   ├── file_metadata.py  # File metadata resource
│   └── template_catalog.py # Template catalog
├── prompts/              # Prompt templates
│   ├── photography.py    # Photo templates
│   ├── design.py         # Design templates
│   └── editing.py        # Editing templates
├── utils/                # Utility functions
│   ├── image_utils.py    # Image processing utilities
│   ├── logging_utils.py  # Logging configuration
│   └── validation_utils.py # Additional validation
└── tests/                # Test suite
    └── ...
```

## 🔧 Development

### Setup Development Environment

```bash
# Install with development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run code formatting
ruff format .

# Run linting
ruff check .

# Run type checking
mypy .
```

### Run Tests

```bash
# Run test suite
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
```

### Code Quality

The project uses:
- **Ruff** for linting and formatting
- **MyPy** for type checking
- **pytest** for testing
- **pre-commit** for git hooks

## 🚀 Deployment

### Local Production

```bash
# Production settings
export GEMINI_API_KEY=your_production_key
export LOG_LEVEL=INFO
export LOG_FORMAT=json
export FASTMCP_MASK_ERRORS=true

# Run server
python server.py
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "server.py"]
```

### Process Management

```bash
# Using systemd
sudo systemctl start nanobanana-mcp-server
sudo systemctl enable nanobanana-mcp-server

# Using PM2
pm2 start "python server.py" --name nanobanana-mcp-server
```

## 📊 Monitoring

The server provides comprehensive logging:

```bash
# Standard logging
2024-01-15 10:30:00 - core.server - INFO - Server started successfully

# JSON structured logging  
{"timestamp": "2024-01-15T10:30:00Z", "level": "INFO", "message": "Image generated", "duration_ms": 3420}
```

### Health Monitoring

- Server startup validation
- API connectivity checks  
- Resource usage tracking
- Error rate monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.nanobanana.dev](https://docs.nanobanana.dev)
- **Issues**: [GitHub Issues](https://github.com/nano-banana/mcp-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nano-banana/mcp-server/discussions)

## 🙏 Acknowledgments

- Built with [FastMCP](https://gofastmcp.com/) framework
- Powered by [Google Gemini 2.5 Flash Image](https://ai.google.dev/gemini-api/docs/image-generation)
- Inspired by the [Model Context Protocol](https://modelcontextprotocol.io/) specification

---

**Made with ❤️ by the Nano Banana Team**