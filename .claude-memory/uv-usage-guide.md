# UV Usage Guide for Nanobanana MCP Server

## Overview
This project uses `uv` as the modern Python package manager, replacing traditional `pip` + `requirements.txt` workflows. All dependencies are managed through `pyproject.toml` and `uv.lock`.

## Core Commands

### Project Setup
```bash
# Install dependencies and create virtual environment
uv sync

# Install development dependencies
uv sync --dev

# Install from scratch (fresh install)
uv sync --reinstall
```

### Running the Application
```bash
# Run the MCP server directly
uv run python -m nanobanana_mcp_server.server

# Run with environment variables
uv run --env GEMINI_API_KEY=your_key python -m nanobanana_mcp_server.server

# Run FastMCP development server (recommended)
fastmcp dev nanobanana_mcp_server.server:create_app
```

### Development Workflow
```bash
# Add new dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Remove dependency
uv remove package-name

# Update dependencies
uv sync --upgrade

# Run scripts/tools
uv run ruff format .
uv run ruff check .
uv run mypy .
uv run pytest
```

### Environment Management
```bash
# Activate virtual environment (optional, uv run handles this)
source .venv/bin/activate

# Check Python version
uv python --version

# Install specific Python version
uv python install 3.11
```

## Key Files

### pyproject.toml
- Contains all project metadata and dependencies
- Defines both runtime and development dependencies
- Includes tool configurations (ruff, mypy, pytest)

### uv.lock
- Lock file ensuring reproducible builds
- Auto-generated, should be committed to version control
- Contains exact versions of all dependencies and their dependencies

## Deployment Patterns

### Docker
```dockerfile
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Run application
CMD ["uv", "run", "python", "-m", "nanobanana_mcp_server.server"]
```

### Production
```bash
# Install only production dependencies
uv sync --no-dev --frozen

# Run with production settings
uv run --env LOG_LEVEL=INFO python -m nanobanana_mcp_server.server
```

## Migration Benefits

### From requirements.txt to uv
- ✅ Faster dependency resolution and installation
- ✅ Automatic virtual environment management
- ✅ Lock file for reproducible builds
- ✅ Unified project configuration in pyproject.toml
- ✅ Better dependency conflict resolution
- ✅ No separate requirements.txt files needed

### Performance Improvements
- ~10x faster dependency installation
- Parallel downloads and installs
- Smart caching and reuse
- Minimal disk space usage

## FastMCP Integration

### Configuration (fastmcp.json)
```json
{
  "mcpServers": {
    "nanobanana-mcp-server": {
      "command": "uv",
      "args": ["run", "python", "-m", "nanobanana_mcp_server.server"],
      "cwd": ".",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Development Commands
```bash
# Start development server
fastmcp dev nanobanana_mcp_server.server:create_app

# With custom ports
fastmcp dev nanobanana_mcp_server.server:create_app --ui-port 6275 --server-port 6278

# Debug mode
LOG_LEVEL=DEBUG fastmcp dev nanobanana_mcp_server.server:create_app
```

## Troubleshooting

### Common Issues
1. **Module not found**: Run `uv sync` to ensure dependencies are installed
2. **Version conflicts**: Check `uv.lock` and run `uv sync --upgrade`
3. **Virtual environment issues**: Delete `.venv/` and run `uv sync`

### Debug Commands
```bash
# Check dependency tree
uv tree

# Show installed packages
uv list

# Verify lock file integrity
uv sync --frozen

# Clean cache
uv cache clean
```

## Best Practices

### Development
1. Always use `uv sync` after pulling changes
2. Commit `uv.lock` to ensure reproducible builds
3. Use `uv run` for running scripts to ensure correct environment
4. Add new dependencies with `uv add` instead of manual pyproject.toml edits

### CI/CD
1. Use `uv sync --frozen` in CI to ensure exact dependency versions
2. Cache `.venv/` and `~/.cache/uv/` for faster builds
3. Use `--no-dev` flag for production builds

### Project Structure
```
nanobanana-mcp-server/
├── pyproject.toml      # Project config and dependencies
├── uv.lock            # Lock file (commit this)
├── .venv/             # Virtual environment (ignore in git)
└── nanobanana_mcp_server/  # Source code
```

This guide covers all essential uv usage patterns for the nanobanana-mcp-server project, from development to deployment.