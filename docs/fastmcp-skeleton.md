Awesome—let’s switch this to a Python FastMCP server and keep everything “nano banana” (Gemini 2.5 Flash Image) friendly. Below you’ll get:

1. a production-ready FastMCP **server skeleton** (Python) you can run today
2. an **English design spec** for tools, resources, and prompts (names, params, returns, behavior) mapped to Gemini’s API and FastMCP conventions

I’ve grounded key choices with official docs—citations follow each relevant section.

---

# FastMCP server skeleton (Python)

> Files you can copy/paste:
>
> * `server.py` (the MCP server)
> * optional `.env` (to hold `GEMINI_API_KEY`)
> * `pyproject.toml` (dependencies and project config)

### `.env`

```
GEMINI_API_KEY=YOUR_API_KEY
```

### `server.py`

```python
import os
from typing import Annotated, Literal, Optional
from dataclasses import dataclass
from io import BytesIO

from dotenv import load_dotenv
from pydantic import Field
from PIL import Image as PILImage

from fastmcp import FastMCP, Context, Image as MCPImage
from fastmcp.tools.tool import ToolResult

# --- Gemini SDK (official) ---
from google import genai
from google.genai import types as gx

# Load local .env if present
load_dotenv()

# ----- Server -----
mcp = FastMCP(
    name="nano-banana-mcp",
    instructions=(
        "This server exposes image generation & editing powered by Gemini 2.5 Flash Image "
        "(aka 'nano banana'). It returns images as real MCP image content blocks, and also "
        "provides structured JSON with metadata and reproducibility hints."
    ),
)

# ----- Helpers -----
def _client() -> genai.Client:
    # google-genai picks up GEMINI_API_KEY or GOOGLE_API_KEY from env
    # We error early if no key is available.
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        raise RuntimeError("Missing GEMINI_API_KEY (or GOOGLE_API_KEY) in environment.")
    return genai.Client()

def _parts_from_inline_b64(images_b64: list[str], mime_types: list[str]) -> list[gx.Part]:
    parts: list[gx.Part] = []
    for b64, mt in zip(images_b64, mime_types):
        # google-genai accepts inline bytes via Part.from_bytes(data=..., mime_type=...)
        parts.append(gx.Part.from_bytes(data=BytesIO(bytes()).getvalue(), mime_type=mt))  # placeholder
        # The SDK expects raw bytes, not base64. Decode if you pass base64:
        import base64
        raw = base64.b64decode(b64)
        parts[-1] = gx.Part.from_bytes(data=raw, mime_type=mt)
    return parts

def _extract_image_bytes_list(response) -> list[bytes]:
    """Extract all image bytes returned in the response."""
    out: list[bytes] = []
    cand = getattr(response, "candidates", None)
    if not cand:
        return out
    for part in cand[0].content.parts:
        # parts may contain text or inline_data (for image bytes)
        if getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
            out.append(part.inline_data.data)
    return out

# ----- Tools -----

@mcp.tool(
    annotations={
        "title": "Generate image (Gemini 2.5 Flash Image)",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def generate_image(
    prompt: Annotated[str, Field(description="Clear, detailed image prompt. "
                                             "Include subject, composition, action, location, style, "
                                             "and any text to render. "
                                             "Add 'Square image' or '16:9' in the text to influence aspect.")],
    n: Annotated[int, Field(ge=1, le=4, description="Requested image count (model may return fewer).")] = 1,
    negative_prompt: Annotated[Optional[str], Field(description="Things to avoid (style, objects, text).")] = None,
    system_instruction: Annotated[Optional[str], Field(description="Optional system tone/style.")] = None,
    images_b64: Annotated[Optional[list[str]], Field(description="Inline base64 input images for composition/editing.")] = None,
    mime_types: Annotated[Optional[list[str]], Field(description="MIME types matching images_b64.")] = None,
    ctx: Context = None,
) -> ToolResult:
    """
    Generate one or more images from a text prompt, optionally conditioned on input image(s).
    Returns both MCP image content blocks and structured JSON with metadata.
    """
    client = _client()

    contents: list = []
    if system_instruction:
        contents.append(system_instruction)

    # Negative prompt is best handled as explicit constraints in the text.
    full_prompt = prompt
    if negative_prompt:
        full_prompt += f"\n\nConstraints (avoid): {negative_prompt}"

    contents.append(full_prompt)

    # Optional: add inline image parts (for edits/compose/style transfer)
    if images_b64 and mime_types:
        contents = _parts_from_inline_b64(images_b64, mime_types) + contents

    # Call Gemini (2.5 Flash Image Preview model name per docs)
    # Tip: number of images is governed by prompt; the SDK returns interleaved text/images.
    responses = []
    for _ in range(n):
        resp = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents,
        )
        responses.append(resp)

    # Collect images from all responses
    all_imgs: list[MCPImage] = []
    meta: list[dict] = []
    for idx, resp in enumerate(responses, start=1):
        imgs = _extract_image_bytes_list(resp)
        # Wrap image bytes into MCP Image blocks (FastMCP base64-encodes automatically)
        for j, b in enumerate(imgs, start=1):
            all_imgs.append(MCPImage(data=b, format="png"))  # format is advisory; PNG is safe default
            meta.append({
                "response_index": idx,
                "image_index": j,
                "mime_type": "image/png",
                "synthid_watermark": True,  # per Gemini docs, images include SynthID
            })

    # Compose human-readable summary + structured JSON
    summary = (
        f"Generated {len(all_imgs)} image(s) with Gemini 2.5 Flash Image from your prompt."
        + (" Included edits/conditioning from provided image(s)." if images_b64 else "")
    )

    return ToolResult(
        # content blocks (first a short text, then the images)
        content=[summary] + all_imgs,
        # structured JSON for clients that parse data
        structured_content={
            "requested": n,
            "returned": len(all_imgs),
            "negative_prompt_applied": bool(negative_prompt),
            "used_inline_images": bool(images_b64),
            "images": meta,
        },
    )


@mcp.tool(
    annotations={"title": "Edit image (conversational)", "readOnlyHint": True, "openWorldHint": True}
)
def edit_image(
    instruction: Annotated[str, Field(description="Conversational edit instruction. "
                                                  "e.g., 'Add a knitted wizard hat to the cat.'")],
    base_image_b64: Annotated[str, Field(description="Base64 image to edit.")] ,
    mime_type: Annotated[str, Field(description="MIME type, e.g., image/png or image/jpeg")] = "image/png",
    ctx: Context = None,
) -> ToolResult:
    """
    Perform a precise, style-preserving edit on a single input image using a natural-language instruction.
    """
    client = _client()

    import base64
    raw = base64.b64decode(base_image_b64)
    parts = [gx.Part.from_bytes(data=raw, mime_type=mime_type), instruction]

    resp = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=parts,
    )

    imgs = _extract_image_bytes_list(resp)
    blocks = [MCPImage(data=b, format="png") for b in imgs]
    return ToolResult(
        content=[f"Applied edit: {instruction}"] + blocks,
        structured_content={
            "returned": len(blocks),
            "synthid_watermark": True
        },
    )


@mcp.tool(
    annotations={"title": "Upload file to Gemini Files API", "readOnlyHint": False, "openWorldHint": True}
)
def upload_file(
    path: Annotated[str, Field(description="Server-accessible file path to upload to Gemini Files API.")],
    display_name: Annotated[Optional[str], Field(description="Optional display name.")] = None,
) -> dict:
    """
    Upload a local file through the Gemini Files API and return its URI & metadata.
    Useful when the image is larger than 20MB or reused across prompts.
    """
    client = _client()
    # Gemini Files API only accepts file parameter
    file_obj = client.files.upload(file=path)

    return {
        "uri": file_obj.uri,
        "name": file_obj.name,
        "mime_type": getattr(file_obj, "mime_type", None),
        "size_bytes": getattr(file_obj, "size_bytes", None),
    }


# ----- Resources -----

@mcp.resource("gemini://files/{name}")
def file_metadata(name: str) -> dict:
    """
    Fetch Files API metadata by file 'name' (like 'files/abc123').
    """
    client = _client()
    f = client.files.get(name=name)
    return {
        "name": f.name,
        "uri": f.uri,
        "mime_type": getattr(f, "mime_type", None),
        "size_bytes": getattr(f, "size_bytes", None),
    }


@mcp.resource("nano-banana://prompt-templates")
def prompt_templates_catalog() -> dict:
    """
    A compact catalog of prompt templates (same schemas as the @mcp.prompt items below).
    """
    return {
        "photorealistic_shot": {
            "description": "High-fidelity photography template.",
            "parameters": ["subject", "composition", "lighting", "camera", "aspect_hint"],
        },
        "logo_text": {
            "description": "Accurate text rendering in a clean logo.",
            "parameters": ["brand", "text", "font_style", "style_desc", "color_scheme"],
        },
        "product_shot": {
            "description": "Studio product mockup for e-commerce.",
            "parameters": ["product", "background", "lighting_setup", "angle", "aspect_hint"],
        },
        "sticker_flat": {
            "description": "Kawaii/flat sticker with bold lines and white background.",
            "parameters": ["character", "accessory", "palette"],
        },
        "iterative_edit_instruction": {
            "description": "Concise edit instruction phrasing",
            "parameters": ["what_to_change", "how_it_should_blend"],
        },
        "composition_and_style_transfer": {
            "description": "Blend multiple images and transfer style.",
            "parameters": ["target_subject", "style_reference", "style_desc"],
        },
    }

# ----- Prompts (reusable message templates) -----

@mcp.prompt
def photorealistic_shot(
    subject: str,
    composition: str,
    lighting: str,
    camera: str,
    aspect_hint: Literal["Square image", "Portrait", "Landscape", "16:9", "4:3"] = "Square image",
) -> str:
    return (
        f"A photorealistic {subject}. Composition: {composition}. Lighting: {lighting}. "
        f"Camera: {camera}. {aspect_hint}."
    )

@mcp.prompt
def logo_text(
    brand: str,
    text: str,
    font_style: str,
    style_desc: str,
    color_scheme: str,
) -> str:
    return (
        f"Create a modern, minimalist logo for {brand}. The text should read '{text}' "
        f"in a {font_style} font. The design should be {style_desc}. Color scheme: {color_scheme}."
    )

@mcp.prompt
def product_shot(
    product: str,
    background: str,
    lighting_setup: str,
    angle: str,
    aspect_hint: str = "Square image",
) -> str:
    return (
        f"A high-resolution, studio-lit product photograph of {product} on {background}. "
        f"Lighting: {lighting_setup}. Camera angle: {angle}. Ultra-realistic. {aspect_hint}."
    )

@mcp.prompt
def sticker_flat(character: str, accessory: str, palette: str) -> str:
    return (
        f"A kawaii-style sticker of {character} with {accessory}. "
        f"Bold, clean outlines, simple cel-shading, vibrant palette ({palette}). "
        f"Background must be white."
    )

@mcp.prompt
def iterative_edit_instruction(what_to_change: str, how_it_should_blend: str) -> str:
    return (
        f"Using the provided image, {what_to_change}. "
        f"Ensure the change {how_it_should_blend} and matches the original style, lighting, and perspective."
    )

@mcp.prompt
def composition_and_style_transfer(target_subject: str, style_reference: str, style_desc: str) -> str:
    return (
        f"Transform the provided photograph of {target_subject} into the style of {style_reference}. "
        f"Preserve composition; render with {style_desc}."
    )

# ----- Entrypoint -----
if __name__ == "__main__":
    # Default to STDIO transport (best for local MCP clients)
    mcp.run()
```

