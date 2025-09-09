# Nano Banana MCP Server 🍌

A production-ready **Model Context Protocol (MCP)** server that provides AI-powered image generation capabilities through Google's **Gemini 2.5 Flash Image** model.

## ✨ Features

- 🎨 **AI Image Generation**: Create high-quality images from detailed text prompts
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
This server is available in the [Model Context Protocol Registry](https://registry.modelcontextprotocol.io/servers/io.github.zhongweili/nanobanana-mcp-server). Install it using your MCP client.

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

##

### Claude Desktop

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

## ⚙️ Environment Variables

Optional configuration:

```bash
# Required
GEMINI_API_KEY=your-gemini-api-key-here

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
