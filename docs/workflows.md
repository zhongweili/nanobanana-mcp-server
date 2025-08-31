# Typical Workflows

```mermaid
sequenceDiagram
    autonumber
    participant U as User/Client
    participant L as LLM
    participant M as MCP (image.generate)
    participant G as Gemini 2.5 Flash Image
    participant FS as Local FS (OUT_DIR)
    participant F as Gemini Files API
    participant D as DB/Index

    U->>L: "Generate a product photo..."
    L->>M: tool: image.generate(prompt, opts)
    M->>G: generateContent([text prompt])
    G-->>M: inline image bytes (base64)
    M->>FS: save full-res image
    M->>FS: create 256px thumbnail (JPEG)
    M->>F: files.upload(full-res path)
    F-->>M: { name:file_id, uri:file_uri }
    M->>D: upsert {path, thumb_path, mime, w,h, file_id, file_uri, expires_at}
    M-->>L: { path, thumb_data_url, mime, w,h, files_api:{name,uri} }
    L-->>U: shows preview (using thumb) and path
```

```mermaid
sequenceDiagram
    autonumber
    participant U as User/Client
    participant L as LLM
    participant M as MCP (image.edit)
    participant F as Gemini Files API
    participant G as Gemini 2.5 Flash Image
    participant FS as Local FS (OUT_DIR)
    participant D as DB/Index

    U->>L: "Soften the background of the last image."
    L->>M: tool: image.edit({ file_id, edit_prompt })
    M->>F: files.get(file_id)
    F-->>M: { uri, mime, status: valid }
    M->>G: generateContent([{file_data:{mime, uri}}, edit_prompt])
    G-->>M: inline edited image
    M->>FS: save new full-res image + new thumbnail
    M->>F: files.upload(new image)
    F-->>M: { name:new_file_id, uri:new_file_uri }
    M->>D: upsert {path2, parent_file_id:file_id, ...}
    M-->>L: { path2, thumb_data_url2, files_api:{name:new_file_id,uri:new_file_uri}, parent_file_id }
    L-->>U: shows updated preview
```

```mermaid
flowchart TD
    A[image.edit({file_id, edit_prompt})] --> B[files.get(file_id)]
    B -->|expired or not found| C[Lookup local path by file_id in DB]
    C -->|path found| D[files.upload(path) -> new_file_id]
    C -->|path missing| E[Return error: artifact unavailable]
    D --> F[Call model with file_data{uri:new}]
    B -->|valid uri| F[Call model with file_data{uri:existing}]
    F --> G[Save new image to OUT_DIR]
    G --> H[Create thumbnail]
    H --> I[files.upload(new image) -> new_file_id2]
    I --> J[DB upsert: new record with parent_file_id]
    J --> K[Return tool result: path, thumb, files_api]
```

```mermaid
flowchart TD
    A[image.edit({path, edit_prompt})] --> B[Validate path under OUT_DIR]
    B -->|invalid| C[Return error: path outside OUT_DIR]
    B -->|valid| D{File exists?}
    D -->|no| E[Return error: not found]
    D -->|yes| F{Large file or multi-turn?}
    F -->|yes| G[files.upload(path) -> file_id, uri]
    F -->|no| H[Optional: inline upload via prompt]
    G --> I[Call model with file_data{uri}]
    H --> I[Call model with inline/streamed bytes]
    I --> J[Save edited image to OUT_DIR]
    J --> K[Make thumbnail]
    K --> L[files.upload(edited) -> new_file_id]
    L --> M[Return {path, thumb, files_api}]
```

```mermaid
flowchart TD
    subgraph Maintenance / Quota & Hygiene
    A[Scheduled task (e.g., hourly)] --> B[Scan DB for Files API expirations (~48h TTL)]
    B --> C{Expired in Files API?}
    C -->|yes| D[If needed, re-upload from local before next edit]
    C -->|no| E[No action]
    A --> F[Local LRU/age-based cleanup of OUT_DIR]
    F --> G{Keep latest + referenced by DB?}
    G -->|no| H[Delete old artifacts & thumbs]
    G -->|yes| I[Retain]
    A --> J[Check project storage budget (Files API ~20GB)]
    J --> K{Over budget soon?}
    K -->|yes| L[Delete unreferenced remote files or shorten retention]
    K -->|no| M[Do nothing]
    end
```

```mermaid
flowchart TD
    %% Optional: Failure & Retry Skeleton
    A[Call Gemini generate/edit] --> B{HTTP / quota / model error?}
    B -->|yes| C[Categorize: retryable vs non-retryable]
    C -->|retryable| D[Exponential backoff + idempotent temp file]
    C -->|non-retryable| E[Return structured error with hint]
    B -->|no| F[Proceed: save -> upload -> respond]
```
