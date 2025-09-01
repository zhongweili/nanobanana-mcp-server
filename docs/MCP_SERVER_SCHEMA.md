# Nano Banana MCP Server - Complete Schema Documentation

## Overview

The Nano Banana MCP Server is a production-ready FastMCP server that provides AI-powered image generation and editing capabilities through Google's Gemini 2.5 Flash Image model. This document provides the complete schema specification for all MCP components.

## Server Configuration

### Server Metadata
```json
{
  "name": "nanobanana-mcp-server",
  "version": "1.0.0",
  "description": "Image generation & editing powered by Gemini 2.5 Flash Image",
  "transport": "stdio|http",
  "entry_point": "server:create_app"
}
```

### Environment Configuration
```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR
LOG_FORMAT=standard|json|detailed
FASTMCP_TRANSPORT=stdio|http
SERVER_NAME=nanobanana-mcp-server
MASK_ERROR_DETAILS=false
IMAGE_OUTPUT_DIR=output
```

---

## MCP Tools Schema

### 1. generate_image

**Purpose**: Generate new images or edit existing images using natural language instructions

**Schema**:
```typescript
interface GenerateImageTool {
  name: "generate_image";
  annotations: {
    title: "Generate or edit images (Gemini 2.5 Flash Image)";
    readOnlyHint: true;
    openWorldHint: true;
  };
  parameters: {
    prompt: {
      type: "string";
      description: "Clear, detailed image prompt. Include subject, composition, action, location, style, and any text to render. Add 'Square image' or '16:9' in the text to influence aspect ratio.";
      minLength: 1;
      maxLength: 8192;
      required: true;
    };
    n: {
      type: "integer";
      description: "Requested image count (model may return fewer).";
      minimum: 1;
      maximum: 4;
      default: 1;
    };
    negative_prompt?: {
      type: "string";
      description: "Things to avoid (style, objects, text).";
      maxLength: 1024;
    };
    system_instruction?: {
      type: "string";
      description: "Optional system tone/style guidance.";
      maxLength: 512;
    };
    input_image_path_1?: {
      type: "string";
      description: "Path to first input image for composition/conditioning";
    };
    input_image_path_2?: {
      type: "string";
      description: "Path to second input image for composition/conditioning";
    };
    input_image_path_3?: {
      type: "string";
      description: "Path to third input image for composition/conditioning";
    };
    file_id?: {
      type: "string";
      description: "Files API file ID to use as input/edit source (e.g., 'files/abc123'). If provided, this takes precedence over input_image_path_* parameters for the primary input.";
    };
    mode: {
      type: "string";
      description: "Operation mode: 'generate' for new image creation, 'edit' for modifying existing images. Auto-detected based on input parameters if not specified.";
      enum: ["auto", "generate", "edit"];
      default: "auto";
    };
  };
}
```

**Response Schema**:
```typescript
interface GenerateImageResponse {
  content: [
    {
      type: "text";
      text: string; // Summary with file paths and metadata
    },
    ...Array<{
      type: "image";
      data: string; // Base64 encoded thumbnail
      format: "jpeg";
    }>
  ];
  structured_content: {
    mode: "generate" | "edit";
    requested: number;
    returned: number;
    negative_prompt_applied: boolean;
    used_input_images: boolean;
    input_image_paths: string[];
    input_image_count: number;
    source_file_id?: string;
    edit_instruction?: string;
    generation_prompt?: string;
    output_method: "file_system_with_files_api";
    workflow: string;
    images: Array<{
      type: "generation" | "edit";
      database_id: number;
      full_path: string;
      thumb_path: string;
      width: number;
      height: number;
      size_bytes: number;
      files_api?: {
        name: string;
        uri: string;
      };
      parent_file_id?: string;
    }>;
    file_paths: string[];
    files_api_ids: string[];
    parent_relationships: Array<[string, string]>;
    total_size_mb: number;
  };
}
```

### 2. upload_file

**Purpose**: Upload a local file through the Gemini Files API

**Schema**:
```typescript
interface UploadFileTool {
  name: "upload_file";
  annotations: {
    title: "Upload file to Gemini Files API";
    readOnlyHint: false;
    openWorldHint: true;
  };
  parameters: {
    path: {
      type: "string";
      description: "Server-accessible file path to upload to Gemini Files API.";
      minLength: 1;
      maxLength: 512;
      required: true;
    };
    display_name?: {
      type: "string";
      description: "Optional display name for the uploaded file.";
      maxLength: 256;
    };
  };
}
```

