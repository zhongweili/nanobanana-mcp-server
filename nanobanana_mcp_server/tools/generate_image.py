import base64
import logging
import mimetypes
import os
from typing import Annotated, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from pydantic import Field

from ..config.constants import MAX_INPUT_IMAGES
from ..config.settings import ModelTier, ThinkingLevel
from ..core.exceptions import ValidationError


def register_generate_image_tool(server: FastMCP):
    """Register the generate_image tool with the FastMCP server."""

    @server.tool(
        annotations={
            "title": "Generate or edit images (Multi-Model: Flash & Pro)",
            "readOnlyHint": True,
            "openWorldHint": True,
        }
    )
    def generate_image(
        prompt: Annotated[
            str,
            Field(
                description="Clear, detailed image prompt. Include subject, composition, "
                "action, location, style, and any text to render. Use the aspect_ratio "
                "parameter to pin a specific canvas shape when needed.",
                min_length=1,
                max_length=8192,
            ),
        ],
        n: Annotated[
            int, Field(description="Requested image count (model may return fewer).", ge=1, le=4)
        ] = 1,
        negative_prompt: Annotated[
            str | None,
            Field(description="Things to avoid (style, objects, text).", max_length=1024),
        ] = None,
        system_instruction: Annotated[
            str | None, Field(description="Optional system tone/style guidance.", max_length=512)
        ] = None,
        input_image_path_1: Annotated[
            str | None,
            Field(description="Path to first input image for composition/conditioning"),
        ] = None,
        input_image_path_2: Annotated[
            str | None,
            Field(description="Path to second input image for composition/conditioning"),
        ] = None,
        input_image_path_3: Annotated[
            str | None,
            Field(description="Path to third input image for composition/conditioning"),
        ] = None,
        file_id: Annotated[
            str | None,
            Field(
                description="Files API file ID to use as input/edit source (e.g., 'files/abc123'). "
                "If provided, this takes precedence over input_image_path_* parameters for the primary input."
            ),
        ] = None,
        mode: Annotated[
            str,
            Field(
                description="Operation mode: 'generate' for new image creation, 'edit' for modifying existing images. "
                "Auto-detected based on input parameters if not specified."
            ),
        ] = "auto",
        model_tier: Annotated[
            str | None,
            Field(
                description="Model tier: 'flash' (speed, 1024px), 'pro' (quality, up to 4K), or 'auto' (smart selection). "
                "Default: 'auto' - automatically selects based on prompt quality/speed indicators."
            ),
        ] = "auto",
        resolution: Annotated[
            str | None,
            Field(
                description="Output resolution: 'high', '4k', '2k', '1k'. "
                "4K and 2K only available with 'pro' model. Default: 'high'."
            ),
        ] = "high",
        thinking_level: Annotated[
            str | None,
            Field(
                description="Reasoning depth for Pro model: 'low' (faster), 'high' (better quality). "
                "Only applies to Pro model. Default: 'high'."
            ),
        ] = "high",
        enable_grounding: Annotated[
            bool,
            Field(
                description="Enable Google Search grounding for factual accuracy (Pro model only). "
                "Useful for real-world subjects. Default: true."
            ),
        ] = True,
        aspect_ratio: Annotated[
            Literal["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"] | None,
            Field(
                description="Optional output aspect ratio (e.g., '16:9'). "
                "See docs for supported values: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9."
            ),
        ] = None,
        _ctx: Context = None,
    ) -> ToolResult:
        """
        Generate new images or edit existing images using natural language instructions.

        Supports multiple input modes:
        1. Pure generation: Just provide a prompt to create new images
        2. Multi-image conditioning: Provide up to 3 input images using input_image_path_1/2/3 parameters
        3. File ID editing: Edit previously uploaded images using Files API ID
        4. File path editing: Edit local images by providing single input image path

        Automatically detects mode based on parameters or can be explicitly controlled.
        Input images are read from the local filesystem to avoid massive token usage.
        Returns both MCP image content blocks and structured JSON with metadata.
        """
        logger = logging.getLogger(__name__)

        try:
            # Construct input_image_paths list from individual parameters
            input_image_paths = []
            for path in [input_image_path_1, input_image_path_2, input_image_path_3]:
                if path:
                    input_image_paths.append(path)

            # Convert empty list to None for consistency
            if not input_image_paths:
                input_image_paths = None

            logger.info(
                f"Generate image request: prompt='{prompt[:50]}...', n={n}, "
                f"paths={input_image_paths}, model_tier={model_tier}, aspect_ratio={aspect_ratio}"
            )

            # Auto-detect mode based on inputs
            detected_mode = mode
            if mode == "auto":
                if file_id or (input_image_paths and len(input_image_paths) == 1):
                    detected_mode = "edit"
                else:
                    detected_mode = "generate"

            # Parse model tier
            try:
                tier = ModelTier(model_tier) if model_tier else ModelTier.AUTO
            except ValueError:
                logger.warning(f"Invalid model_tier '{model_tier}', defaulting to AUTO")
                tier = ModelTier.AUTO

            # Validate thinking level for Pro model
            try:
                if thinking_level:
                    _ = ThinkingLevel(thinking_level)  # Just validate
            except ValueError:
                logger.warning(f"Invalid thinking_level '{thinking_level}', defaulting to HIGH")
                thinking_level = "high"

            # Get model selector to determine which model to use
            from ..services import get_model_selector
            model_selector = get_model_selector()

            # Select model based on prompt and parameters
            selected_service, selected_tier = model_selector.select_model(
                prompt=prompt,
                requested_tier=tier,
                n=n,
                resolution=resolution,
                input_images=input_image_paths,
                thinking_level=thinking_level,
                enable_grounding=enable_grounding
            )

            model_info = model_selector.get_model_info(selected_tier)
            logger.info(
                f"Selected {model_info['emoji']} {model_info['name']} "
                f"({selected_tier.value}) for this request"
            )

            # Validation
            if mode not in ["auto", "generate", "edit"]:
                raise ValidationError("Mode must be 'auto', 'generate', or 'edit'")

            if input_image_paths:
                if len(input_image_paths) > MAX_INPUT_IMAGES:
                    raise ValidationError(f"Maximum {MAX_INPUT_IMAGES} input images allowed")

                # Validate that all files exist
                for i, path in enumerate(input_image_paths):
                    if not os.path.exists(path):
                        raise ValidationError(f"Input image {i + 1} not found: {path}")
                    if not os.path.isfile(path):
                        raise ValidationError(f"Input image {i + 1} is not a file: {path}")

            # Mode-specific validation
            if detected_mode == "edit":
                if not file_id and not input_image_paths:
                    raise ValidationError("Edit mode requires either file_id or input_image_paths")
                if file_id and input_image_paths and len(input_image_paths) > 1:
                    raise ValidationError(
                        "Edit mode with file_id supports only additional input images, not multiple primary inputs"
                    )

            # Get enhanced image service (would be injected in real implementation)
            enhanced_image_service = _get_enhanced_image_service()

            # Execute based on detected mode
            if detected_mode == "edit" and file_id:
                # Edit by file_id following workflows.md sequence
                logger.info(f"Edit mode: using file_id {file_id}")
                thumbnail_images, metadata = enhanced_image_service.edit_image_by_file_id(
                    file_id=file_id, edit_prompt=prompt
                )

            elif detected_mode == "edit" and input_image_paths and len(input_image_paths) == 1:
                # Edit by file path
                logger.info(f"Edit mode: using file path {input_image_paths[0]}")
                thumbnail_images, metadata = enhanced_image_service.edit_image_by_path(
                    instruction=prompt, file_path=input_image_paths[0]
                )

            else:
                # Generation mode (with optional input images for conditioning)
                logger.info("Generate mode: creating new images")
                if aspect_ratio:
                    logger.info(f"Using aspect ratio override: {aspect_ratio}")

                # Prepare input images by reading from file paths
                input_images = None
                if input_image_paths:
                    input_images = []

                    for path in input_image_paths:
                        try:
                            # Read image file
                            with open(path, "rb") as f:
                                image_bytes = f.read()

                            # Detect MIME type
                            mime_type, _ = mimetypes.guess_type(path)
                            if not mime_type or not mime_type.startswith("image/"):
                                mime_type = "image/png"  # Fallback

                            # Convert to base64 for internal API use
                            base64_data = base64.b64encode(image_bytes).decode("utf-8")
                            input_images.append((base64_data, mime_type))

                            logger.debug(f"Loaded input image: {path} ({mime_type})")

                        except Exception as e:
                            raise ValidationError(f"Failed to load input image {path}: {e}") from e

                    logger.info(f"Loaded {len(input_images)} input images from file paths")

                # Generate images following workflows.md pattern:
                # M->G->FS->F->D (save full-res, create thumbnail, upload to Files API, track in DB)
                thumbnail_images, metadata = enhanced_image_service.generate_images(
                    prompt=prompt,
                    n=n,
                    negative_prompt=negative_prompt,
                    system_instruction=system_instruction,
                    input_images=input_images,
                    aspect_ratio=aspect_ratio,
                )

            # Create response with file paths and thumbnails
            if metadata:
                # Filter out any None entries from metadata (defensive programming)
                metadata = [m for m in metadata if m is not None and isinstance(m, dict)]

                if not metadata:
                    summary = f"❌ Failed to {detected_mode} image(s): {prompt[:50]}... No valid results returned."
                    content = [TextContent(type="text", text=summary)]
                    structured_content = {
                        "error": "no_valid_metadata",
                        "message": summary,
                        "mode": detected_mode,
                    }
                    return ToolResult(content=content, structured_content=structured_content)

                # Build summary with mode-specific information
                action_verb = "Edited" if detected_mode == "edit" else "Generated"
                model_name = model_info["name"]
                model_emoji = model_info["emoji"]
                summary_lines = [
                    f"✅ {action_verb} {len(metadata)} image(s) with {model_emoji} {model_name}.",
                    f"📊 **Model**: {selected_tier.value.upper()} tier"
                ]

                # Add Pro-specific information
                if selected_tier == ModelTier.PRO:
                    summary_lines.append(f"🧠 **Thinking Level**: {thinking_level}")
                    summary_lines.append(f"📏 **Resolution**: {resolution}")
                    if enable_grounding:
                        summary_lines.append("🔍 **Grounding**: Enabled (Google Search)")
                summary_lines.append("")  # Blank line

                # Add source information based on mode and inputs
                if detected_mode == "edit":
                    if file_id:
                        summary_lines.append(f"📎 **Edit Source**: Files API {file_id}")
                    elif input_image_paths and len(input_image_paths) == 1:
                        summary_lines.append(f"📁 **Edit Source**: {input_image_paths[0]}")
                elif input_image_paths:
                    summary_lines.append(
                        f"🖼️ Conditioned on {len(input_image_paths)} input image(s): {', '.join(input_image_paths)}"
                    )
                if aspect_ratio and detected_mode == "generate":
                    summary_lines.append(f"📐 Aspect ratio: {aspect_ratio}")

                # Add file information
                result_label = "Edited Images" if detected_mode == "edit" else "Generated Images"
                summary_lines.append(f"\n📁 **{result_label}:**")
                for i, meta in enumerate(metadata, 1):
                    if not meta or not isinstance(meta, dict):
                        summary_lines.append(f"  {i}. ❌ Invalid metadata entry")
                        continue

                    size_bytes = meta.get("size_bytes", 0)
                    size_mb = round(size_bytes / (1024 * 1024), 1) if size_bytes else 0
                    full_path = meta.get("full_path", "Unknown path")
                    width = meta.get("width", "?")
                    height = meta.get("height", "?")

                    # Add Files API and parent info for edits
                    extra_info = ""
                    if detected_mode == "edit":
                        files_api_info = meta.get("files_api") or {}
                        if files_api_info.get("name"):
                            extra_info += f" • 🌐 Files API: {files_api_info['name']}"
                        if meta.get("parent_file_id"):
                            extra_info += f" • 👨‍👩‍👧 Parent: {meta.get('parent_file_id')}"

                    summary_lines.append(
                        f"  {i}. `{full_path}`\n"
                        f"     📏 {width}x{height} • 💾 {size_mb}MB{extra_info}"
                    )

                summary_lines.append(
                    "\n🖼️ **Thumbnail previews shown below** (actual images saved to disk)"
                )
                full_summary = "\n".join(summary_lines)

                content = [TextContent(type="text", text=full_summary), *thumbnail_images]
            else:
                # Fallback if no images generated
                summary = "❌ No images were generated. Please check the logs for details."
                content = [TextContent(type="text", text=summary)]

            structured_content = {
                "mode": detected_mode,
                "model_tier": selected_tier.value,
                "model_name": model_info["name"],
                "model_id": model_info["model_id"],
                "requested_tier": model_tier,
                "auto_selected": tier == ModelTier.AUTO,
                "thinking_level": thinking_level if selected_tier == ModelTier.PRO else None,
                "resolution": resolution,
                "grounding_enabled": enable_grounding if selected_tier == ModelTier.PRO else False,
                "requested": n,
                "returned": len(thumbnail_images),
                "negative_prompt_applied": bool(negative_prompt),
                "used_input_images": bool(input_image_paths) or bool(file_id),
                "input_image_paths": input_image_paths or [],
                "input_image_count": len(input_image_paths)
                if input_image_paths
                else (1 if file_id else 0),
                "aspect_ratio": aspect_ratio,
                "source_file_id": file_id,
                "edit_instruction": prompt if detected_mode == "edit" else None,
                "generation_prompt": prompt if detected_mode == "generate" else None,
                "output_method": "file_system_with_files_api",
                "workflow": f"workflows.md_{detected_mode}_sequence",
                "images": metadata,
                "file_paths": [
                    m.get("full_path")
                    for m in metadata
                    if m and isinstance(m, dict) and m.get("full_path")
                ],
                "files_api_ids": [
                    m.get("files_api", {}).get("name")
                    for m in metadata
                    if m
                    and isinstance(m, dict)
                    and m.get("files_api", {})
                    and m.get("files_api", {}).get("name")
                ],
                "parent_relationships": [
                    (m.get("parent_file_id"), m.get("files_api", {}).get("name"))
                    for m in metadata
                    if m and isinstance(m, dict)
                ]
                if detected_mode == "edit"
                else [],
                "total_size_mb": round(
                    sum(m.get("size_bytes", 0) for m in metadata if m and isinstance(m, dict))
                    / (1024 * 1024),
                    2,
                ),
            }

            action_verb = "edited" if detected_mode == "edit" else "generated"
            logger.info(
                f"Successfully {action_verb} {len(thumbnail_images)} images in {detected_mode} mode"
            )

            return ToolResult(content=content, structured_content=structured_content)

        except ValidationError as e:
            logger.error(f"Validation error in generate_image: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in generate_image: {e}")
            raise


def _get_enhanced_image_service():
    """Get the enhanced image service instance."""
    from ..services import get_enhanced_image_service
    return get_enhanced_image_service()
