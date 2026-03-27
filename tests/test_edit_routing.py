import os

import pytest
from fastmcp import FastMCP
from fastmcp.utilities.types import Image as MCPImage


class _FakeModelSelector:
    def __init__(self, *, selected_service, selected_tier, model_id: str, name: str):
        self._selected_service = selected_service
        self._selected_tier = selected_tier
        self._model_id = model_id
        self._name = name

    def select_model(self, *args, **kwargs):
        return self._selected_service, self._selected_tier

    def get_model_info(self, tier):
        # Tool uses this for the summary/structured response.
        return {"tier": tier.value, "name": self._name, "model_id": self._model_id, "emoji": "🧪"}


class _FakeProLikeService:
    def __init__(self):
        self.calls = []

    def generate_images(self, **kwargs):
        self.calls.append(("generate", kwargs))
        return [MCPImage(data=b"thumb", format="jpeg")], [
            {
                "full_path": os.path.join(os.getcwd(), "out.png"),
                "width": 1,
                "height": 1,
                "size_bytes": 4,
            }
        ]

    def edit_images(self, **kwargs):
        self.calls.append(("edit", kwargs))
        return [MCPImage(data=b"thumb", format="jpeg")], [
            {
                "full_path": os.path.join(os.getcwd(), "out.png"),
                "width": 1,
                "height": 1,
                "size_bytes": 4,
            }
        ]


class _FakeEnhancedImageService:
    def __init__(self):
        self.calls = []

    def edit_image_by_file_id(self, **kwargs):
        self.calls.append(("file_id", kwargs))
        return [MCPImage(data=b"thumb", format="jpeg")], [
            {
                "full_path": os.path.join(os.getcwd(), "out.png"),
                "width": 1,
                "height": 1,
                "size_bytes": 4,
            }
        ]

    def edit_image_by_path(self, **kwargs):
        self.calls.append(("path", kwargs))
        return [MCPImage(data=b"thumb", format="jpeg")], [
            {
                "full_path": os.path.join(os.getcwd(), "out.png"),
                "width": 1,
                "height": 1,
                "size_bytes": 4,
            }
        ]


class _FakeFilesAPIService:
    def __init__(self):
        self.calls = []

    def create_file_data_part(self, file_id: str):
        self.calls.append(file_id)
        return {"file_data": {"mime_type": "image/png", "uri": "https://example.test/file.png"}}


def _get_generate_image_fn():
    from nanobanana_mcp_server.tools.generate_image import register_generate_image_tool

    server = FastMCP("test")
    register_generate_image_tool(server)
    tool = list(server._tool_manager._tools.values())[0]
    return tool.fn


@pytest.mark.unit
def test_edit_mode_pro_routes_to_selected_service_for_path(monkeypatch, tmp_path):
    from nanobanana_mcp_server.config.settings import ModelTier

    gen_fn = _get_generate_image_fn()

    src = tmp_path / "src.png"
    src.write_bytes(b"not-a-real-png-but-ok-for-tool")
    out = tmp_path / "out.png"

    pro_service = _FakeProLikeService()
    enhanced = _FakeEnhancedImageService()
    model_selector = _FakeModelSelector(
        selected_service=pro_service,
        selected_tier=ModelTier.PRO,
        model_id="gemini-3-pro-image-preview",
        name="Gemini 3 Pro Image",
    )

    monkeypatch.setattr("nanobanana_mcp_server.services.get_model_selector", lambda: model_selector)
    monkeypatch.setattr(
        "nanobanana_mcp_server.tools.generate_image._get_enhanced_image_service",
        lambda: enhanced,
    )

    result = gen_fn(
        prompt="make it cooler",
        mode="edit",
        model_tier="pro",
        input_image_path_1=str(src),
        output_path=str(out),
        thinking_level="high",
    )

    assert pro_service.calls, "Expected Pro-like service to be called"
    assert enhanced.calls == []
    assert pro_service.calls[0][0] == "edit"
    assert pro_service.calls[0][1]["output_path"] == str(out)
    assert result.structured_content["model_tier"] == "pro"
    assert result.structured_content["model_id"] == "gemini-3-pro-image-preview"


