# Nano Banana MCP Server - Documentation Index

**Version:** 0.1.4  
**Status:** Production Ready  
**Package:** `nanobanana-mcp-server`

A production-ready Model Context Protocol (MCP) server for AI-powered image generation using Google's Gemini 2.5 Flash Image model.

## 📋 Quick Navigation

### 🚀 Getting Started
- **[README.md](../README.md)** - Installation and client configuration
- **[CLAUDE.md](../CLAUDE.md)** - Claude Code development guidance

### 📚 Core Documentation
- **[API Specification](API_SPECIFICATION.md)** - Complete API reference
- **[System Design](SYSTEM_DESIGN.md)** - Architecture and design patterns
- **[Component Design](COMPONENT_DESIGN.md)** - Detailed component documentation

### 🔧 Development
- **[Implementation Plan](IMPLEMENTATION_PLAN.md)** - Development roadmap and milestones
- **[FastMCP Skeleton](fastmcp-skeleton.md)** - FastMCP integration guide
- **[Workflows](workflows.md)** - Development workflows and processes

### 📦 Publishing
- **[Publishing Workflow](PUBLISHING_WORKFLOW.md)** - Complete publishing guide
- **[PyPI Upload Guide](PYPI_UPLOAD_GUIDE.md)** - PyPI deployment instructions

## 🏗️ Project Structure

### Package Layout
```
nanobanana_mcp_server/
├── __init__.py                 # Package entry point (v0.1.4)
├── server.py                   # Main server implementation
├── config/                     # Configuration management
│   ├── settings.py            # Server and API settings
│   └── constants.py           # Application constants
├── core/                      # Core functionality
│   ├── server.py             # FastMCP server setup
│   ├── exceptions.py         # Custom exceptions
│   ├── validation.py         # Input validation
│   └── progress_tracker.py   # Progress tracking
├── services/                  # Business logic services
│   ├── __init__.py           # Service registry
│   ├── gemini_client.py      # Gemini API wrapper
│   ├── *_image_service.py    # Image processing services
│   ├── file_service.py       # File management
│   └── maintenance_service.py # System maintenance
├── tools/                     # MCP tools implementation
│   ├── generate_image.py     # Image generation tool
│   ├── upload_file.py        # File upload tool
│   ├── output_stats.py       # Statistics tool
│   └── maintenance.py        # Maintenance tool
├── resources/                 # MCP resources
│   ├── file_metadata.py      # File metadata resource
│   ├── template_catalog.py   # Template catalog
│   └── operation_status.py   # Operation status
├── prompts/                   # Prompt templates
│   ├── photography.py        # Photography templates
│   ├── design.py            # Design templates
│   └── editing.py           # Image editing templates
└── utils/                     # Utility functions
    ├── image_utils.py        # Image processing utilities
    ├── logging_utils.py      # Logging configuration
    └── validation_utils.py   # Validation helpers
```

### Configuration Files
```
├── pyproject.toml              # Project configuration and dependencies
├── fastmcp.json               # FastMCP CLI configuration
├── ruff.toml                  # Code linting configuration
└── uv.lock                    # Dependency lock file
```

### Scripts & Tools
```
scripts/
├── build.py                   # Automated build script
└── upload.py                  # PyPI upload script
```

## 🔌 MCP Integration

### Available Tools
| Tool | Description | Status |
|------|-------------|---------|
| `generate_image` | AI image generation from prompts | ✅ Active |
| `upload_file` | File upload to Gemini Files API | ✅ Active |
| `output_stats` | Image storage statistics | ✅ Active |
| `maintenance` | System maintenance operations | ✅ Active |

### Available Resources
| Resource | URI Pattern | Description |
|----------|-------------|-------------|
| File Metadata | `gemini://files/{name}` | Gemini Files API metadata |
| Template Catalog | `nano-banana://prompt-templates` | Prompt template browser |
| Operation Status | `progress://operations/{id}` | Long-running operation progress |
| Operation List | `progress://operations/list` | In-flight operations |

Generated images are returned in the tool response; metadata may reference logical `file://images/{id}` URIs for thumbnails/full images (no dedicated MCP resource handler).

### Prompt Templates
| Template | Module | Purpose |
|----------|---------|---------|
| `photorealistic_shot` | photography.py | High-quality photography |
| `product_shot` | photography.py | E-commerce product photos |
| `logo_text` | design.py | Logo design with text |
| `sticker_flat` | design.py | Flat design illustrations |
| `iterative_edit_instruction` | editing.py | Precise image editing |
| `composition_and_style_transfer` | editing.py | Artistic style transfer |

## 🛠️ Technical Stack

### Core Dependencies
- **FastMCP** (≥2.11.0) - MCP server framework
- **Google GenAI** (≥0.3.0) - Gemini API integration
- **Pillow** (≥10.4.0) - Image processing
- **Pydantic** (≥2.0.0) - Data validation
- **Python-dotenv** (≥1.0.1) - Environment management

### Development Tools
- **uv** - Modern Python package management
- **Ruff** - Fast Python linter and formatter
- **MyPy** - Static type checking
- **Pytest** - Testing framework

### Build System
- **Hatchling** - Modern Python build backend
- **Twine** - PyPI package uploading
- **Build** - PEP 517 build frontend

## 📊 Project Metrics

### Package Information
- **Total Python Files:** 40+
- **Package Size:** ~260KB (wheel + source)
- **Supported Python:** 3.11+
- **License:** MIT
- **Development Status:** Alpha (Production Ready)

### Documentation Coverage
| Category | Files | Status |
|----------|-------|---------|
| API Documentation | 3 | ✅ Complete |
| System Design | 2 | ✅ Complete |
| User Guides | 2 | ✅ Complete |
| Development Guides | 3 | ✅ Complete |
| Publishing Guides | 2 | ✅ Complete |

## 🔍 Version History

### v0.1.4 (Latest) - Comprehensive Import Fixes
- ✅ Fixed all absolute imports to relative imports
- ✅ Restructured to proper package layout
- ✅ Added automated PyPI publishing workflow
- ✅ Streamlined README with client configurations

### v0.1.3 - Import Fixes
- ✅ Fixed service import issues
- ✅ Updated resource handlers

### v0.1.2 - Directory Fixes
- ✅ Fixed read-only filesystem issues
- ✅ Improved default directory handling

### v0.1.1 - Initial Package
- ✅ Basic MCP server functionality
- ✅ Image generation tools

## 📋 Development Status

### ✅ Completed Features
- Production-ready MCP server
- Comprehensive image generation capabilities
- File management and storage
- Template system with 6+ templates
- Error handling and logging
- PyPI package publishing
- Multi-client configuration support

### 🔄 In Progress
- Enhanced documentation
- Performance optimization
- Additional prompt templates

### 📋 Planned Features
- Image editing capabilities expansion
- Batch processing tools
- Advanced template customization
- Performance monitoring

## 🆘 Support & Resources

- **Issues:** [GitHub Issues](https://github.com/zhongweili/nanobanana-mcp-server/issues)
- **Discussions:** [GitHub Discussions](https://github.com/zhongweili/nanobanana-mcp-server/discussions)
- **Package:** [PyPI Package](https://pypi.org/project/nanobanana-mcp-server/)

---

*Last updated: December 2024 | Version 0.1.4*