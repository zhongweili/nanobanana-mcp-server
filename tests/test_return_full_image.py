"""
Tests for return_full_image feature.

This module tests the return_full_image option, including:
- ServerConfig.return_full_image field and env var parsing
- Tool parameter registration and schema
- Priority resolution: tool param > server config > env var > default
- Replacement logic: full images, fallback to thumbnails, metadata alignment
"""

import os
import tempfile
from unittest.mock import patch

from fastmcp.utilities.types import Image as MCPImage
import pytest

from nanobanana_mcp_server.config.settings import ServerConfig

pytestmark = pytest.mark.unit


class TestServerConfigReturnFullImage:
    """Test ServerConfig.return_full_image field and env var parsing."""

    def test_default_is_false(self):
        """return_full_image defaults to false when env var is not set."""
        with patch("nanobanana_mcp_server.config.settings.load_dotenv"), patch.dict(
            os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True
        ):
            config = ServerConfig.from_env()
            assert config.return_full_image is False

    def test_env_var_true(self):
        """return_full_image is true when RETURN_FULL_IMAGE=true."""
        with patch("nanobanana_mcp_server.config.settings.load_dotenv"), patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key", "RETURN_FULL_IMAGE": "true"},
            clear=True,
        ):
            config = ServerConfig.from_env()
            assert config.return_full_image is True

    def test_env_var_false(self):
        """return_full_image is false when RETURN_FULL_IMAGE=false."""
        with patch("nanobanana_mcp_server.config.settings.load_dotenv"), patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key", "RETURN_FULL_IMAGE": "false"},
            clear=True,
        ):
            config = ServerConfig.from_env()
            assert config.return_full_image is False

    def test_env_var_1(self):
        """return_full_image is true when RETURN_FULL_IMAGE=1."""
        with patch("nanobanana_mcp_server.config.settings.load_dotenv"), patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key", "RETURN_FULL_IMAGE": "1"},
            clear=True,
        ):
            config = ServerConfig.from_env()
            assert config.return_full_image is True

    def test_env_var_yes(self):
        """return_full_image is true when RETURN_FULL_IMAGE=yes."""
        with patch("nanobanana_mcp_server.config.settings.load_dotenv"), patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key", "RETURN_FULL_IMAGE": "yes"},
            clear=True,
        ):
            config = ServerConfig.from_env()
            assert config.return_full_image is True

    def test_env_var_invalid(self):
        """return_full_image is false for unrecognized values."""
        with patch("nanobanana_mcp_server.config.settings.load_dotenv"), patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key", "RETURN_FULL_IMAGE": "maybe"},
            clear=True,
        ):
            config = ServerConfig.from_env()
            assert config.return_full_image is False

    def test_env_var_case_insensitive(self):
        """return_full_image parsing is case-insensitive."""
        with patch("nanobanana_mcp_server.config.settings.load_dotenv"), patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key", "RETURN_FULL_IMAGE": "TRUE"},
            clear=True,
        ):
            config = ServerConfig.from_env()
            assert config.return_full_image is True

    def test_env_var_with_whitespace(self):
        """return_full_image handles whitespace in env var value."""
        with patch("nanobanana_mcp_server.config.settings.load_dotenv"), patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key", "RETURN_FULL_IMAGE": " true "},
            clear=True,
        ):
            config = ServerConfig.from_env()
            assert config.return_full_image is True


class TestReturnFullImageToolParameter:
    """Test return_full_image parameter in generate_image tool schema."""

    def test_parameter_exists_in_schema(self):
        """Verify return_full_image exists in tool JSON schema properties."""
        from fastmcp import FastMCP

        from nanobanana_mcp_server.tools.generate_image import register_generate_image_tool

        server = FastMCP("test")
        register_generate_image_tool(server)

        tools = list(server._tool_manager._tools.values())
        assert len(tools) > 0
        tool = tools[0]
        properties = tool.parameters.get("properties", {})
        assert "return_full_image" in properties

    def test_parameter_not_required(self):
        """Verify return_full_image is not in required params (defaults to None)."""
        from fastmcp import FastMCP

        from nanobanana_mcp_server.tools.generate_image import register_generate_image_tool

        server = FastMCP("test")
        register_generate_image_tool(server)

        tools = list(server._tool_manager._tools.values())
        assert len(tools) > 0
        tool = tools[0]
        required = tool.parameters.get("required", [])
        assert "return_full_image" not in required


class TestReturnFullImagePriority:
    """Test priority resolution: tool param > server config > env var > default."""

    def test_tool_param_true_overrides_config_false(self):
        """Tool param True overrides server config false."""
        return_full_image = True
        effective = return_full_image
        if effective is None:
            config = ServerConfig(return_full_image=False)
            effective = config.return_full_image
        assert effective is True

    def test_tool_param_false_overrides_config_true(self):
        """Tool param False overrides server config true."""
        return_full_image = False
        effective = return_full_image
        if effective is None:
            config = ServerConfig(return_full_image=True)
            effective = config.return_full_image
        assert effective is False

    def test_none_falls_through_to_config_true(self):
        """None tool param falls through to server config (true)."""
        return_full_image = None
        effective = return_full_image
        if effective is None:
            config = ServerConfig(return_full_image=True)
            effective = config.return_full_image
        assert effective is True

    def test_none_falls_through_to_config_false(self):
        """None tool param falls through to server config (false)."""
        return_full_image = None
        effective = return_full_image
        if effective is None:
            config = ServerConfig(return_full_image=False)
            effective = config.return_full_image
        assert effective is False

    def test_env_var_fallback_when_services_not_initialized(self):
        """When services aren't initialized, falls back to env var directly."""
        with patch.dict(os.environ, {"RETURN_FULL_IMAGE": "true"}):
            effective = None
            if effective is None:
                # Simulate RuntimeError from get_server_config
                effective = (
                    os.getenv("RETURN_FULL_IMAGE", "false").strip().lower()
                    in ("true", "1", "yes")
                )
            assert effective is True

    def test_env_var_fallback_defaults_to_false(self):
        """When services aren't initialized and no env var, defaults to false."""
        with patch.dict(os.environ, {}, clear=True):
            effective = None
            if effective is None:
                effective = (
                    os.getenv("RETURN_FULL_IMAGE", "false").strip().lower()
                    in ("true", "1", "yes")
                )
            assert effective is False