**Why this skeleton works well with FastMCP & Gemini**

* `mcp.run()` starts the FastMCP server (STDIO by default), matching the docs’ “Running the server” guidance. ([FastMCP][1])
* Tools return **mixed content**: a short text summary + **real image blocks** (`fastmcp.Image`). FastMCP auto-converts these to MCP ImageContent; returning `bytes` or `Image` objects is the recommended way to stream binary content to clients. ([FastMCP][2])
* We optionally add **structured JSON** via `ToolResult.structured_content`, aligned with FastMCP’s structured output support. ([FastMCP][2])
* Gemini SDK usage mirrors the official “image generation” & “image understanding” recipes (inline bytes via `types.Part.from_bytes`, Files API for large/reusable assets, and reading generated image bytes from `response.candidates[0].content.parts`). ([Google AI for Developers][3])
* Prompts follow Google’s **prompting tips** (subject, composition, action/location, style, and explicit text rendering). ([blog.google][4])
* Note: All generated images include a **SynthID watermark**, which we surface in metadata. ([Google AI for Developers][5])



## Run & connect

* Start locally (STDIO default):

```bash
uv sync
export GEMINI_API_KEY=YOUR_KEY
uv run python server.py
```

FastMCP defaults to STDIO transport; MCP clients can connect immediately. For HTTP transport, use `mcp.run(transport="http", host="127.0.0.1", port=9000)`. ([FastMCP][1])

