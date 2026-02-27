# Tech Stack

## Language & Runtime

- **Language:** Python >=3.11
- **Package manager:** `uv` (recommended) — lock file at `uv.lock`
- **Entry points:** `fastmcp dev nanobanana_mcp_server.server:create_app` or `python -m nanobanana_mcp_server.server`

## Core Framework

- **MCP framework:** `fastmcp>=2.11.0` — Application factory pattern via `create_app()`, tool/resource/prompt registration decorators
- **Architecture:** Layered (Entry → Core → Services → Tools/Resources → Config/Utils)

## Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `google-genai` | >=1.57.0 | Gemini API client (`image_size` param requires this minimum) |
| `pillow` | >=10.4.0 | Thumbnail generation, image processing |
| `python-dotenv` | >=1.0.1 | `.env` file loading |
| `pydantic` | >=2.0.0 | Data validation, config dataclasses |

## Dev Dependencies

| Package | Purpose |
|---------|---------|
| `ruff>=0.1.0` | Linting + formatting (replaces black + isort + flake8) |
| `mypy>=1.0.0` | Static type checking |
| `pytest>=7.0.0` | Test runner |
| `pytest-asyncio>=0.21.0` | Async test support |
| `pre-commit>=3.0.0` | Git hooks |

## External Services

| Service | Purpose | Auth |
|---------|---------|------|
| Gemini Flash (`gemini-2.5-flash-image`) | Fast image generation, 1024px | API Key or Vertex AI |
| Gemini Pro (`gemini-3-pro-image-preview`) | 4K quality generation, grounding | API Key or Vertex AI |
| Gemini Files API | File upload and reuse across calls | Same credentials |
| Google Search (grounding) | Factual accuracy for Pro model | Bundled with Pro model |

## Code Quality Tools

- **Linter/formatter:** `ruff` (`ruff.toml`) — line length 100, Python 3.11 target
- **Type checker:** `mypy` — strict mode, disallow untyped defs
- **Rules enabled:** E, W, F, I, B, C4, UP, N, S, T20, SIM, ARG, DTZ, Q, TCH, RUF, McCabe max-complexity=10

## Technical Debt

- [ ] Test coverage — Only 4 test files. 80% minimum threshold may not be met; check `pytest --cov` before PRs
- [ ] Pro model is preview — `gemini-3-pro-image-preview` model ID may change when GA; monitor Google release notes
- [ ] No CI/CD pipeline — No `.github/workflows/` present; publishing is done manually via `scripts/build.py` + `scripts/upload.py`

## Tech Decisions

### 2026-01-06 — FastMCP over raw MCP SDK
- **Background:** Needed MCP server with minimal boilerplate for decorator-based tool registration
- **Choice:** `fastmcp>=2.11.0`
- **Reason:** Native `@server.tool()`, `@server.resource()`, `@server.prompt()` decorators; built-in STDIO/HTTP transport; active development

### 2026-01-06 — Dual-model architecture (Flash + Pro)
- **Background:** Users need both speed (iteration) and quality (production assets)
- **Choice:** Separate `ImageService` (Flash) and `ProImageService` (Pro) behind `ModelSelector`
- **Reason:** Clean separation, model-specific configs, intelligent auto-routing without exposing complexity
