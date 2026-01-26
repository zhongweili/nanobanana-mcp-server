# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.3] - 2026-01-26

### Added
- **aspect_ratio support for Pro model**: Pass aspect ratio parameter to Gemini API for Pro service (#10)
- **output_path support for Pro model**: Direct file saving with automatic thumbnail generation (#10)

### Fixed
- **Input validation**: Add aspect_ratio validation before API calls to prevent invalid requests
- **Error handling**: Graceful degradation when thumbnail creation fails (returns full image instead)
- **Code quality**: Fix datetime timezone awareness (DTZ005) and hashlib security parameter (S324)

### Contributors
- @paulrobello (#10)

## [0.3.2] - 2026-01-17

### Fixed
- **API compatibility**: Remove unsupported `output_mime_type` parameter from `ImageConfig` (#11)
- **Dependency version**: Bump `google-genai` requirement from `>=1.41.0` to `>=1.57.0` to ensure `image_size` parameter support (#12)
- **Test coverage**: Update test expectations after `output_mime_type` removal

### Changed
- `ImageConfig` is now only created when there are actual parameters to configure (aspect_ratio or resolution)

### Contributors
- @georgesung (#13)

## [0.3.1] - 2026-01-08

### Added
- **output_path parameter**: Control where generated images are saved (#8)
  - Exact file path mode: `/path/to/image.png`
  - Directory mode: `/path/to/dir/`
  - Default fallback: `IMAGE_OUTPUT_DIR` or `~/nanobanana-images`

### Fixed
- **Pro model routing**: Fix critical bug where Pro model requests were always routed to Flash service (#9)
- **API parameters**: Remove unsupported `thinking_level` parameter from gemini-3-pro-image-preview
- **Response modalities**: Change from `["Image"]` to `["TEXT", "IMAGE"]` for Pro model compatibility
- **Default region**: Change default GCP region to `global` for Pro model support

### Contributors
- @jgeewax
- @akshayvkt

## [0.3.0] - 2026-01-06

### Added
- **Nano Banana Pro Integration**: Support for Gemini 3 Pro Image model
  - 4K resolution support (up to 3840px)
  - Google Search grounding for factual accuracy
  - Configurable thinking levels (LOW/HIGH)
  - Media resolution control
- **Intelligent Model Selection**: Automatic routing between Flash and Pro models
  - `ModelSelector` service for smart model routing
  - Quality/speed keyword detection
  - Resolution-based selection
- **ADC Authentication**: Application Default Credentials support for Vertex AI (#6)

### Changed
- Multi-tier configuration system: `ModelSelectionConfig`, `ProImageConfig`
- `ProImageService` for dedicated Gemini 3 Pro Image operations

## [0.2.0] - 2026-01-03

### Added
- Initial production-ready release
- Gemini 2.5 Flash Image support
- FastMCP framework integration
- Image generation and editing tools
- Aspect ratio validation
- Comprehensive test coverage
- MIT License

[0.3.3]: https://github.com/zhongweili/nanobanana-mcp-server/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/zhongweili/nanobanana-mcp-server/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/zhongweili/nanobanana-mcp-server/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/zhongweili/nanobanana-mcp-server/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/zhongweili/nanobanana-mcp-server/releases/tag/v0.2.0
