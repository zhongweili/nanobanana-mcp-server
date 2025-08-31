# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains design documentation and implementation details for a "nano banana" MCP server - an image generation and editing server that leverages Google's Gemini 2.5 Flash Image model through the FastMCP framework. The project is focused on creating production-ready MCP (Model Context Protocol) servers for AI-powered image operations.

## Architecture & Structure

### Core Components

**FastMCP Server Architecture**: The main server implementation follows the FastMCP framework pattern:
- Tools for image generation (`generate_image`) and editing (`edit_image`)
- Resources for file metadata access (`gemini://files/{name}`) and prompt templates
- Prompts for reusable image generation templates (photorealistic shots, logos, product shots, etc.)
- File upload capabilities through Gemini Files API

**Key Design Patterns**:
- Uses `google-genai` SDK for Gemini API integration
- Returns mixed content: text summaries + MCP image blocks
- Includes structured JSON metadata for programmatic access
- Implements SynthID watermark metadata tracking
- Base64 inline image support with MIME type handling

### Technology Stack

**Dependencies** (from `fastmcp-skeleton.md`):
```
fastmcp>=2.11.0
google-genai>=0.3.0
pillow>=10.4.0
python-dotenv>=1.0.1
```

**Key Integrations**:
- Google Gemini 2.5 Flash Image Preview model
- FastMCP framework for MCP server implementation
- Gemini Files API for large file handling (>20MB)
- SynthID watermarking system

## Development Commands

### Setup and Environment
```bash
# Create and activate virtual environment
uv venv && source .venv/bin/activate
# or: python -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export GEMINI_API_KEY=YOUR_API_KEY
```

### Running the Server
```bash
# Start MCP server (STDIO transport - default)
python server.py

# For HTTP transport (alternative)
# Modify server.py to use: mcp.run(transport="http", host="127.0.0.1", port=9000)
```

## Implementation Details

### Image Generation Flow
1. **Input Processing**: Accepts text prompts, optional negative prompts, and inline base64 images
2. **Gemini API Call**: Uses `gemini-2.5-flash-image-preview` model with structured content
3. **Response Extraction**: Extracts image bytes from `response.candidates[0].content.parts`
4. **MCP Integration**: Returns FastMCP `Image` objects that auto-convert to MCP ImageContent blocks
5. **Metadata Tracking**: Includes SynthID watermark info and generation parameters

### Key Technical Considerations

**Image Handling**:
- Inline base64 images limited to 20MB per Gemini API constraints
- Use Gemini Files API (`upload_file` tool) for larger files or reused assets
- All generated images include SynthID watermarks (tracked in metadata)

**Prompt Engineering**:
- Templates follow Google's best practices: subject + composition + action/location + style
- Aspect ratio hints embedded in prompt text ("Square image", "16:9", etc.)
- Conversational editing instructions for style-preserving modifications

**Error Handling**:
- Early validation for missing `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- Graceful handling of API response parsing
- Base64 decoding with proper exception handling

### FastMCP Integration Patterns

**Tools**: Return `ToolResult` with mixed content (text + images) and optional structured JSON
**Resources**: Simple functions returning dictionaries (auto-converted to JSON)
**Prompts**: String templates that clients can pass directly to tools

## File Organization

```
/
├── docs/
│   ├── fastmcp-skeleton.md      # Complete server implementation
│   └── mcp-server-design-01.md  # API specification and design patterns
└── [implementation files would go here]
```

The `docs/` directory contains comprehensive implementation guidance and API specifications that serve as the authoritative reference for the server architecture and capabilities.