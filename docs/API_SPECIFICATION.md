# Nano Banana MCP Server - API Specification

## Overview

This document defines the complete API specification for the Nano Banana MCP Server, including tools, resources, prompts, and their interfaces. The API follows the Model Context Protocol (MCP) specification and FastMCP conventions.

## Server Information

- **Name**: `nanobanana-mcp-server`
- **Version**: `1.0.0`
- **Protocol**: MCP (Model Context Protocol)
- **Framework**: FastMCP
- **Transport**: STDIO (default), HTTP (optional)

## Authentication

The server requires a valid Gemini API key configured through environment variables:

```bash
GEMINI_API_KEY=your_api_key
# or
GOOGLE_API_KEY=your_api_key
```

## Tools

### 1. generate_image

**Purpose**: Generate one or more images using Gemini 2.5 Flash Image model.

**Signature**:
```python
def generate_image(
    prompt: str,
    n: int = 1,
    negative_prompt: Optional[str] = None,
    system_instruction: Optional[str] = None,
    images_b64: Optional[list[str]] = None,
    mime_types: Optional[list[str]] = None,
    ctx: Context = None
) -> ToolResult
```

**Parameters**:

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `prompt` | `string` | Yes | 1-8192 chars | Detailed image prompt including subject, composition, lighting, style, and aspect ratio hints |
| `n` | `integer` | No | 1-4 | Number of images to generate (default: 1) |
| `negative_prompt` | `string` | No | 0-1024 chars | Things to avoid in generation |
| `system_instruction` | `string` | No | 0-512 chars | System-level style or tone guidance |
| `images_b64` | `array[string]` | No | Max 4 images | Base64-encoded input images for composition/style transfer |
| `mime_types` | `array[string]` | No | Must match images_b64 length | MIME types for input images (e.g., "image/png") |

**Response Structure**:
```typescript
interface GenerateImageResponse {
  content: [
    string,           // Summary text
    ...ImageContent[] // Generated images
  ];
  structured_content: {
    requested: number;
    returned: number;
    negative_prompt_applied: boolean;
    used_inline_images: boolean;
    images: Array<{
      response_index: number;
      image_index: number;
      mime_type: string;
      synthid_watermark: boolean;
    }>;
  };
}
```

**Example Usage**:
```json
{
  "prompt": "A photorealistic golden retriever sitting in a sunlit meadow. Professional photography, shallow depth of field, warm lighting. Square image.",
  "n": 2,
  "negative_prompt": "blurry, dark, indoor"
}
```

**Error Conditions**:
- `400`: Invalid prompt or parameters
- `401`: Missing or invalid API key
- `429`: Rate limit exceeded
- `500`: Gemini API error

### 2. edit_image

**Purpose**: Perform precise, style-preserving edits on an image using conversational instructions.

**Signature**:
```python
def edit_image(
    instruction: str,
    base_image_b64: str,
    mime_type: str = "image/png",
    ctx: Context = None
) -> ToolResult
```

**Parameters**:

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `instruction` | `string` | Yes | 1-1024 chars | Natural language editing instruction |
| `base_image_b64` | `string` | Yes | Valid base64 | Base64-encoded source image |
| `mime_type` | `string` | No | Valid MIME type | MIME type of source image (default: "image/png") |

**Response Structure**:
```typescript
interface EditImageResponse {
  content: [
    string,           // Edit description
    ...ImageContent[] // Edited images
  ];
  structured_content: {
    returned: number;
    synthid_watermark: boolean;
  };
}
```

**Example Usage**:
```json
{
  "instruction": "Add a red baseball cap to the person, matching the existing lighting and shadows",
  "base_image_b64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "mime_type": "image/jpeg"
}
```

### 3. upload_file

**Purpose**: Upload a local file to Gemini Files API for reuse in multiple operations.

**Signature**:
```python
def upload_file(
    path: str,
    display_name: Optional[str] = None
) -> dict
```

**Parameters**:

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `path` | `string` | Yes | Valid file path | Server-accessible file path |
| `display_name` | `string` | No | 1-128 chars | Optional display name for the file |

**Response Structure**:
```typescript
interface UploadFileResponse {
  uri: string;       // Files API URI (e.g., "gs://...")
  name: string;      // File identifier (e.g., "files/abc123")
  mime_type: string; // Detected MIME type
  size_bytes: number; // File size in bytes
}
```

**Use Cases**:
- Files larger than 20MB (inline limit)
- Images used across multiple generation requests
- Reference images for style transfer

## Resources

### 1. gemini://files/{name}

**Purpose**: Retrieve metadata for files uploaded to Gemini Files API.

**URI Pattern**: `gemini://files/{name}`

**Parameters**:
- `name`: File identifier (e.g., "files/abc123")

**Response Structure**:
```typescript
interface FileMetadataResponse {
  name: string;
  uri: string;
  mime_type: string;
  size_bytes: number;
}
```

**Example**:
```
GET gemini://files/files%2Fabc123
```

