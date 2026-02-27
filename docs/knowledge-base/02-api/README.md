# API — MCP Tools, Resources & Prompts

This server exposes its API via the MCP protocol (STDIO or HTTP transport).

## Tools

### `generate_image` (primary tool)
File: `nanobanana_mcp_server/tools/generate_image.py`

Handles generation, editing, and multi-image conditioning in one unified tool.

**Parameters:**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `prompt` | str | Yes | — | 1–8192 chars |
| `n` | int | No | 1 | 1–4 images |
| `negative_prompt` | str | No | None | Max 1024 chars |
| `system_instruction` | str | No | None | Max 512 chars |
| `input_image_path_1/2/3` | str | No | None | Local paths for conditioning |
| `file_id` | str | No | None | Files API ID (e.g. `files/abc123`) |
| `mode` | str | No | `"auto"` | `"generate"`, `"edit"`, `"auto"` |
| `model_tier` | str | No | `"auto"` | `"flash"`, `"pro"`, `"auto"` |
| `resolution` | str | No | `"high"` | `"high"`, `"4k"`, `"2k"`, `"1k"` — 4K/2K force Pro model |
| `thinking_level` | str | No | `"high"` | `"low"`, `"high"` — Pro model selection hint only |
| `enable_grounding` | bool | No | `true` | Google Search integration (Pro model) |
| `aspect_ratio` | str | No | None | `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9` |
| `output_path` | str | No | None | File path or directory path for saving |
| `return_full_image` | bool | No | None | Full resolution vs thumbnail in response |

**Return value:** MCP content blocks — image (thumbnail or full) + text JSON metadata:
```json
{
  "model_tier": "pro",
  "resolution": "4k",
  "images_generated": 1,
  "storage_id": "abc123",
  "thinking_level": "high"
}
```

**Operation modes:**
1. **Pure generation** — prompt only, no input images
2. **Multi-image conditioning** — up to 3 local `input_image_path_*` params
3. **File ID editing** — `file_id` from previous `upload_file` call
4. **File path editing** — single `input_image_path_1` with edit `mode`

---

### `upload_file`
File: `nanobanana_mcp_server/tools/upload_file.py`

Upload a local file to Gemini Files API. Returns a `file_id` for use with `generate_image`.

---

### `output_stats`
File: `nanobanana_mcp_server/tools/output_stats.py`

Display statistics about the output directory and recently generated images.

---

### `maintenance`
File: `nanobanana_mcp_server/tools/maintenance.py`

Run maintenance operations:
- `cleanup_expired` — Remove expired Files API entries from database
- `cleanup_local` — Clean old local files by age/LRU
- `check_quota` — Check Files API storage (~20GB budget)
- `database_hygiene` — Clean up database inconsistencies
- `full_cleanup` — Run all cleanup operations

---

## Resources

| URI Pattern | File | Description |
|-------------|------|-------------|
| `gemini://files/{name}` | `resources/file_metadata.py` | File metadata from Gemini Files API |
| `nanobanana://templates/{category}` | `resources/template_catalog.py` | Prompt templates by category |
| `nanobanana://images/{id}` | `resources/stored_images.py` | Stored image and thumbnail access |
| `nanobanana://status/{op_id}` | `resources/operation_status.py` | Operation progress tracking |

---

## Prompt Templates

Organized by category in `nanobanana_mcp_server/prompts/`:

| Category | File | Templates |
|----------|------|-----------|
| Photography | `prompts/photography.py` | Photorealistic shots, professional photography, lighting/composition |
| Design | `prompts/design.py` | Logo/branding, graphic design, UI/UX |
| Editing | `prompts/editing.py` | Photo retouching, color correction, enhancement |

---

## Model Capabilities Reference

| Feature | Flash (`gemini-2.5-flash-image`) | Pro (`gemini-3-pro-image-preview`) |
|---------|----------------------------------|-----------------------------------|
| Max resolution | 1024px | 4K (3840px) |
| Speed | ~2–3s/image | ~5–8s/image |
| Google Search grounding | No | Yes |
| Thinking levels | N/A | LOW / HIGH |
| Cost | Lower | Higher |
| Best for | Iteration, drafts | Production assets |