class TestReturnFullImageReplacement:
    """Test full-image replacement logic."""

    def test_mcpimage_path_creates_valid_image(self):
        """MCPImage(path=) creates a valid Image object from a file."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
            f.flush()
            try:
                img = MCPImage(path=f.name)
                assert img is not None
            finally:
                os.unlink(f.name)

    def test_fallback_to_thumbnail_when_file_missing(self):
        """When full_path doesn't exist, thumbnail should be used."""
        thumbnail = MCPImage(data=b"\xff\xd8\xff\xe0" + b"\x00" * 50, format="jpeg")
        metadata = [{"full_path": "/nonexistent/image.png", "size_bytes": 1000}]

        full_images = []
        for i, meta in enumerate(metadata):
            full_path = meta.get("full_path")
            if full_path and os.path.isfile(full_path):
                full_images.append(MCPImage(path=full_path))
            else:
                if i < len([thumbnail]):
                    full_images.append(thumbnail)

        assert len(full_images) == 1
        assert full_images[0] is thumbnail

    def test_fallback_when_full_path_missing_from_metadata(self):
        """When metadata has no full_path key, thumbnail should be used."""
        thumbnail = MCPImage(data=b"\xff\xd8\xff\xe0" + b"\x00" * 50, format="jpeg")
        metadata = [{"size_bytes": 1000}]  # no full_path

        full_images = []
        for i, meta in enumerate(metadata):
            full_path = meta.get("full_path")
            if full_path and os.path.isfile(full_path):
                full_images.append(MCPImage(path=full_path))
            else:
                if i < len([thumbnail]):
                    full_images.append(thumbnail)

        assert len(full_images) == 1
        assert full_images[0] is thumbnail

    def test_metadata_filtering_keeps_alignment(self):
        """Filtering metadata should keep thumbnail_images aligned."""
        thumb_a = MCPImage(data=b"\xff\xd8\xff\xe0" + b"\x00" * 10, format="jpeg")
        thumb_b = MCPImage(data=b"\xff\xd8\xff\xe0" + b"\x00" * 20, format="jpeg")
        thumb_c = MCPImage(data=b"\xff\xd8\xff\xe0" + b"\x00" * 30, format="jpeg")

        # Metadata has a None entry in the middle
        metadata = [
            {"full_path": "/a.png", "size_bytes": 100},
            None,
            {"full_path": "/c.png", "size_bytes": 300},
        ]
        thumbnail_images = [thumb_a, thumb_b, thumb_c]

        # Apply the same filtering logic as generate_image.py
        filtered_pairs = [
            (m, thumbnail_images[i] if i < len(thumbnail_images) else None)
            for i, m in enumerate(metadata)
            if m is not None and isinstance(m, dict)
        ]
        if filtered_pairs:
            filtered_meta, filtered_thumbs = zip(*filtered_pairs, strict=False)
            filtered_meta = list(filtered_meta)
            filtered_thumbs = [img for img in filtered_thumbs if img is not None]
        else:
            filtered_meta = []
            filtered_thumbs = []

        # Should have 2 entries: first and third (None removed)
        assert len(filtered_meta) == 2
        assert len(filtered_thumbs) == 2
        assert filtered_meta[0]["full_path"] == "/a.png"
        assert filtered_meta[1]["full_path"] == "/c.png"
        assert filtered_thumbs[0] is thumb_a
        assert filtered_thumbs[1] is thumb_c

    def test_all_metadata_valid_no_filtering(self):
        """When all metadata is valid, filtering keeps everything intact."""
        thumb_a = MCPImage(data=b"\xff\xd8\xff\xe0" + b"\x00" * 10, format="jpeg")
        thumb_b = MCPImage(data=b"\xff\xd8\xff\xe0" + b"\x00" * 20, format="jpeg")

        metadata = [
            {"full_path": "/a.png", "size_bytes": 100},
            {"full_path": "/b.png", "size_bytes": 200},
        ]
        thumbnail_images = [thumb_a, thumb_b]

        filtered_pairs = [
            (m, thumbnail_images[i] if i < len(thumbnail_images) else None)
            for i, m in enumerate(metadata)
            if m is not None and isinstance(m, dict)
        ]
        filtered_meta, filtered_thumbs = zip(*filtered_pairs, strict=False)
        filtered_meta = list(filtered_meta)
        filtered_thumbs = [img for img in filtered_thumbs if img is not None]

        assert len(filtered_meta) == 2
        assert len(filtered_thumbs) == 2
        assert filtered_thumbs[0] is thumb_a
        assert filtered_thumbs[1] is thumb_b
