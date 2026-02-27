# Deployment

This project is distributed as a **PyPI package**. End users install and run it locally via `uvx` or `pip`. There is no server-side deployment.

## Publishing to PyPI

Scripts: `scripts/build.py`, `scripts/upload.py`

```bash
# Build the package
uv run python scripts/build.py

# Upload to PyPI
uv run python scripts/upload.py
```

**No CI/CD pipeline** — publishing is done manually. [待确认: planned automation timeline]

## End User Installation & Configuration

### Claude Desktop
```json
{
  "mcpServers": {
    "nanobanana": {
      "command": "uvx",
      "args": ["nanobanana-mcp-server@latest"],
      "env": {
        "GEMINI_API_KEY": "your-key"
      }
    }
  }
}
```

### Claude Code (CLI)
```bash
claude mcp add nanobanana -- uvx nanobanana-mcp-server@latest
# Set env var separately or in shell profile
```

### Cursor / Continue.dev / Open WebUI
Same pattern as Claude Desktop — command-based MCP server setup with `uvx nanobanana-mcp-server@latest`.

### Direct Python
```bash
pip install nanobanana-mcp-server
export GEMINI_API_KEY=your-key
python -m nanobanana_mcp_server.server
```

## Development Server

```bash
# Recommended (with hot reload via FastMCP inspector)
./scripts/cleanup-ports.sh && fastmcp dev nanobanana_mcp_server.server:create_app

# HTTP transport
FASTMCP_TRANSPORT=http python -m nanobanana_mcp_server.server
```

## Transport Modes

| Mode | Use case | Config |
|------|---------|--------|
| `stdio` (default) | MCP client integration (Claude Desktop, etc.) | `FASTMCP_TRANSPORT=stdio` |
| `http` | Direct API access, debugging | `FASTMCP_TRANSPORT=http` |

## Authentication for End Users

See `08-configuration/README.md` for full env var reference.

**API Key** (simplest):
```bash
export GEMINI_API_KEY=your_key
```

**Vertex AI / ADC** (GCP environments):
```bash
export NANOBANANA_AUTH_METHOD=vertex_ai
export GCP_PROJECT_ID=your-project
export GCP_REGION=global  # Must be "global" for Pro model
gcloud auth application-default login
```

## Package Metadata

- **PyPI name:** `nanobanana-mcp-server`
- **Registry:** `io.github.zhongweili/nanobanana-mcp-server`
- **GitHub:** https://github.com/nano-banana/mcp-server
- **License:** MIT
