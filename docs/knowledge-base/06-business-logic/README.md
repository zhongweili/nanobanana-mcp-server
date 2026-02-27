# Business Logic

## Image Generation Pipeline

```
generate_image tool call
    ↓
Input validation & sanitization (core/validation.py)
    ↓
Model selection via ModelSelector (services/model_selector.py)
    ↓
┌──────────────────────────────────────────────────────────────┐
│ Flash path              │ NB2 path (default) │ Pro path      │
│ ImageService            │ ProImageService    │ ProImageService│
│ gemini-2.5-flash-image  │ gemini-3.1-flash-  │ gemini-3-pro- │
│ 1024px, square          │ image-preview      │ image-preview  │
│                         │ 4K, grounding      │ 4K, thinking   │
└──────────────────────────────────────────────────────────────┘
    ↓
GeminiClient API call (services/gemini_client.py)
    ↓
Response processing & image extraction
    ↓
Optional storage: ImageStorageService (thumbnails + full)
    ↓
Metadata generation (model_tier, resolution, storage_id)
    ↓
FastMCP Image + JSON metadata returned to client
```

## Model Selection Logic

File: `nanobanana_mcp_server/services/model_selector.py`

**Priority (highest first):**
1. Explicit `model_tier` parameter (`"flash"`, `"nb2"`, or `"pro"`)
2. Strong quality keywords in prompt (2× weight): `"professional"`, `"production"`, `"high-res"`, `"HD"` → favors Pro
3. Explicit `thinking_level="high"` (+3) → favors Pro (Pro-only feature)
4. Multiple input images → favors Pro (better context handling)
5. Speed keywords: `"quick"`, `"draft"`, `"sketch"`, `"rapid"` → favors NB2
6. `n > 2` (batch) → favors NB2 for speed
7. **Default:** NB2 (Flash speed + 4K quality)

**Algorithm:**
```python
quality_score = base_keywords + (strong_matches * 2) + (thinking_level=="high") * 3
speed_score = speed_keywords + (n > 2) * 1
selected = PRO if quality_score > speed_score else NB2
```

**Key design:** Resolution and `enable_grounding` are intentionally NOT scoring inputs — NB2 supports both 4K and grounding natively, so they no longer signal "needs Pro".

**NB2 reuses `ProImageService`** — `NanoBanana2Config` extends `ProImageConfig` with `supports_thinking=False` and model name `gemini-3.1-flash-image-preview`. `isinstance(config, ProImageConfig)` stays `True`, so `GeminiClient._filter_parameters()` works unchanged.

## Authentication Strategy

File: `nanobanana_mcp_server/config/settings.py` + `services/gemini_client.py`

**Auto-detection order (`auth_method=auto`):**
1. If `GEMINI_API_KEY` or `GOOGLE_API_KEY` present → API Key mode
2. If `GCP_PROJECT_ID` present → Vertex AI / ADC mode
3. Neither → raise `ConfigurationError` at startup

**API Key mode:** Direct Gemini Developer API calls
**Vertex AI mode:** Uses `google.auth.default()` (Application Default Credentials) — requires `gcloud auth application-default login` or service account

## Aspect Ratio Handling

Supported values: `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`

- Validated in `core/validation.py` **before** API call (fixed in v0.3.3 to prevent invalid requests)
- Passed directly to Gemini `ImageConfig`
- Works for both Flash and Pro models

## File Upload Flow

```
upload_file tool call
    ↓
FilesAPIService.upload(local_path)
    ↓
Gemini Files API → returns file_id (e.g. "files/abc123")
    ↓
ImageDatabaseService records metadata
    ↓
file_id returned to user → reuse in generate_image(file_id=...)
```

Files expire automatically on Google's side. Use `maintenance cleanup_expired` to reconcile local DB.

## Error Masking

When `FASTMCP_MASK_ERRORS=true` (production default), internal error details are replaced with user-friendly messages. Internal details still logged to stderr at ERROR level.

## Progress Tracking

`core/progress_tracker.py` provides a context manager for long-running operations (primarily Pro model generation at 5–8s). Progress state exposed via `nanobanana://status/{op_id}` resource.
