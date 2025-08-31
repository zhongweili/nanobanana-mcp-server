# Tools / Resources / Prompts — Design spec

Below is a concise “contract” for each component so any MCP client (Cursor, Claude Desktop, VS Code, etc.) can use the server consistently.

## Tools

### 1) `generate_image`

* **Purpose:** Create one or more images with Gemini 2.5 Flash Image (“nano banana”).
* **Params**

  * `prompt` *(str, required)* — Detailed prompt. Include subject, composition, lighting/camera, style; add an **aspect hint** (e.g., “Square image”, “16:9”) in text. ([Google AI for Developers][6])
  * `n` *(int, 1–4, default 1)* — Requested image count (model may return fewer).
  * `negative_prompt` *(str, optional)* — What to avoid.
  * `system_instruction` *(str, optional)* — Optional system tone/style.
  * `images_b64` *(list\[str], optional)* — Inline base64 input image(s) to compose / edit / style-transfer against.
  * `mime_types` *(list\[str], optional)* — MIME type per inline image.
* **Returns:**

  * **Content blocks:** a short text summary + 1..N **image blocks** (PNG).
  * **Structured JSON:** `{ requested, returned, negative_prompt_applied, used_inline_images, images:[{response_index, image_index, mime_type, synthid_watermark}] }`
* **Notes:**

  * Inline images use `Part.from_bytes`; prefer **Files API** for >20MB or reuse. ([Google AI for Developers][3])
  * The model produces interleaved text & images; we extract image `inline_data` parts. ([Google AI for Developers][6])
  * All output images carry a **SynthID** watermark. ([Google AI for Developers][5])

### 2) `edit_image`

* **Purpose:** Precise, **conversational** editing (add/remove/mask/change) while preserving original style & lighting. ([Google AI for Developers][6])
* **Params**

  * `instruction` *(str, required)* — e.g., “Add a knitted wizard hat on the cat; match the soft lighting.”
  * `base_image_b64` *(str, required)* — Base64 of the image to edit.
  * `mime_type` *(str, default `image/png`)* — MIME type of base image.
* **Returns:**

  * **Content blocks:** a short text summary + the edited image(s).
  * **Structured JSON:** `{ returned, synthid_watermark: true }`
* **Notes:**

  * The edit instruction style mirrors official templates for “Adding/removing elements”, “In-painting”, etc. ([Google AI for Developers][6])

### 3) `upload_file`

* **Purpose:** Upload a local file to Gemini **Files API** and get a reusable `uri` (better for large inputs or repeated use).
* **Params**

  * `path` *(str, required)* — Server-accessible path.
  * `display_name` *(str, optional)*
* **Returns:** `{ uri, name, mime_type, size_bytes }`
* **Notes:** Inline bytes are limited by a **20MB** request cap; Files API is recommended beyond that or for reuse. ([Google AI for Developers][3])

## Resources

### `gemini://files/{name}`

* **Purpose:** Fetch **Files API** metadata by `name` (e.g., `files/abc123`).
* **Returns:** `{ name, uri, mime_type, size_bytes }`
* **Rationale:** Gives clients a stable way to introspect file handles they plan to reuse across prompts. ([Google AI for Developers][3])

### `nano-banana://prompt-templates`

* **Purpose:** A machine-readable catalog of prompt templates (the same as the server’s `@mcp.prompt` items).
* **Returns:** A JSON dictionary listing the template names, descriptions, and parameter lists.

> FastMCP resources are simple functions; returning a dict produces JSON content per the Resources guide. ([FastMCP][7])

## Prompts (reusable templates)

> FastMCP `@mcp.prompt` returns **string messages** that clients can pass straight to tools. ([FastMCP][8])

1. **`photorealistic_shot(subject, composition, lighting, camera, aspect_hint)`**

   * Captures photo realism & camera/lighting specifics. Include an **aspect hint** (“Square image”, “16:9”) in text because Gemini infers size/aspect from text cues. ([Google AI for Developers][6])

2. **`logo_text(brand, text, font_style, style_desc, color_scheme)`**

   * Aims for **accurate text rendering** in logos; prompt fields mirror the official “text in images” guidance. ([Google AI for Developers][6])

3. **`product_shot(product, background, lighting_setup, angle, aspect_hint)`**

   * Studio product mockups with high realism; aligns with recommended product template. ([Google AI for Developers][6])

4. **`sticker_flat(character, accessory, palette)`**

   * Flat/kawaii sticker with bold lines and a **white background** (explicit in prompt to enforce cutout-friendly output). ([Google AI for Developers][6])

5. **`iterative_edit_instruction(what_to_change, how_it_should_blend)`**

   * Short instruction phrasing for **conversational editing** that preserves original style/lighting. ([Google AI for Developers][6])

6. **`composition_and_style_transfer(target_subject, style_reference, style_desc)`**

   * For blending or restyling with multiple inputs; pairs with `images_b64` or Files API URIs. ([Google AI for Developers][6])

---