**Response Schema**:
```typescript
interface UploadFileResponse {
  content: [
    {
      type: "text";
      text: string; // Upload summary
    }
  ];
  structured_content: {
    uri: string;
    name: string; // Files API ID
    mime_type: string;
    size_bytes: number;
    display_name: string;
    original_path: string;
    expires_at: string; // ISO 8601 timestamp
    status: "active";
  };
}
```

### 3. output_stats

**Purpose**: Get statistics about generated images and Files API usage

**Schema**:
```typescript
interface OutputStatsTool {
  name: "output_stats";
  annotations: {
    title: "Get image generation and Files API statistics";
    readOnlyHint: true;
    openWorldHint: false;
  };
  parameters: {
    include_files: {
      type: "boolean";
      description: "Include detailed file information";
      default: false;
    };
  };
}
```

### 4. maintenance

**Purpose**: Perform maintenance operations on images and Files API

**Schema**:
```typescript
interface MaintenanceTool {
  name: "maintenance";
  annotations: {
    title: "Maintenance operations for images and Files API";
    readOnlyHint: false;
    openWorldHint: false;
  };
  parameters: {
    operation: {
      type: "string";
      description: "Maintenance operation to perform";
      enum: ["cleanup_expired", "sync_database", "cleanup_orphaned"];
      required: true;
    };
    dry_run: {
      type: "boolean";
      description: "Preview changes without applying them";
      default: true;
    };
  };
}
```

---

## MCP Resources Schema

### 1. File Metadata Resource

**URI Pattern**: `gemini://files/{name}`

**Purpose**: Fetch Files API metadata by file name

**Schema**:
```typescript
interface FileMetadataResource {
  uri: "gemini://files/{name}";
  name: string; // File ID like 'files/abc123'
  mimeType: "application/json";
}
```

**Response Schema**:
```typescript
interface FileMetadataResponse {
  uri: string;
  name: string;
  display_name: string;
  mime_type: string;
  size_bytes: number;
  create_time: string; // ISO 8601
  update_time: string; // ISO 8601
  expiration_time: string; // ISO 8601
  sha256_hash: string;
  state: "ACTIVE" | "FAILED" | "PROCESSING";
}
```

### 2. Template Catalog Resource

**URI Pattern**: `gemini://templates/catalog`

**Purpose**: Browse available prompt templates by category

**Schema**:
```typescript
interface TemplateCatalogResource {
  uri: "gemini://templates/catalog";
  mimeType: "application/json";
}
```

**Response Schema**:
```typescript
interface TemplateCatalogResponse {
  categories: {
    photography: {
      description: string;
      templates: Array<{
        name: string;
        description: string;
        parameters: string[];
      }>;
    };
    design: {
      description: string;
      templates: Array<{
        name: string;
        description: string;
        parameters: string[];
      }>;
    };
    editing: {
      description: string;
      templates: Array<{
        name: string;
        description: string;
        parameters: string[];
      }>;
    };
  };
  total_templates: number;
}
```

### 3. Operation Status Resources

**URI Pattern**: `gemini://operations/{operation_id}/progress`

**Purpose**: Track progress of long-running operations

**Schema**:
```typescript
interface OperationStatusResource {
  uri: "gemini://operations/{operation_id}/progress";
  operation_id: string;
  mimeType: "application/json";
}
```

### 4. Stored Images Resource

**URI Pattern**: `gemini://images/{image_id}/{type}`

**Purpose**: Access generated images and thumbnails

**Schema**:
```typescript
interface StoredImagesResource {
  uri: "gemini://images/{image_id}/{type}";
  image_id: string;
  type: "full" | "thumbnail";
  mimeType: "image/png" | "image/jpeg";
}
```

---

## MCP Prompts Schema

### Photography Prompts

#### 1. photorealistic_shot

