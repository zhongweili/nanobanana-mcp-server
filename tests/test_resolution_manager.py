"""Tests for ResolutionManager service."""


import pytest

from nanobanana_mcp_server.config.settings import ResolutionConfig
from nanobanana_mcp_server.core.exceptions import ValidationError
from nanobanana_mcp_server.services.model_selector import ModelTier
from nanobanana_mcp_server.services.resolution_manager import ResolutionManager


class TestResolutionManager:
    """Test suite for ResolutionManager."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ResolutionConfig(
            flash_max_resolution=2048,
            pro_max_resolution=3840,
            default_resolution="1024",
            memory_limit_mb=2048,
        )

    @pytest.fixture
    def manager(self, config):
        """Create ResolutionManager instance."""
        return ResolutionManager(config)

    def test_parse_resolution_string_preset(self, manager):
        """Test parsing string resolution presets."""
        # Test known presets
        assert manager.parse_resolution("4k") == (3840, 3840)
        assert manager.parse_resolution("2k") == (2048, 2048)
        assert manager.parse_resolution("1080p") == (1920, 1080)
        assert manager.parse_resolution("720p") == (1280, 720)

    def test_parse_resolution_string_dimensions(self, manager):
        """Test parsing dimension strings."""
        assert manager.parse_resolution("1920x1080") == (1920, 1080)
        assert manager.parse_resolution("3840x2160") == (3840, 2160)
        assert manager.parse_resolution("1024x768") == (1024, 768)

    def test_parse_resolution_dict(self, manager):
        """Test parsing dictionary resolution."""
        # Direct width/height
        assert manager.parse_resolution({"width": 1920, "height": 1080}) == (1920, 1080)

        # Aspect ratio with target size
        result = manager.parse_resolution({"aspect_ratio": "16:9", "target_size": "1080p"})
        # Should maintain 16:9 aspect ratio
        assert result[0] == 1920
        assert result[1] == 1080

    def test_parse_resolution_list(self, manager):
        """Test parsing list resolution."""
        assert manager.parse_resolution([1920, 1080]) == (1920, 1080)
        assert manager.parse_resolution([3840, 2160]) == (3840, 2160)

    def test_parse_resolution_none_default(self, manager):
        """Test that None resolution uses default."""
        result = manager.parse_resolution(None)
        assert result == (1024, 1024)  # Default is "1024"

    def test_validate_resolution_flash_model(self, manager):
        """Test resolution validation for Flash model."""
        # Within limits
        result = manager.validate_resolution("2k", ModelTier.FLASH)
        assert result == (2048, 2048)

        # Exceeds limits - should normalize
        result = manager.validate_resolution("4k", ModelTier.FLASH)
        assert result[0] <= 2048 and result[1] <= 2048

    def test_validate_resolution_pro_model(self, manager):
        """Test resolution validation for Pro model."""
        # Within limits
        result = manager.validate_resolution("4k", ModelTier.PRO)
        assert result == (3840, 3840)

        # Custom resolution within limits
        result = manager.validate_resolution({"width": 3000, "height": 2000}, ModelTier.PRO)
        assert result == (3000, 2000)

    def test_normalize_resolution(self, manager):
        """Test resolution normalization."""
        # No normalization needed
        assert manager.normalize_resolution(1920, 1080, 2048) == (1920, 1080)

        # Normalize width
        result = manager.normalize_resolution(4000, 2000, 3840)
        assert result[0] == 3840
        assert result[1] == 1920  # Maintains aspect ratio

        # Normalize height
        result = manager.normalize_resolution(2000, 4000, 3840)
        assert result[0] == 1920  # Maintains aspect ratio
        assert result[1] == 3840

    def test_estimate_memory(self, manager):
        """Test memory estimation."""
        # 1024x1024 PNG
        memory = manager.estimate_memory(1024, 1024, "png")
        expected = 1024 * 1024 * 4 * 1.5  # RGBA * overhead
        assert memory == int(expected)

        # 1920x1080 JPEG
        memory = manager.estimate_memory(1920, 1080, "jpeg")
        expected = 1920 * 1080 * 3 * 1.5  # RGB * overhead
        assert memory == int(expected)

    def test_extract_resolution_hints(self, manager):
        """Test extraction of resolution hints from prompt."""
        # Test 4K hints
        hints = manager.extract_resolution_hints("Generate a 4K ultra HD image")
        assert "4k" in hints
        assert "ultra hd" in hints

        # Test quality hints
        hints = manager.extract_resolution_hints("Create a high resolution professional photo")
        assert "high resolution" in hints
        assert "professional" in hints

        # Test custom resolution
        hints = manager.extract_resolution_hints("Make a 1920x1080 wallpaper")
        assert "custom_resolution" in hints

    def test_recommend_resolution(self, manager):
        """Test resolution recommendation."""
        # 4K request for Pro model
        result = manager.recommend_resolution("Generate a 4K image", ModelTier.PRO)
        assert result == "4k"

        # 4K request for Flash model (should downgrade)
        result = manager.recommend_resolution("Generate a 4K image", ModelTier.FLASH)
        assert result == "2k"

        # Quality request
        result = manager.recommend_resolution(
            "Create a professional high-quality photo", ModelTier.PRO
        )
        assert result == "high"

        # Default for Flash
        result = manager.recommend_resolution("Generate an image", ModelTier.FLASH)
        assert result == "1024"

    def test_format_resolution_string(self, manager):
        """Test resolution string formatting."""
        # Known resolution
        result = manager.format_resolution_string(1920, 1080)
        assert "1920x1080" in result
        assert "1080p" in result

        # 4K
        result = manager.format_resolution_string(3840, 2160)
        assert "3840x2160" in result
        assert "4K" in result

        # Custom resolution
        result = manager.format_resolution_string(1234, 567)
        assert result == "1234x567"

    def test_dynamic_presets(self, manager):
        """Test dynamic resolution presets."""
        # High preset for Pro
        result = manager._get_dynamic_preset("high", ModelTier.PRO)
        assert result == (3840, 3840)

        # High preset for Flash
        result = manager._get_dynamic_preset("high", ModelTier.FLASH)
        assert result == (2048, 2048)

        # Medium preset
        result = manager._get_dynamic_preset("medium", ModelTier.PRO)
        assert result == (1920, 1920)  # 50% of 3840

        # Low preset
        result = manager._get_dynamic_preset("low", ModelTier.FLASH)
        assert result == (512, 512)  # 25% of 2048

    def test_aspect_ratio_parsing(self, manager):
        """Test aspect ratio parsing with different formats."""
        # String ratio
        result = manager._parse_aspect_ratio_resolution(
            {"aspect_ratio": "16:9", "max_dimension": 1920}
        )
        assert result == (1920, 1080)

        # Float ratio
        result = manager._parse_aspect_ratio_resolution(
            {"aspect_ratio": 1.778, "max_dimension": 1920}
        )
        width, height = result
        assert abs(width / height - 1.778) < 0.01

        # Portrait aspect ratio
        result = manager._parse_aspect_ratio_resolution(
            {"aspect_ratio": "9:16", "max_dimension": 1920}
        )
        assert result == (1080, 1920)

    def test_memory_constraint_validation(self, manager):
        """Test memory constraint validation."""
        # Small image - should pass
        result = manager.validate_resolution("1024", ModelTier.FLASH)
        assert result == (1024, 1024)

        # Large image but within limits
        result = manager.validate_resolution("2k", ModelTier.FLASH)
        assert result == (2048, 2048)

        # Test with very limited memory
        manager.config.memory_limit_mb = 10  # Very small limit
        with pytest.raises(ValidationError) as exc_info:
            manager._validate_memory_constraints(3840, 3840)
        assert "memory usage" in str(exc_info.value).lower()

    def test_invalid_resolution_inputs(self, manager):
        """Test handling of invalid resolution inputs."""
        # Invalid preset
        with pytest.raises(ValidationError):
            manager.parse_resolution("invalid_preset")

        # Invalid dimension string
        with pytest.raises(ValidationError):
            manager.parse_resolution("not-a-resolution")

        # Invalid dictionary
        with pytest.raises(ValidationError):
            manager.parse_resolution({"invalid": "dict"})

        # Invalid list
        with pytest.raises(ValidationError):
            manager.parse_resolution([1920])  # Only one element

        # Invalid type
        with pytest.raises(ValidationError):
            manager.parse_resolution(12345)  # Integer instead of valid type

    def test_resolution_with_input_images(self, manager):
        """Test resolution recommendation with input images."""
        # High-res input images
        result = manager.recommend_resolution(
            "Edit this image", ModelTier.PRO, input_images=[(3840, 2160), (3000, 2000)]
        )
        assert result == "4k"

        # Medium-res input images
        result = manager.recommend_resolution(
            "Modify image", ModelTier.FLASH, input_images=[(1920, 1080)]
        )
        assert result == "1080p"

        # Low-res input images
        result = manager.recommend_resolution(
            "Process image", ModelTier.FLASH, input_images=[(640, 480)]
        )
        assert result == "1024"  # Default for Flash
