# Nano Banana MCP Server 🍌

A production-ready **Model Context Protocol (MCP)** server that provides AI-powered image generation capabilities through Google's **Gemini** models with intelligent model selection.

## ⭐ NEW: Gemini 3 Pro Image Support! 🚀

Now featuring **Nano Banana Pro** - Google's latest and most powerful image generation model:

- 🏆 **Professional 4K Quality**: Generate stunning images up to 3840px resolution
- 🌐 **Google Search Grounding**: Access real-world knowledge for factually accurate images
- 🧠 **Advanced Reasoning**: Configurable thinking levels for complex compositions
- 🎯 **Superior Text Rendering**: Crystal-clear text in images at high resolution
- 🎨 **Enhanced Understanding**: Better context comprehension for complex prompts

<a href="https://glama.ai/mcp/servers/@zhongweili/nanobanana-mcp-server">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@zhongweili/nanobanana-mcp-server/badge" alt="nanobanana-mcp-server MCP server" />
</a>

## ✨ Features

- 🎨 **Multi-Model AI Image Generation**: Intelligent selection between Flash (speed) and Pro (quality) models
- ⚡ **Gemini 2.5 Flash Image**: Fast generation (1024px) for rapid prototyping
- 🏆 **Gemini 3 Pro Image**: High-quality up to 4K with Google Search grounding
- 🤖 **Smart Model Selection**: Automatically chooses optimal model based on your prompt
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
      "args": [
        "run",
        "python",
        "-m",
        "nanobanana_mcp_server.server"
      ],
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

Nano Banana supports two Gemini models with intelligent automatic selection:

### 🏆 Pro Model - Nano Banana Pro (Gemini 3 Pro Image) ⭐ NEW!
**Google's latest and most advanced image generation model**

- **Quality**: Professional-grade, production-ready
- **Resolution**: Up to 4K (3840px) - highest available
- **Speed**: ~5-8 seconds per image
- **Special Features**:
  - 🌐 **Google Search Grounding**: Leverages real-world knowledge for accurate, contextual images
  - 🧠 **Advanced Reasoning**: Configurable thinking levels (LOW/HIGH) for complex compositions
  - 📐 **Media Resolution Control**: Fine-tune vision processing detail (LOW/MEDIUM/HIGH/AUTO)
  - 📝 **Superior Text Rendering**: Exceptional clarity for text-in-image generation
  - 🎨 **Enhanced Context Understanding**: Better interpretation of complex, narrative prompts
- **Best for**: Production assets, marketing materials, professional photography, high-fidelity outputs, images requiring text, factual accuracy
- **Cost**: Higher per image (premium quality)

### ⚡ Flash Model (Gemini 2.5 Flash Image)
**Fast, reliable model for rapid iteration**

- **Speed**: Very fast (2-3 seconds)
- **Resolution**: Up to 1024px
- **Quality**: High quality for everyday use
- **Best for**: Rapid prototyping, iterations, high-volume generation, drafts, sketches
- **Cost**: Lower per image

### 🤖 Automatic Selection (Recommended)

By default, the server uses **AUTO** mode which intelligently analyzes your prompt and requirements:

**Pro Model Selected When**:
- Quality keywords detected: "4K", "professional", "production", "high-res", "HD"
- High resolution requested: `resolution="4k"` or `resolution="high"`
- Google Search grounding enabled: `enable_grounding=True`
- High thinking level requested: `thinking_level="HIGH"`
- Multi-image conditioning with multiple input images

**Flash Model Selected When**:
- Speed keywords detected: "quick", "draft", "sketch", "rapid"
- High-volume batch generation: `n > 2`
- Standard or lower resolution requested
- No special Pro features required

### Usage Examples

```python
# Automatic selection (recommended)
"Generate a professional 4K product photo"  # → Pro model (quality keywords + 4K)
"Quick sketch of a cat"                     # → Flash model (speed keyword)
"Create a diagram with clear text labels"   # → Pro model (text rendering)
"Draft mockup for website hero section"     # → Flash model (draft keyword)

# Explicit model selection
generate_image(
    prompt="A scenic landscape",
    model_tier="flash"  # Force Flash model for speed
)

# Leverage Nano Banana Pro features
generate_image(
    prompt="Professional product photo of vintage camera on wooden desk",
    model_tier="pro",              # Use Pro model
    resolution="4k",               # 4K resolution (Pro-only)
    thinking_level="HIGH",         # Enhanced reasoning
    enable_grounding=True,         # Use Google Search for accuracy
    media_resolution="HIGH"        # High-detail vision processing
)

# Pro model for high-quality text rendering
generate_image(
    prompt="Infographic showing 2024 market statistics with clear labels",
    model_tier="pro",              # Pro excels at text rendering
    resolution="4k"                # Maximum clarity for text
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

### 📐 Aspect Ratio Control ⭐ NEW!

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
NANOBANANA_MODEL=auto  # Options: flash, pro, auto (default: auto)

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