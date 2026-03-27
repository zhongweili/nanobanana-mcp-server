# Changelog (Knowledge Base)

Tracks knowledge base updates alongside code changes.

---

## 2026-03-26

### v0.4.3 — NB2 thinking + extreme aspect ratios (PR #24)

**NB2 now correctly enables thinking and exposes extreme aspect ratios**

- `NanoBanana2Config`: corrected `supports_thinking=True` (was `False`) and added `supports_extreme_aspect_ratios=True`
- `generate_image` tool: `thinking_level` is now passed to NB2 in both generation and edit code paths (was Pro-only)
- `generate_image` tool: `aspect_ratio` Literal extended with NB2 extreme ratios `4:1`, `1:4`, `8:1`, `1:8`
- Edit-path `thinking_level` guard updated from `PRO`-only to `PRO or NB2`
- `structured_content` response includes `thinking_level` for NB2 responses

**Affected docs:** `02-api`, `06-business-logic`, `08-configuration`

---

## 2026-02-27

### v0.4.2 — NB2 routing fixes (knowledge base updated)

**Nano Banana 2 (`gemini-3.1-flash-image-preview`) added as default model**

- Added `ModelTier.NB2` enum and `NanoBanana2Config(ProImageConfig)` — inherits 4K + grounding, overrides model name + timeout, enables thinking (`supports_thinking=True`) and extreme aspect ratios (`4:1`, `1:4`, `8:1`, `1:8`)
- `NB2` is now the AUTO default; PRO only selected for strong quality keywords or explicit `thinking_level="high"`
- `ModelSelector` updated: new `nb2_service` parameter, NB2 explicit routing, `_auto_select()` default changed from FLASH → NB2
- `generate_image` tool: NB2 generation and edit branches pass `thinking_level`; extreme aspect ratios added to `aspect_ratio` Literal
- Three default-parameter routing bugs fixed across v0.4.0–v0.4.2:
  - `resolution="high"` default was adding `quality_score +3` → always PRO (fixed v0.4.1)
  - `enable_grounding=True` default was adding `quality_score +2` → always PRO (fixed v0.4.1)
  - `thinking_level="high"` tool default was adding `quality_score +3` → always PRO (fixed v0.4.2)
- Resolution boost removed entirely — NB2 supports 4K natively
- MCP config updated to `uvx nanobanana-mcp-server@latest` (pinned to 0.4.2 during rollout)

**Affected docs:** `06-business-logic`, `08-configuration`

---

### Knowledge Base Initialized
- Created full knowledge base from v0.3.4 codebase
- All 10 sections generated from code analysis

---

## Code Versions (from CHANGELOG.md)

### v0.3.4 — Current
- Pro model integration refinements

### v0.3.3 — 2026-01-26
- Added aspect_ratio support for Pro model
- Added output_path support for Pro model
- Fixed: aspect_ratio validation before API calls
- Fixed: graceful degradation when thumbnail fails (returns full image)
- Fixed: datetime timezone awareness and hashlib security parameter
- Contributors: @paulrobello

### v0.3.2 — 2026-01-17
- Fixed: removed unsupported `output_mime_type` from `ImageConfig`
- Changed: `ImageConfig` only created when aspect_ratio or resolution present
- Bumped: `google-genai` requirement to `>=1.57.0` for `image_size` support
- Contributors: @georgesung

### v0.3.1 — 2026-01-08
- Added: `output_path` parameter (file path, directory path, or default)
- Fixed: **critical** Pro model routing bug — Pro requests were always falling back to Flash
- Fixed: removed unsupported `thinking_level` from gemini-3-pro-image-preview API call
- Fixed: response modalities changed to `["TEXT", "IMAGE"]` for Pro model
- Fixed: default GCP region changed to `global` for Pro model support
- Contributors: @jgeewax, @akshayvkt

### v0.3.0 — 2026-01-06
- Added: Gemini 3 Pro Image support (4K, grounding, thinking levels, media resolution)
- Added: `ModelSelector` for intelligent Flash/Pro routing
- Added: Vertex AI / ADC authentication support
- Added: `ProImageService`, `ModelSelectionConfig`, `ProImageConfig`

### v0.2.0 — 2026-01-03
- Initial production-ready release
- Gemini 2.5 Flash Image support
- FastMCP framework integration
- Image generation and editing tools
- Aspect ratio validation, test coverage, MIT License
