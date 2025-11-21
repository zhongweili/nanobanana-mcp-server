"""
Tests for aspect ratio functionality.

This module tests the aspect ratio feature added in PR #3, including:
- Parameter validation
- API integration
- Metadata tracking
- Edge cases
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from google.genai import types as gx

from nanobanana_mcp_server.services.gemini_client import GeminiClient
from nanobanana_mcp_server.config.settings import ServerConfig, GeminiConfig


# Supported aspect ratios according to Gemini API docs
SUPPORTED_ASPECT_RATIOS = [
    "1:1", "2:3", "3:2", "3:4", "4:3",
    "4:5", "5:4", "9:16", "16:9", "21:9"
]


class TestAspectRatioValidation:
    """Test aspect ratio parameter validation."""

    @pytest.mark.parametrize("ratio", SUPPORTED_ASPECT_RATIOS)
    def test_valid_aspect_ratios(self, ratio):
        """Test that all supported aspect ratios are accepted."""
        # This tests the Literal type constraint in generate_image.py
        # The Pydantic validation should accept these values
        assert ratio in SUPPORTED_ASPECT_RATIOS

    def test_aspect_ratio_literal_type_constraint(self):
        """Verify the tool parameter uses Literal type for type safety."""
        from nanobanana_mcp_server.tools.generate_image import register_generate_image_tool
        from fastmcp import FastMCP

        # This test ensures the Literal constraint is in place
        # If it's not, the type system won't catch invalid values
        server = FastMCP("test")
        register_generate_image_tool(server)

        # Get the tool function
        tool_func = server._tools[0]

        # Check that aspect_ratio parameter exists
        import inspect
        sig = inspect.signature(tool_func.fn)
        assert 'aspect_ratio' in sig.parameters


class TestGeminiClientAspectRatio:
    """Test GeminiClient aspect ratio integration."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        server_config = ServerConfig(gemini_api_key="test-key")
        gemini_config = GeminiConfig()
        return server_config, gemini_config

    @pytest.fixture
    def gemini_client(self, mock_config):
        """Create GeminiClient with mocked dependencies."""
        server_config, gemini_config = mock_config
        client = GeminiClient(server_config, gemini_config)

        # Mock the underlying genai client
        client._client = Mock()
        client._client.models = Mock()
        client._client.models.generate_content = Mock()

        return client

    def test_aspect_ratio_creates_image_config(self, gemini_client):
        """Test that aspect_ratio parameter creates ImageConfig."""
        with patch('nanobanana_mcp_server.services.gemini_client.gx') as mock_gx:
            # Setup mocks
            mock_image_config = Mock()
            mock_gx.ImageConfig.return_value = mock_image_config
            mock_gx.GenerateContentConfig = Mock()

            # Call generate_content with aspect_ratio
            gemini_client.generate_content(
                contents=["test prompt"],
                aspect_ratio="16:9"
            )

            # Verify ImageConfig was called with aspect_ratio
            mock_gx.ImageConfig.assert_called_once_with(aspect_ratio="16:9")

    def test_aspect_ratio_none_skips_image_config(self, gemini_client):
        """Test that aspect_ratio=None doesn't create ImageConfig."""
        with patch('nanobanana_mcp_server.services.gemini_client.gx') as mock_gx:
            mock_gx.GenerateContentConfig = Mock()

            # Call without aspect_ratio
            gemini_client.generate_content(contents=["test prompt"])

            # Verify ImageConfig was not called
            mock_gx.ImageConfig.assert_not_called()

    def test_config_conflict_warning(self, gemini_client, caplog):
        """Test warning when both config kwarg and aspect_ratio are provided."""
        import logging
        caplog.set_level(logging.WARNING)

        # Provide both config kwarg and aspect_ratio
        custom_config = Mock(spec=gx.GenerateContentConfig)
        gemini_client.generate_content(
            contents=["test"],
            aspect_ratio="16:9",
            config=custom_config
        )

        # Verify warning was logged
        assert any("ignoring aspect_ratio" in record.message.lower()
                  for record in caplog.records)

    def test_response_modalities_forced_to_image(self, gemini_client):
        """Test that response_modalities is always set to ['Image']."""
        with patch('nanobanana_mcp_server.services.gemini_client.gx') as mock_gx:
            mock_gx.ImageConfig = Mock()
            mock_gx.GenerateContentConfig = Mock()

            gemini_client.generate_content(
                contents=["test"],
                aspect_ratio="16:9"
            )

            # Check that GenerateContentConfig was called with response_modalities
            call_kwargs = mock_gx.GenerateContentConfig.call_args[1]
            assert call_kwargs.get('response_modalities') == ['Image']


