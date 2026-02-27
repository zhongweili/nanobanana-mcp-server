# Testing

## Running Tests

```bash
pytest                           # All tests
pytest -m unit                   # Fast unit tests only
pytest -m integration            # Service integration tests
pytest -m network                # Tests requiring live API
pytest -m slow                   # Long-running tests
pytest --cov=. --cov-report=html # Coverage report (htmlcov/)
```

## Test Categories (Markers)

Configured in `pyproject.toml` under `[tool.pytest.ini_options]`:

| Marker | Description | Run on CI? |
|--------|-------------|-----------|
| `unit` | Isolated, no I/O | Yes |
| `integration` | Service-level, mocked APIs | Yes |
| `network` | Requires live Gemini API | No (needs API key) |
| `slow` | Long-running (>5s) | No |

## Coverage Requirements

- **Minimum:** 80% (`fail_under = 80` in `pyproject.toml`)
- **Excluded:** `__init__.py`, test files, debug utilities
- **Report:** HTML at `htmlcov/index.html`

**Known gap:** Only 4 test files currently exist — coverage may be below threshold. Check before submitting PRs:
```bash
pytest --cov=. --cov-report=term-missing
```

## Current Test Files

| File | What it tests |
|------|--------------|
| `tests/test_auth.py` | API Key vs Vertex AI authentication methods |
| `tests/test_aspect_ratio.py` | Aspect ratio validation logic |
| `tests/test_output_path.py` | Output path parsing (file vs directory modes) |
| `tests/test_return_full_image.py` | Full image vs thumbnail return logic |

## Test Configuration

In `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = [
    "unit: ...",
    "integration: ...",
    "network: ...",
    "slow: ...",
]

[tool.coverage.report]
fail_under = 80
exclude_lines = [...]
```

## Testing Conventions

- Use `pytest-asyncio` for async functions — `asyncio_mode = "auto"` in config
- Mock Gemini API calls with `pytest-mock` or `unittest.mock` for unit/integration tests
- `network` tests require `GEMINI_API_KEY` in environment — gate with `pytest.mark.network`
