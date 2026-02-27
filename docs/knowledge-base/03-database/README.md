# Database & Storage

This project has no traditional database. Data persistence is handled via three mechanisms:

## 1. Local File Storage (`ImageStorageService`)

File: `nanobanana_mcp_server/services/image_storage_service.py`

- **Default location:** `~/nanobanana-images` (overridden by `IMAGE_OUTPUT_DIR` env var)
- **Structure:** Full-resolution images + auto-generated thumbnails
- **Naming:** Single image → `image.png`; multiple → `image.png`, `image_2.png`, `image_3.png`
- **Thumbnails:** Created by Pillow; if thumbnail creation fails, returns full image (graceful degradation — fixed in v0.3.3)

### Output Path Modes

| Input | Behavior |
|-------|---------|
| `/path/to/image.png` (file path) | Save directly to this path |
| `/path/to/dir/` (directory path) | Auto-generate filename in directory |
| `None` | Use `IMAGE_OUTPUT_DIR` or `~/nanobanana-images` |

## 2. Image Metadata Database (`ImageDatabaseService`)

File: `nanobanana_mcp_server/services/image_database_service.py`

- Local SQLite-based metadata persistence for generated images
- Stores: generation parameters, model tier, storage IDs, timestamps
- Used by `output_stats` tool and `maintenance` tool for cleanup operations

## 3. Gemini Files API (`FilesAPIService`)

File: `nanobanana_mcp_server/services/files_api_service.py`

- Remote file storage via Google's Files API (~20GB budget)
- Files uploaded via `upload_file` tool get a `file_id` (e.g. `files/abc123`)
- Files expire automatically — use `maintenance cleanup_expired` to sync local DB
- Used as input source for `generate_image` via `file_id` parameter

## Maintenance

Run via the `maintenance` MCP tool or `MaintenanceService`:

```
cleanup_expired  — Remove expired Files API entries from database
cleanup_local    — Clean old local files (age/LRU based)
check_quota      — Check Files API storage vs ~20GB budget
database_hygiene — Clean DB inconsistencies
full_cleanup     — All of the above
```

See `docs/workflows.md` for detailed maintenance workflows.
