# Development Standards

## Git Workflow

**Strategy:** GitHub Flow — feature branches + PRs to `master`

```
master (main/default)
  └── feat/your-feature   ← short-lived, PR back to master
  └── fix/bug-name
```

- Branch from `master`, PR back to `master`
- Use conventional commit messages (implied by changelog format)
- Tag releases with `v{semver}` (e.g. `v0.3.4`)

## Code Style

**Tool:** `ruff` (configured in `ruff.toml`)

```bash
ruff format .    # Format
ruff check .     # Lint
```

- Line length: **100 characters**
- Python target: **3.11**
- Enabled rule sets: E, W, F, I, B, C4, UP, N, S, T20, SIM, ARG, DTZ, Q, TCH, RUF
- McCabe max complexity: **10**

## Type Checking

```bash
mypy .
```

- Strict mode: `disallow_untyped_defs = true`
- Check incomplete definitions
- Enforce return types
- No implicit optionals

## Testing

```bash
pytest                          # All tests
pytest -m unit                  # Unit tests only
pytest --cov=. --cov-report=html  # Coverage report
```

- Minimum coverage: **80%** (`fail_under = 80`)
- Test markers: `unit`, `integration`, `network`, `slow`

## Pre-commit Hooks

```bash
pre-commit install
```

Runs ruff + mypy on staged files before each commit.

## Logging Rules

**Critical:** All application output must go to `stderr`. `stdout` is reserved for MCP JSON-RPC.

```python
import sys
import logging

# Handler must write to stderr
handler = logging.StreamHandler(sys.stderr)
```

Never use `print()` — use the logger from `utils/logging_utils.py`.

## Service Layer Conventions

- New services go in `nanobanana_mcp_server/services/`
- Register in `services/__init__.py` global registry
- Provide getter function: `get_my_service() -> MyService`
- Use `initialize_services()` for singleton instantiation

## Tool Registration Pattern

```python
# tools/my_tool.py
def register_my_tool(server: FastMCP) -> None:
    @server.tool()
    def my_tool(param: str) -> list:
        ...
        return [text_content, image_content]
```

Register in `core/server.py` → `_register_tools()`.

## Error Handling

Use custom exception classes from `core/exceptions.py`:
- `ConfigurationError` — bad config at startup
- `ValidationError` — bad user input
- `ImageProcessingError` — Gemini API / image processing failure
- `AuthenticationError` — auth failure

Never surface internal details to users when `mask_error_details=True`.
