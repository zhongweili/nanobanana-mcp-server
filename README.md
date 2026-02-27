# Nano Banana MCP Server 🍌

A production-ready **Model Context Protocol (MCP)** server that provides AI-powered image generation capabilities through Google's **Gemini** models with intelligent model selection.

## ⭐ NEW: Nano Banana 2 — Gemini 3.1 Flash Image! 🍌🚀

**Nano Banana 2** (`gemini-3.1-flash-image-preview`) is now the **default model** — delivering Pro-level quality at Flash speed:

- 🍌 **Flash Speed + 4K Quality**: Up to 3840px at Gemini 2.5 Flash latency
- 🌐 **Google Search Grounding**: Real-world knowledge for factually accurate images
- 🎯 **Subject Consistency**: Up to 5 characters and 14 objects per scene
- ✍️ **Precision Text Rendering**: Crystal-clear text placement in images
- 🏆 **Gemini 3 Pro Image** still available for maximum reasoning depth

<a href="https://glama.ai/mcp/servers/@zhongweili/nanobanana-mcp-server">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@zhongweili/nanobanana-mcp-server/badge" alt="nanobanana-mcp-server MCP server" />
</a>

## ✨ Features

- 🎨 **Multi-Model AI Image Generation**: Three Gemini models with intelligent automatic selection
- 🍌 **Gemini 3.1 Flash Image (NB2)**: Default model — 4K resolution at Flash speed with grounding
- 🏆 **Gemini 3 Pro Image**: Maximum reasoning depth for the most complex compositions
- ⚡ **Gemini 2.5 Flash Image**: Legacy Flash model for high-volume rapid prototyping
- 🤖 **Smart Model Selection**: Automatically routes to NB2 or Pro based on your prompt
- 📐 **Aspect Ratio Control** ⭐ NEW: Specify output dimensions (1:1, 16:9, 9:16, 21:9, and more)
- 📋 **Smart Templates**: Pre-built prompt templates for photography, design, and editing
- 📁 **File Management**: Upload and manage files via Gemini Files API
- 🔍 **Resource Discovery**: Browse templates and file metadata through MCP resources
- 🛡️ **Production Ready**: Comprehensive error handling, logging, and validation
- ⚡ **High Performance**: Optimized architecture with intelligent caching

## 🚀 Quick Start

### Prerequisites