### 2. nano-banana://prompt-templates

**Purpose**: Retrieve a catalog of available prompt templates.

**URI Pattern**: `nano-banana://prompt-templates`

**Response Structure**:
```typescript
interface PromptTemplatesResponse {
  [templateName: string]: {
    description: string;
    parameters: string[];
  };
}
```

**Example Response**:
```json
{
  "photorealistic_shot": {
    "description": "High-fidelity photography template",
    "parameters": ["subject", "composition", "lighting", "camera", "aspect_hint"]
  },
  "logo_text": {
    "description": "Accurate text rendering in a clean logo",
    "parameters": ["brand", "text", "font_style", "style_desc", "color_scheme"]
  }
}
```

## Prompts

### 1. photorealistic_shot

**Purpose**: Generate prompts for high-quality photorealistic images.

**Parameters**:
```typescript
interface PhotorealisticShotParams {
  subject: string;
  composition: string;
  lighting: string;
  camera: string;
  aspect_hint: "Square image" | "Portrait" | "Landscape" | "16:9" | "4:3";
}
```

**Example**:
```json
{
  "subject": "a vintage motorcycle",
  "composition": "three-quarter view on empty road",
  "lighting": "golden hour side lighting",
  "camera": "85mm lens, f/2.8",
  "aspect_hint": "16:9"
}
```

**Generated Prompt**:
```
"A photorealistic a vintage motorcycle. Composition: three-quarter view on empty road. Lighting: golden hour side lighting. Camera: 85mm lens, f/2.8. 16:9."
```

### 2. logo_text

**Purpose**: Generate prompts for text-accurate logos.

**Parameters**:
```typescript
interface LogoTextParams {
  brand: string;
  text: string;
  font_style: string;
  style_desc: string;
  color_scheme: string;
}
```

### 3. product_shot

**Purpose**: Generate prompts for professional product photography.

**Parameters**:
```typescript
interface ProductShotParams {
  product: string;
  background: string;
  lighting_setup: string;
  angle: string;
  aspect_hint: string;
}
```

### 4. sticker_flat

**Purpose**: Generate prompts for flat, kawaii-style stickers.

**Parameters**:
```typescript
interface StickerFlatParams {
  character: string;
  accessory: string;
  palette: string;
}
```

### 5. iterative_edit_instruction

**Purpose**: Generate structured edit instructions for image modifications.

**Parameters**:
```typescript
interface IterativeEditInstructionParams {
  what_to_change: string;
  how_it_should_blend: string;
}
```

### 6. composition_and_style_transfer

**Purpose**: Generate prompts for style transfer and composition blending.

**Parameters**:
```typescript
interface CompositionAndStyleTransferParams {
  target_subject: string;
  style_reference: string;
  style_desc: string;
}
```

## Data Types

### ImageContent

```typescript
interface ImageContent {
  type: "image";
  data: string;    // Base64-encoded image data
  format: string;  // Image format (e.g., "png", "jpeg")
}
```

### ToolResult

```typescript
interface ToolResult {
  content: (string | ImageContent)[];
  structured_content?: Record<string, any>;
}
```

### Context

```typescript
interface Context {
  // MCP context object passed by the client
  // Contains client information and session data
}
```

## Error Handling

### Standard Error Responses

All errors follow this structure:
```typescript
interface ErrorResponse {
  error: {
    code: number;
    message: string;
    details?: any;
  };
}
```

### Common Error Codes

| Code | Description | Typical Causes |
|------|-------------|----------------|
| 400 | Bad Request | Invalid parameters, malformed input |
| 401 | Unauthorized | Missing or invalid API key |
| 404 | Not Found | Invalid resource URI, file not found |
| 413 | Payload Too Large | Image exceeds size limits |
| 429 | Rate Limited | Gemini API rate limit exceeded |
| 500 | Internal Error | Gemini API failures, server errors |

## Rate Limits

The server inherits rate limits from the Gemini API:

- **Image Generation**: ~60 requests/minute
- **File Uploads**: ~10 requests/minute for large files
- **Metadata Queries**: ~300 requests/minute

Actual limits may vary based on Gemini API tier and usage patterns.

## Best Practices

### Prompt Engineering

1. **Be Specific**: Include subject, composition, lighting, and style
2. **Aspect Ratios**: Use text hints like "Square image" or "16:9"
3. **Negative Prompts**: Keep concise and specific
4. **Style Consistency**: Use system instructions for consistent tone

### File Management

1. **Size Optimization**: Use Files API for >20MB or reused images
2. **Format Selection**: PNG for transparency, JPEG for photographs
3. **Metadata Tracking**: Store file identifiers for reuse

### Error Handling

1. **Retry Logic**: Implement exponential backoff for rate limits
2. **Fallback Strategies**: Have alternatives for API failures
3. **User Feedback**: Provide meaningful error messages

This API specification provides comprehensive guidance for integrating with the Nano Banana MCP Server, ensuring consistent and reliable image generation and editing capabilities.