**Schema**:
```typescript
interface PhotorealisticShotPrompt {
  name: "photorealistic_shot";
  description: "Generate a prompt for high-quality photorealistic images";
  parameters: {
    subject: {
      type: "string";
      description: "Main subject of the photograph";
      required: true;
    };
    composition: {
      type: "string";  
      description: "Composition style and framing";
      required: true;
    };
    lighting: {
      type: "string";
      description: "Lighting conditions and style";
      required: true;
    };
    camera: {
      type: "string";
      description: "Camera and lens specifications";
      required: true;
    };
    aspect_hint: {
      type: "string";
      enum: ["Square image", "Portrait", "Landscape", "16:9", "4:3"];
      default: "Square image";
    };
  };
}
```

### Design Prompts

#### 1. logo_text

**Schema**:
```typescript
interface LogoTextPrompt {
  name: "logo_text";
  description: "Generate a prompt for logo design with text";
  parameters: {
    text: string;
    style: string;
    colors: string;
    background: string;
    aspect_hint: "Square image" | "Portrait" | "Landscape" | "16:9" | "4:3";
  };
}
```

#### 2. product_shot

**Schema**:
```typescript
interface ProductShotPrompt {
  name: "product_shot";
  description: "Generate a prompt for commercial product photography";
  parameters: {
    product: string;
    background: string;
    lighting: string;
    angle: string;
    aspect_hint: "Square image" | "Portrait" | "Landscape" | "16:9" | "4:3";
  };
}
```

#### 3. sticker_flat

**Schema**:
```typescript
interface StickerFlatPrompt {
  name: "sticker_flat";
  description: "Generate a prompt for flat sticker design";
  parameters: {
    subject: string;
    style: string;
    colors: string;
    aspect_hint: "Square image" | "Portrait" | "Landscape" | "16:9" | "4:3";
  };
}
```

### Editing Prompts

#### 1. iterative_edit_instruction

**Schema**:
```typescript
interface IterativeEditPrompt {
  name: "iterative_edit_instruction";
  description: "Generate iterative editing instructions";
  parameters: {
    current_state: string;
    desired_change: string;
    intensity: "subtle" | "moderate" | "strong";
  };
}
```

#### 2. composition_and_style_transfer

**Schema**:
```typescript
interface CompositionStyleTransferPrompt {
  name: "composition_and_style_transfer";
  description: "Generate prompt for composition and style transfer";
  parameters: {
    target_composition: string;
    style_reference: string;
    blend_strength: "light" | "medium" | "heavy";
  };
}
```

---

## Server Lifecycle

### Initialization Sequence
1. **Environment Validation**: Check required API keys and configuration
2. **Service Registration**: Initialize all services with dependency injection
3. **Component Registration**: Register tools, resources, and prompts
4. **Server Ready**: FastMCP server ready to handle requests

### Request Processing
1. **Input Validation**: Validate all parameters against schema
2. **Service Execution**: Execute business logic through service layer
3. **Response Formation**: Format response according to MCP specification
4. **Error Handling**: Structured error responses with appropriate logging

### Error Response Schema
```typescript
interface ErrorResponse {
  error: "validation_error" | "file_operation_error" | "api_error" | "unexpected_error";
  message: string;
  context?: Record<string, any>;
}
```

---

## Usage Examples

### Image Generation
```json
{
  "method": "tools/call",
  "params": {
    "name": "generate_image",
    "arguments": {
      "prompt": "A serene mountain lake at sunset, photorealistic style, 16:9",
      "n": 2,
      "negative_prompt": "people, buildings, text"
    }
  }
}
```

### File Upload
```json
{
  "method": "tools/call", 
  "params": {
    "name": "upload_file",
    "arguments": {
      "path": "/path/to/reference/image.jpg",
      "display_name": "Reference Image"
    }
  }
}
```

### Prompt Template Usage
```json
{
  "method": "prompts/get",
  "params": {
    "name": "photorealistic_shot",
    "arguments": {
      "subject": "mountain landscape",
      "composition": "rule of thirds with foreground interest",
      "lighting": "golden hour with warm backlighting", 
      "camera": "full frame DSLR with wide angle lens",
      "aspect_hint": "16:9"
    }
  }
}
```

---

## Implementation Notes

- **Thread Safety**: All services are designed to be thread-safe
- **Error Recovery**: Graceful handling of API failures with fallback mechanisms
- **Resource Management**: Automatic cleanup of temporary files and expired resources
- **Performance**: Optimized for concurrent requests with intelligent caching
- **Extensibility**: Modular architecture allows for easy addition of new tools and resources

This schema documentation provides the complete specification for integrating with the Nano Banana MCP Server.