1. **Google Gemini API Key** - [Get one free here](https://makersuite.google.com/app/apikey)
2. **Python 3.11+** (for development only)

### Installation

Option 1: From MCP Registry (Recommended)
This server is available in the [Model Context Protocol Registry](https://registry.modelcontextprotocol.io/?q=nanobanana). Search for "nanobanana" or use the MCP name below with your MCP client.

mcp-name: io.github.zhongweili/nanobanana-mcp-server

Option 2: Using `uvx`

```bash
uvx nanobanana-mcp-server@latest
```

Option 3: Using `pip`

```bash
pip install nanobanana-mcp-server
```

## 🔧 Configuration

### Authentication Methods

Nano Banana supports two authentication methods via `NANOBANANA_AUTH_METHOD`:

1. **API Key** (`api_key`): Uses `GEMINI_API_KEY`. Best for local development and simple deployments.
2. **Vertex AI ADC** (`vertex_ai`): Uses Google Cloud Application Default Credentials. Best for production on Google Cloud (Cloud Run, GKE, GCE).
3. **Automatic** (`auto`): Defaults to API Key if present, otherwise tries Vertex AI.

#### 1. API Key Authentication (Default)

Set `GEMINI_API_KEY` environment variable.

#### 2. Vertex AI Authentication (Google Cloud)

Required environment variables:

- `NANOBANANA_AUTH_METHOD=vertex_ai` (or `auto`)
- `GCP_PROJECT_ID=your-project-id`
- `GCP_REGION=us-central1` (default)

**Prerequisites**:

- Enable Vertex AI API: `gcloud services enable aiplatform.googleapis.com`
- Grant IAM Role: `roles/aiplatform.user` to the service account.

### Claude Desktop

#### Option 1: Using Published Server (Recommended)

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nanobanana": {
      "command": "uvx",
      "args": ["nanobanana-mcp-server@latest"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    }
  }
}
```

#### Option 2: Using Local Source (Development)

If you are running from source code, point to your local installation:

```json
{
  "mcpServers": {
    "nanobanana-local": {
      "command": "uv",
      "args": ["run", "python", "-m", "nanobanana_mcp_server.server"],
      "cwd": "/absolute/path/to/nanobanana-mcp-server",
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    }
  }
}
```

#### Option 3: Using Vertex AI (ADC)

To authenticate with Google Cloud Application Default Credentials (instead of an API Key):

```json
{
  "mcpServers": {
    "nanobanana-adc": {
      "command": "uvx",
      "args": ["nanobanana-mcp-server@latest"],
      "env": {
        "NANOBANANA_AUTH_METHOD": "vertex_ai",
        "GCP_PROJECT_ID": "your-project-id",
        "GCP_REGION": "us-central1"
      }
    }
  }
}
```

**Configuration file locations:**

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Claude Code (VS Code Extension)

Install and configure in VS Code:

1. Install the Claude Code extension
2. Open Command Palette (`Cmd/Ctrl + Shift + P`)
3. Run "Claude Code: Add MCP Server"
4. Configure:
   ```json
   {
     "name": "nanobanana",
     "command": "uvx",
     "args": ["nanobanana-mcp-server@latest"],
     "env": {
       "GEMINI_API_KEY": "your-gemini-api-key-here"
     }
   }
   ```

### Cursor

Add to Cursor's MCP configuration:

```json
{
  "mcpServers": {
    "nanobanana": {
      "command": "uvx",
      "args": ["nanobanana-mcp-server@latest"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    }
  }
}
```

### Continue.dev (VS Code/JetBrains)

Add to your `config.json`:

```json
{
  "mcpServers": [
    {
      "name": "nanobanana",
      "command": "uvx",
      "args": ["nanobanana-mcp-server@latest"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    }
  ]
}
```

### Open WebUI

Configure in Open WebUI settings:

```json
{
  "mcp_servers": {
    "nanobanana": {
      "command": ["uvx", "nanobanana-mcp-server@latest"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    }
  }
}
```

### Gemini CLI / Generic MCP Client

```bash
# Set environment variable
export GEMINI_API_KEY="your-gemini-api-key-here"

# Run server in stdio mode
uvx nanobanana-mcp-server@latest

# Or with pip installation
python -m nanobanana_mcp_server.server
```

## 🤖 Model Selection

Nano Banana supports three Gemini models with intelligent automatic selection:

### 🍌 NB2 — Nano Banana 2 (Gemini 3.1 Flash Image) ⭐ DEFAULT

**Flash speed with Pro-level quality — the best of both worlds**

- **Quality**: Production-ready 4K output
- **Resolution**: Up to 4K (3840px)
- **Speed**: ~2-4 seconds per image (Flash-class latency)
- **Special Features**:
  - 🌐 **Google Search Grounding**: Real-world knowledge for factually accurate images
  - 🎯 **Subject Consistency**: Up to 5 characters and 14 objects per scene
  - ✍️ **Precision Text Rendering**: Clear, well-placed text in images
- **Best for**: Almost everything — production assets, marketing, photography, text overlays
- **model_tier**: `"nb2"` (or `"auto"` — NB2 is the auto default)

### 🏆 Pro Model — Nano Banana Pro (Gemini 3 Pro Image)

**Maximum reasoning depth for the most demanding compositions**

- **Quality**: Highest available
- **Resolution**: Up to 4K (3840px)
- **Speed**: ~5-8 seconds per image
- **Special Features**:
  - 🧠 **Advanced Reasoning**: Configurable thinking levels (LOW/HIGH)
  - 🌐 **Google Search Grounding**: Real-world knowledge integration
  - 📐 **Media Resolution Control**: Fine-tune vision processing detail
- **Best for**: Complex narrative scenes, intricate compositions, maximum reasoning required
- **model_tier**: `"pro"`

### ⚡ Flash Model (Gemini 2.5 Flash Image)

**Legacy model for high-volume rapid iteration**

- **Speed**: Very fast (2-3 seconds)
- **Resolution**: Up to 1024px
- **Best for**: High-volume generation, quick drafts where 4K is not needed
- **model_tier**: `"flash"`

### 🤖 Automatic Selection (Recommended)

By default, the server uses **AUTO** mode which routes to **NB2** unless Pro's deeper reasoning is clearly needed:

**Pro Model Selected When**:

- Strong quality keywords: "4K", "professional", "production", "high-res", "HD"
- High thinking level requested: `thinking_level="HIGH"`
- Multi-image conditioning with multiple input images

**NB2 Model Selected When** (default):

- Standard requests, everyday image generation
- Speed keywords: "quick", "draft", "sketch", "rapid"
- High-volume batch generation (`n > 2`)

### Usage Examples

```python
# Automatic selection (recommended) — routes to NB2 by default
"A cat sitting on a windowsill"             # → NB2 (default)
"Quick sketch of a cat"                     # → NB2 (speed keyword, NB2 is fast enough)
"Professional 4K product photo"             # → Pro (strong quality keywords)

# Explicit NB2 selection
generate_image(
    prompt="Product photo on white background",
    model_tier="nb2",              # Nano Banana 2 (Flash speed + 4K)
    resolution="4k",
    enable_grounding=True
)

# Leverage Nano Banana Pro for complex reasoning
generate_image(
    prompt="Cinematic scene: three characters in a tense standoff at dusk",
    model_tier="pro",              # Pro for deep reasoning
    resolution="4k",
    thinking_level="HIGH",         # Enhanced reasoning
    enable_grounding=True
)

# Legacy Flash for high-volume drafts
generate_image(
    prompt="Simple icon",
    model_tier="flash"             # Fast 1024px generation
)

# Control aspect ratio for different formats ⭐ NEW!
generate_image(
    prompt="Cinematic landscape at sunset",
    aspect_ratio="21:9"            # Ultra-wide cinematic format
)

generate_image(
    prompt="Instagram post about coffee",
    aspect_ratio="1:1"             # Square format for social media
)

generate_image(
    prompt="YouTube thumbnail design",
    aspect_ratio="16:9"            # Standard video format
)

generate_image(
    prompt="Mobile wallpaper of mountain vista",
    aspect_ratio="9:16"            # Portrait format for phones
)
```

### 📐 Aspect Ratio Control

Control the output image dimensions with the `aspect_ratio` parameter:

**Supported Aspect Ratios**:

- `1:1` - Square (Instagram, profile pictures)
- `4:3` - Classic photo format
- `3:4` - Portrait orientation
- `16:9` - Widescreen (YouTube thumbnails, presentations)
- `9:16` - Mobile portrait (phone wallpapers, stories)
- `21:9` - Ultra-wide cinematic
- `2:3`, `3:2`, `4:5`, `5:4` - Various photo formats

```python
# Examples for different use cases
generate_image(
    prompt="Product showcase for e-commerce",
    aspect_ratio="3:4",    # Portrait format, good for product pages
    model_tier="pro"
)

generate_image(
    prompt="Social media banner for Facebook",
    aspect_ratio="16:9"    # Landscape banner format
)
```

**Note**: Aspect ratio works with both Flash and Pro models. For best results with specific aspect ratios at high resolution, use the Pro model with `resolution="4k"`.

### 📁 Output Path Control ⭐ NEW!

Control where generated images are saved with the `output_path` parameter:

**Three modes of operation:**

1. **Specific file path** - Save to an exact file location:

```python
generate_image(
    prompt="A beautiful sunset",
    output_path="/path/to/sunset.png"  # Exact file location
)
```

2. **Directory path** - Use auto-generated filename in a specific directory:

```python
generate_image(
    prompt="Product photo",
    output_path="/path/to/products/"  # Trailing slash indicates directory
)
```

3. **Default location** - Uses IMAGE_OUTPUT_DIR or ~/nanobanana-images:

```python
generate_image(
    prompt="Random image"
    # output_path defaults to None
)
```

**Multiple images (n > 1):**
When generating multiple images with a file path, images are automatically numbered:

- First image: `/path/to/image.png`
- Second image: `/path/to/image_2.png`
- Third image: `/path/to/image_3.png`

**Precedence Rules:**

1. `output_path` parameter (if provided) - highest priority
2. `IMAGE_OUTPUT_DIR` environment variable
3. `~/nanobanana-images` (default fallback)

```python
# Save to specific location with Pro model
generate_image(
    prompt="Professional headshot",
    model_tier="pro",
    output_path="/Users/me/photos/headshot.png"
)

# Save multiple images to a directory
generate_image(
    prompt="Product variations",
    n=4,
    output_path="/path/to/products/"  # Each gets unique filename
)
```

## ⚙️ Environment Variables

Configuration options:

```bash
# Authentication (Required)
# Method 1: API Key
GEMINI_API_KEY=your-gemini-api-key-here

# Method 2: Vertex AI (Google Cloud)
NANOBANANA_AUTH_METHOD=vertex_ai
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# Model Selection (optional)
NANOBANANA_MODEL=auto  # Options: flash, nb2, pro, auto (default: auto → nb2)

# Optional
IMAGE_OUTPUT_DIR=/path/to/image/directory  # Default: ~/nanobanana-images
LOG_LEVEL=INFO                             # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=standard                        # standard, json, detailed
```

## 🐛 Troubleshooting

### Common Issues

**"GEMINI_API_KEY not set"**

- Add your API key to the MCP server configuration in your client
- Get a free API key at [Google AI Studio](https://makersuite.google.com/app/apikey)

**"Server failed to start"**

- Ensure you're using the latest version: `uvx nanobanana-mcp-server@latest`
- Check that your client supports MCP (Claude Desktop 0.10.0+)

**"Permission denied" errors**

- The server creates images in `~/nanobanana-images` by default
- Ensure write permissions to your home directory

### Development Setup

For local development:

```bash
# Clone repository
git clone https://github.com/zhongweili/nanobanana-mcp-server.git
cd nanobanana-mcp-server

# Install with uv
uv sync

# Set environment
export GEMINI_API_KEY=your-api-key-here

# Run locally
uv run python -m nanobanana_mcp_server.server
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/zhongweili/nanobanana-mcp-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/zhongweili/nanobanana-mcp-server/discussions)