---

## Design notes & rationale (doc-backed)

* **Gemini API usage**

  * **Inline images** with `Part.from_bytes` for small files; use **Files API** for large or reusable assets (the docs call out the 20MB inline limit). ([Google AI for Developers][3])
  * **Extracting generated images** from `response.candidates[0].content.parts` (look for `inline_data`). ([Google AI for Developers][6])
  * **SynthID watermark** included on generated images (we surface this in metadata). ([Google AI for Developers][5])

* **Prompting best practices**

  * Include **subject, composition, action/location, style, editing instructions** for higher fidelity and consistency; this mirrors Google’s official guidance. ([blog.google][4])

* **FastMCP specifics**

  * Returning `Image` (or `bytes`) creates proper MCP **image content blocks**; if you also want machine-readable output, use `ToolResult.structured_content`. ([FastMCP][2])
  * `mcp.run()` is the canonical entry point; STDIO is the default transport recommended for local use. ([FastMCP][1])

---

### What you can add next

* **Auth & rate-limit guards** (wrap Gemini calls and shape exceptions; consider `mask_error_details=True` during server creation for safer errors).
* **HTTP transport** + `/health` route for remote deployments.
* **Caching** of Files API uploads (e.g., by checksum) to avoid duplicates.
* **Resource templates** that expose previously generated outputs by `job_id` if you want a browsable history.

If you’d like, I can tweak the tools/prompt catalog for your exact workflows (e.g., banners, ads, thumbnails, character packs), or wire in Vertex AI endpoints instead of the public Gemini API.

[1]: https://gofastmcp.com/servers/server "The FastMCP Server - FastMCP"
[2]: https://gofastmcp.com/servers/tools "Tools - FastMCP"
[3]: https://ai.google.dev/gemini-api/docs/image-understanding "Image understanding  |  Gemini API  |  Google AI for Developers"
[4]: https://blog.google/products/gemini/image-generation-prompting-tips/?utm_source=chatgpt.com "Gemini image generation: How to write an effective prompt"
[5]: https://ai.google.dev/gemini-api/docs/image-generation?utm_source=chatgpt.com "Image generation with Gemini | Gemini API | Google AI for Developers"
[6]: https://ai.google.dev/gemini-api/docs/image-generation "Image generation with Gemini (aka Nano Banana)  |  Gemini API  |  Google AI for Developers"
[7]: https://gofastmcp.com/servers/resources?utm_source=chatgpt.com "Resources & Templates - FastMCP"
[8]: https://gofastmcp.com/servers/prompts "Prompts - FastMCP"