@pytest.mark.unit
def test_edit_mode_nb2_routes_to_selected_service_for_file_id(monkeypatch, tmp_path):
    from nanobanana_mcp_server.config.settings import ModelTier

    gen_fn = _get_generate_image_fn()

    nb2_service = _FakeProLikeService()
    enhanced = _FakeEnhancedImageService()
    model_selector = _FakeModelSelector(
        selected_service=nb2_service,
        selected_tier=ModelTier.NB2,
        model_id="gemini-3.1-flash-image-preview",
        name="Gemini 3.1 Flash Image",
    )
    files_api = _FakeFilesAPIService()

    monkeypatch.setattr("nanobanana_mcp_server.services.get_model_selector", lambda: model_selector)
    monkeypatch.setattr("nanobanana_mcp_server.services.get_files_api_service", lambda: files_api)
    monkeypatch.setattr(
        "nanobanana_mcp_server.tools.generate_image._get_enhanced_image_service",
        lambda: enhanced,
    )

    out_dir = tmp_path / "edits"
    out_dir.mkdir()

    result = gen_fn(
        prompt="add a hat",
        mode="edit",
        model_tier="nb2",
        file_id="files/abc123",
        output_path=str(out_dir) + os.sep,
        thinking_level="high",
    )

    assert files_api.calls == ["files/abc123"]
    assert nb2_service.calls, "Expected NB2 service to be called"
    assert enhanced.calls == []
    assert nb2_service.calls[0][0] == "edit"
    assert nb2_service.calls[0][1]["file_data_part"]["file_data"]["uri"].startswith("https://")
    assert nb2_service.calls[0][1]["output_path"].startswith(str(out_dir))
    assert nb2_service.calls[0][1]["thinking_level"].value == "high"
    assert result.structured_content["model_tier"] == "nb2"
    assert result.structured_content["model_id"] == "gemini-3.1-flash-image-preview"
    assert result.structured_content["thinking_level"] == "high"


@pytest.mark.unit
def test_edit_mode_flash_routes_to_enhanced_service(monkeypatch, tmp_path):
    from nanobanana_mcp_server.config.settings import ModelTier

    gen_fn = _get_generate_image_fn()

    src = tmp_path / "src.png"
    src.write_bytes(b"x")
    out = tmp_path / "out.png"

    enhanced = _FakeEnhancedImageService()
    model_selector = _FakeModelSelector(
        selected_service=object(),  # unused
        selected_tier=ModelTier.FLASH,
        model_id="gemini-2.5-flash-image",
        name="Gemini 2.5 Flash Image",
    )

    monkeypatch.setattr("nanobanana_mcp_server.services.get_model_selector", lambda: model_selector)
    monkeypatch.setattr(
        "nanobanana_mcp_server.tools.generate_image._get_enhanced_image_service",
        lambda: enhanced,
    )

    result = gen_fn(
        prompt="brighten it",
        mode="edit",
        model_tier="flash",
        input_image_path_1=str(src),
        output_path=str(out),
    )

    assert enhanced.calls and enhanced.calls[0][0] == "path"
    assert enhanced.calls[0][1]["output_path"] == str(out)
    assert result.structured_content["model_tier"] == "flash"
    assert result.structured_content["model_id"] == "gemini-2.5-flash-image"


@pytest.mark.unit
def test_generate_mode_nb2_routes_thinking_and_extreme_aspect_ratio(monkeypatch, tmp_path):
    from nanobanana_mcp_server.config.settings import ModelTier

    gen_fn = _get_generate_image_fn()

    nb2_service = _FakeProLikeService()
    enhanced = _FakeEnhancedImageService()
    model_selector = _FakeModelSelector(
        selected_service=nb2_service,
        selected_tier=ModelTier.NB2,
        model_id="gemini-3.1-flash-image-preview",
        name="Gemini 3.1 Flash Image",
    )

    monkeypatch.setattr("nanobanana_mcp_server.services.get_model_selector", lambda: model_selector)
    monkeypatch.setattr(
        "nanobanana_mcp_server.tools.generate_image._get_enhanced_image_service",
        lambda: enhanced,
    )

    out_dir = tmp_path / "generated"
    out_dir.mkdir()

    result = gen_fn(
        prompt="make a panorama",
        mode="generate",
        model_tier="nb2",
        thinking_level="high",
        aspect_ratio="4:1",
        output_path=str(out_dir) + os.sep,
    )

    assert nb2_service.calls, "Expected NB2 service to be called"
    assert nb2_service.calls[0][0] == "generate"
    assert nb2_service.calls[0][1]["thinking_level"].value == "high"
    assert nb2_service.calls[0][1]["aspect_ratio"] == "4:1"
    assert result.structured_content["model_tier"] == "nb2"
    assert result.structured_content["thinking_level"] == "high"
    assert result.structured_content["aspect_ratio"] == "4:1"
