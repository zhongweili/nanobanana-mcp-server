"""Input image paths must resolve to a supported image file."""

import pytest

from nanobanana_mcp_server.core.exceptions import ValidationError
from nanobanana_mcp_server.utils.validation_utils import validate_input_image_path


@pytest.mark.unit
@pytest.mark.parametrize("suffix", [".png", ".jpg", ".jpeg", ".webp", ".gif", ".JPG"])
def test_supported_image_file_is_accepted(tmp_path, suffix):
    image = tmp_path / f"photo{suffix}"
    image.write_bytes(b"img")

    assert validate_input_image_path(str(image), index=1) == image.resolve()


@pytest.mark.unit
def test_non_image_extension_is_rejected(tmp_path):
    secret = tmp_path / "notes.txt"
    secret.write_text("secret")

    with pytest.raises(ValidationError, match="must be an image file"):
        validate_input_image_path(str(secret), index=2)


@pytest.mark.unit
def test_symlink_to_non_image_is_rejected(tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("secret")
    link = tmp_path / "photo.png"
    link.symlink_to(secret)

    with pytest.raises(ValidationError, match="must be an image file"):
        validate_input_image_path(str(link))


@pytest.mark.unit
def test_symlink_to_image_is_accepted(tmp_path):
    real = tmp_path / "real.jpg"
    real.write_bytes(b"img")
    link = tmp_path / "alias.png"
    link.symlink_to(real)

    assert validate_input_image_path(str(link)) == real.resolve()


@pytest.mark.unit
def test_missing_file_and_directory_are_rejected(tmp_path):
    with pytest.raises(ValidationError, match="not found"):
        validate_input_image_path(str(tmp_path / "missing.png"), index=1)

    with pytest.raises(ValidationError, match="not a file"):
        validate_input_image_path(str(tmp_path), index=1)


@pytest.mark.unit
def test_generate_image_rejects_non_image_before_reading(monkeypatch, tmp_path):
    from fastmcp import FastMCP

    from nanobanana_mcp_server.config.settings import ModelTier
    from nanobanana_mcp_server.tools.generate_image import register_generate_image_tool

    secret = tmp_path / "id_rsa.txt"
    secret.write_text("secret")

    class _Selector:
        def __init__(self):
            self.called = False

        def select_model(self, *args, **kwargs):
            self.called = True
            return object(), ModelTier.NB2

        def get_model_info(self, tier):
            return {
                "tier": tier.value,
                "name": "Gemini 3.1 Flash Image",
                "model_id": "gemini-3.1-flash-image-preview",
                "emoji": "🍌",
            }

    selector = _Selector()
    monkeypatch.setattr("nanobanana_mcp_server.services.get_model_selector", lambda: selector)
    server = FastMCP("test")
    register_generate_image_tool(server)
    generate_image = next(iter(server._tool_manager._tools.values())).fn

    with pytest.raises(ValidationError, match="must be an image file"):
        generate_image(prompt="edit this", mode="edit", input_image_path_1=str(secret))

    assert selector.called is True
