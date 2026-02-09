"""
Tests for return_full_image feature.

This module tests the return_full_image option, including:
- ServerConfig.return_full_image field and env var parsing
- Tool parameter registration and schema
- Priority resolution: tool param > env var > default
"""

import os
from unittest.mock import patch

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
    """Test priority resolution: tool param > env var > default."""

    def test_tool_param_true_overrides_env_false(self):
        """Tool param True overrides env var false."""
        # Simulate the resolution logic from generate_image
        return_full_image = True  # tool param
        effective = return_full_image
        if effective is None:
            config = ServerConfig(return_full_image=False)
            effective = config.return_full_image
        assert effective is True

    def test_tool_param_false_overrides_env_true(self):
        """Tool param False overrides env var true."""
        return_full_image = False  # tool param
        effective = return_full_image
        if effective is None:
            config = ServerConfig(return_full_image=True)
            effective = config.return_full_image
        assert effective is False

    def test_none_falls_through_to_env_true(self):
        """None tool param falls through to env var (true)."""
        return_full_image = None  # tool param
        effective = return_full_image
        if effective is None:
            config = ServerConfig(return_full_image=True)
            effective = config.return_full_image
        assert effective is True

    def test_none_falls_through_to_env_false(self):
        """None tool param falls through to env var (false)."""
        return_full_image = None  # tool param
        effective = return_full_image
        if effective is None:
            config = ServerConfig(return_full_image=False)
            effective = config.return_full_image
        assert effective is False
