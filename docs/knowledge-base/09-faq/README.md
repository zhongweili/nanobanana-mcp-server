# FAQ & Troubleshooting

## Development Issues

### Port conflict on `fastmcp dev`

**Symptom:** `EADDRINUSE` error when starting the dev server

**Fix:**
```bash
./scripts/cleanup-ports.sh && fastmcp dev nanobanana_mcp_server.server:create_app
```

Manual cleanup if script doesn't work:
```bash
pkill -f "@modelcontextprotocol/inspector"
pkill -f "fastmcp.*nanobanana_mcp_server.server"
```

---

### JSON parsing errors in Claude Desktop / MCP client

**Symptom:** MCP client shows JSON parse errors; server appears to crash

**Cause:** Something is writing to `stdout`. MCP STDIO protocol reserves `stdout` for JSON-RPC messages only.

**Fix:** Ensure all logging uses `sys.stderr`. Never use `print()` — use the logger from `utils/logging_utils.py`.

---

### Pro model requests always use Flash model

**Symptom:** Setting `model_tier="pro"` has no effect; response metadata shows `"model_tier": "flash"`

**Note:** This was a critical bug fixed in **v0.3.1**. Ensure you're on `>=0.3.1`.

---

### `thinking_level` parameter rejected by API

**Cause:** `thinking_level` is **not** a Gemini API parameter — it's internal to the `ModelSelector` for routing decisions only.

**Fix:** Do not pass `thinking_level` to `GeminiClient.generate_content()`. It's handled in `ProImageService` internally.

---

### Pro model fails with region error

**Symptom:** `404` or region-not-supported error for Pro model with Vertex AI

**Fix:** Set `GCP_REGION=global` — Pro model requires `global` region, not regional endpoints.

---

### Thumbnail creation fails silently

**Behavior (by design):** If thumbnail generation fails (e.g. Pillow error), the full image is returned instead. This is graceful degradation added in v0.3.3.

---

## API Key Issues

### Which env var to use?

Both `GEMINI_API_KEY` and `GOOGLE_API_KEY` work — they're treated identically. `GEMINI_API_KEY` is preferred for clarity.

### API key works locally but not in Claude Desktop

Ensure the key is set in Claude Desktop's MCP server `env` config, not just in your shell profile:
```json
"env": { "GEMINI_API_KEY": "your-key" }
```

---

## Image Generation Issues

### 4K images not generating

**Check:** Are you on Pro model? `resolution="4k"` requires Pro model (automatically selected when specified, but verify with `model_tier` in response metadata).

### `output_mime_type` parameter error

**Cause:** This parameter was removed from `ImageConfig` in v0.3.2 — it's not supported by the Gemini API.

**Fix:** Do NOT add `output_mime_type` back. The API doesn't accept it.

### Multi-image conditioning not working

**Check:** Provide absolute file paths in `input_image_path_1/2/3`. Relative paths may not resolve correctly depending on MCP client working directory.

---

## Vertex AI / ADC Issues

### ADC credentials not found

```bash
gcloud auth application-default login
```

For service accounts: set `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`

### Required IAM role

Your GCP service account or user needs: `roles/aiplatform.user`