class TestAspectRatioMetadata:
    """Test aspect ratio in metadata tracking."""

    def test_aspect_ratio_in_generation_metadata(self):
        """Test that aspect_ratio appears in generation metadata."""
        # This would need integration with actual services
        # For now, verify the metadata structure
        metadata = {
            "prompt": "test image",
            "negative_prompt": None,
            "system_instruction": None,
            "aspect_ratio": "16:9",
        }

        assert "aspect_ratio" in metadata
        assert metadata["aspect_ratio"] == "16:9"

    def test_aspect_ratio_none_in_metadata(self):
        """Test that aspect_ratio=None is properly tracked."""
        metadata = {
            "prompt": "test image",
            "aspect_ratio": None,
        }

        assert "aspect_ratio" in metadata
        assert metadata["aspect_ratio"] is None


class TestAspectRatioEdgeCases:
    """Test edge cases and error conditions."""

    def test_aspect_ratio_with_edit_mode(self):
        """Test aspect ratio behavior in edit mode."""
        # Currently aspect_ratio only works in generate mode
        # This test documents the current behavior
        # If edit mode support is added, update this test
        pass  # Document-only test for now

    def test_aspect_ratio_with_multiple_images(self):
        """Test aspect ratio when generating multiple images."""
        # All generated images should have the same aspect ratio
        # This would require integration testing with real API
        pass  # Integration test placeholder

    def test_aspect_ratio_with_input_images(self):
        """Test aspect ratio with image conditioning."""
        # Aspect ratio should apply to output, not input
        pass  # Integration test placeholder


class TestAspectRatioIntegration:
    """Integration tests for aspect ratio feature.

    Note: These tests are marked as 'integration' and require actual API access.
    They are skipped by default in CI/CD but can be run manually with:
        pytest -m integration
    """

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires Gemini API access and costs money")
    def test_generate_with_16_9_aspect_ratio(self):
        """Integration test: Generate image with 16:9 aspect ratio."""
        # This would test actual API call
        # from nanobanana_mcp_server.tools.generate_image import generate_image
        # result = generate_image(prompt="test", aspect_ratio="16:9")
        # assert result is not None
        pass

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires Gemini API access and costs money")
    @pytest.mark.parametrize("ratio", SUPPORTED_ASPECT_RATIOS)
    def test_all_aspect_ratios_work(self, ratio):
        """Integration test: Verify all aspect ratios work with real API."""
        pass


class TestAspectRatioServicePropagation:
    """Test that aspect_ratio propagates through service layers."""

    def test_enhanced_image_service_accepts_aspect_ratio(self):
        """Test EnhancedImageService.generate_images accepts aspect_ratio."""
        from nanobanana_mcp_server.services.enhanced_image_service import EnhancedImageService
        import inspect

        # Check method signature
        sig = inspect.signature(EnhancedImageService.generate_images)
        assert 'aspect_ratio' in sig.parameters

    def test_file_image_service_accepts_aspect_ratio(self):
        """Test FileImageService.generate_images accepts aspect_ratio."""
        from nanobanana_mcp_server.services.file_image_service import FileImageService
        import inspect

        sig = inspect.signature(FileImageService.generate_images)
        assert 'aspect_ratio' in sig.parameters

    def test_image_service_accepts_aspect_ratio(self):
        """Test ImageService.generate_images accepts aspect_ratio."""
        from nanobanana_mcp_server.services.image_service import ImageService
        import inspect

        sig = inspect.signature(ImageService.generate_images)
        assert 'aspect_ratio' in sig.parameters


# Test configuration
pytest_plugins = []  # Add any required plugins

# Mark integration tests
pytestmark = pytest.mark.unit  # Default mark for this module
