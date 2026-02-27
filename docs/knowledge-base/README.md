# Nano Banana MCP Server — Knowledge Base

AI-powered image generation MCP server using Google Gemini models, distributed as a PyPI package.

## Navigation

| # | Section | Description |
|---|---------|-------------|
| 01 | [Tech Stack](./01-tech-stack/README.md) | Languages, frameworks, dependencies |
| 02 | [API](./02-api/README.md) | MCP tools, resources, prompt templates |
| 03 | [Database](./03-database/README.md) | Image storage, Files API, local persistence |
| 04 | [Deployment](./04-deployment/README.md) | Publishing to PyPI, client configuration |
| 05 | [Dev Standards](./05-dev-standards/README.md) | Code style, git workflow, type checking |
| 06 | [Business Logic](./06-business-logic/README.md) | Model selection, image pipeline, auth |
| 07 | [Testing](./07-testing/README.md) | Test categories, coverage requirements |
| 08 | [Configuration](./08-configuration/README.md) | Environment variables, config classes |
| 09 | [FAQ](./09-faq/README.md) | Common issues and solutions |
| 10 | [Changelog](./10-changelog/README.md) | Version history |

## Common Pitfalls

| Pitfall | Details |
|---------|---------|
| STDIO stdout pollution | All logs must go to `stderr`. Writing anything to `stdout` breaks MCP JSON-RPC communication |
| Pro model routing bug | Fixed in v0.3.1 — Pro requests were silently falling back to Flash. Always verify `model_tier` in response metadata |
| `output_mime_type` removed | Do NOT add this parameter back to `ImageConfig` — unsupported by API (removed in v0.3.2) |
| `thinking_level` API param | Not supported by `gemini-3-pro-image-preview` at API level — only used for internal model selection logic |
| GCP region for Pro model | Default region must be `global` (not `us-central1`) for Pro model support |
| Response modalities | Pro model requires `["TEXT", "IMAGE"]` not `["Image"]` |
| Port conflicts in dev | Run `./scripts/cleanup-ports.sh` before `fastmcp dev` to avoid inspector port conflicts |
| Test coverage | Current tests (4 files) may fall below the 80% threshold — check before PRs |

## Maintenance

- **Created:** 2026-02-27
- **Last updated:** 2026-02-27
- **Based on version:** v0.4.2
- **Template:** project-knowledge-base skill
