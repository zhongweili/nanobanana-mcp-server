"""
Tests for output_path parameter functionality.

This module tests the output_path feature, including:
- resolve_output_path utility function
- validate_output_path validation
- Parameter integration with generate_image tool
- Edge cases and error handling
"""

import os
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from nanobanana_mcp_server.utils.validation_utils import (
    resolve_output_path,
    validate_output_path,
    IMAGE_EXTENSIONS,
)
from nanobanana_mcp_server.core.exceptions import ValidationError


class TestResolveOutputPath:
    """Test resolve_output_path utility function."""

    def test_none_returns_default_directory(self):
        """None output_path uses default directory with generated filename."""
        with TemporaryDirectory() as tmpdir:
            # Resolve tmpdir to handle macOS /private/var symlink
            resolved_tmpdir = str(Path(tmpdir).resolve())
            result = resolve_output_path(None, tmpdir, "gen_123.png")
            assert result == os.path.join(resolved_tmpdir, "gen_123.png")

    def test_none_creates_default_directory_if_missing(self):
        """None output_path creates default directory if it doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "new_subdir")
            resolved_new_dir = str(Path(new_dir).resolve())
            result = resolve_output_path(None, new_dir, "gen_123.png")
            assert result == os.path.join(resolved_new_dir, "gen_123.png")
            assert Path(new_dir).exists()

    def test_file_path_with_png_extension(self):
        """File path with .png extension is used directly."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "custom", "image.png")
            result = resolve_output_path(output, "/default", "gen.png")
            assert result == str(Path(output).resolve())
            assert Path(result).parent.exists()  # Parent created

    def test_file_path_with_jpg_extension(self):
        """File path with .jpg extension is used directly."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "photo.jpg")
            result = resolve_output_path(output, "/default", "gen.png")
            assert result.endswith("photo.jpg")

    def test_file_path_with_jpeg_extension(self):
        """File path with .jpeg extension is used directly."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "photo.jpeg")
            result = resolve_output_path(output, "/default", "gen.png")
            assert result.endswith("photo.jpeg")

    def test_file_path_with_webp_extension(self):
        """File path with .webp extension is used directly."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "photo.webp")
            result = resolve_output_path(output, "/default", "gen.png")
            assert result.endswith("photo.webp")

    def test_file_path_with_gif_extension(self):
        """File path with .gif extension is used directly."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "animation.gif")
            result = resolve_output_path(output, "/default", "gen.png")
            assert result.endswith("animation.gif")

    def test_existing_directory(self):
        """Existing directory uses generated filename."""
        with TemporaryDirectory() as tmpdir:
            result = resolve_output_path(tmpdir, "/default", "gen_123.png")
            expected = str(Path(tmpdir).resolve() / "gen_123.png")
            assert result == expected

    def test_directory_with_trailing_slash(self):
        """Path ending with / is treated as directory."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "newdir") + "/"
            result = resolve_output_path(output, "/default", "gen.png")
            assert result.endswith("gen.png")
            assert "newdir" in result
            assert Path(result).parent.exists()

    def test_directory_with_os_separator(self):
        """Path ending with os.sep is treated as directory."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "newdir") + os.sep
            result = resolve_output_path(output, "/default", "gen.png")
            assert result.endswith("gen.png")
            assert Path(result).parent.exists()

    def test_ambiguous_path_no_extension(self):
        """Path without extension treated as file path."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "myimage")
            result = resolve_output_path(output, "/default", "gen.png")
            assert result.endswith("myimage")  # Used as-is

    def test_creates_parent_directories(self):
        """Parent directories are created automatically."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "deep", "nested", "path", "image.png")
            result = resolve_output_path(output, "/default", "gen.png")
            assert Path(result).parent.exists()

    def test_relative_path_resolved_to_absolute(self):
        """Relative paths are resolved to absolute."""
        result = resolve_output_path("./output/image.png", "/default", "gen.png")
        assert os.path.isabs(result)

    def test_home_directory_expansion(self):
        """Paths with ~ are expanded."""
        result = resolve_output_path("~/images/photo.png", "/default", "gen.png")
        assert "~" not in result
        assert os.path.isabs(result)

    def test_multiple_images_first_index(self):
        """First image (index 1) uses exact path."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "image.png")
            result = resolve_output_path(output, "/default", "gen.png", image_index=1)
            assert result.endswith("image.png")
            assert "_2" not in result

    def test_multiple_images_second_index(self):
        """Second image (index 2) appends _2 to filename."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "image.png")
            result = resolve_output_path(output, "/default", "gen.png", image_index=2)
            assert result.endswith("image_2.png")

    def test_multiple_images_third_index(self):
        """Third image (index 3) appends _3 to filename."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "photo.jpg")
            result = resolve_output_path(output, "/default", "gen.png", image_index=3)
            assert result.endswith("photo_3.jpg")

    def test_multiple_images_with_directory(self):
        """Multiple images with directory use default filenames (no indexing needed)."""
        with TemporaryDirectory() as tmpdir:
            # When output_path is a directory, default_filename is used as-is
            # So each call should generate unique filenames from the caller
            result1 = resolve_output_path(tmpdir, "/default", "gen_1.png", image_index=1)
            result2 = resolve_output_path(tmpdir, "/default", "gen_2.png", image_index=2)
            assert result1.endswith("gen_1.png")
            assert result2.endswith("gen_2.png")

    def test_multiple_images_no_extension_ambiguous(self):
        """Multiple images with ambiguous path appends index."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "myimage")
            result = resolve_output_path(output, "/default", "gen.png", image_index=2)
            assert result.endswith("myimage_2")


class TestValidateOutputPath:
    """Test validate_output_path validation function."""

    def test_none_is_valid(self):
        """None output_path is always valid."""
        # Should not raise
        validate_output_path(None)

    def test_valid_file_path(self):
        """Valid file path passes validation."""
        with TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "image.png")
            validate_output_path(path)

    def test_valid_directory_path(self):
        """Valid directory path passes validation."""
        with TemporaryDirectory() as tmpdir:
            validate_output_path(tmpdir)

    def test_empty_string_raises_error(self):
        """Empty string raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be an empty string"):
            validate_output_path("")

    def test_whitespace_only_raises_error(self):
        """Whitespace-only string raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be an empty string"):
            validate_output_path("   ")

    def test_system_bin_path_raises_error(self):
        """Path to /bin raises ValidationError."""
        with pytest.raises(ValidationError, match="system directory"):
            validate_output_path("/bin/image.png")

    def test_system_etc_path_raises_error(self):
        """Path to /etc raises ValidationError on Linux systems."""
        # Note: On macOS, /etc is a symlink to /private/etc, so the resolved
        # path won't start with /etc. This test is Linux-specific.
        import platform

        if platform.system() == "Linux":
            with pytest.raises(ValidationError, match="system directory"):
                validate_output_path("/etc/image.png")
        else:
            # On macOS/Windows, skip this test
            pytest.skip("System path validation is platform-specific")

    def test_system_usr_bin_path_raises_error(self):
        """Path to /usr/bin raises ValidationError."""
        with pytest.raises(ValidationError, match="system directory"):
            validate_output_path("/usr/bin/image.png")


class TestImageExtensions:
    """Test IMAGE_EXTENSIONS constant."""

    def test_contains_common_extensions(self):
        """IMAGE_EXTENSIONS contains common image formats."""
        assert ".png" in IMAGE_EXTENSIONS
        assert ".jpg" in IMAGE_EXTENSIONS
        assert ".jpeg" in IMAGE_EXTENSIONS
        assert ".webp" in IMAGE_EXTENSIONS
        assert ".gif" in IMAGE_EXTENSIONS

    def test_extensions_are_lowercase(self):
        """All extensions are lowercase."""
        for ext in IMAGE_EXTENSIONS:
            assert ext == ext.lower()

    def test_extensions_start_with_dot(self):
        """All extensions start with a dot."""
        for ext in IMAGE_EXTENSIONS:
            assert ext.startswith(".")


class TestOutputPathToolParameter:
    """Test output_path parameter in generate_image tool."""

    def test_generate_image_accepts_output_path(self):
        """Verify generate_image function accepts output_path parameter."""
        from nanobanana_mcp_server.tools.generate_image import register_generate_image_tool
        from fastmcp import FastMCP

        server = FastMCP("test")
        register_generate_image_tool(server)

        # Access the registered tool through FastMCP's internal structure
        # FastMCP Tool stores parameters as a JSON schema, not a function reference
        tools = list(server._tool_manager._tools.values())
        assert len(tools) > 0
        tool = tools[0]
        properties = tool.parameters.get("properties", {})
        assert "output_path" in properties

    def test_output_path_has_correct_default(self):
        """Verify output_path defaults to None (not required)."""
        from nanobanana_mcp_server.tools.generate_image import register_generate_image_tool
        from fastmcp import FastMCP

        server = FastMCP("test")
        register_generate_image_tool(server)

        tools = list(server._tool_manager._tools.values())
        assert len(tools) > 0
        tool = tools[0]
        # In JSON schema, optional params with default None are not in "required"
        required = tool.parameters.get("required", [])
        assert "output_path" not in required


class TestEnhancedImageServiceOutputPath:
    """Test output_path in EnhancedImageService."""

    def test_generate_images_accepts_output_path(self):
        """Verify generate_images method accepts output_path parameter."""
        from nanobanana_mcp_server.services.enhanced_image_service import EnhancedImageService
        import inspect

        sig = inspect.signature(EnhancedImageService.generate_images)
        assert "output_path" in sig.parameters

    def test_process_generated_image_accepts_output_path(self):
        """Verify _process_generated_image accepts output_path parameter."""
        from nanobanana_mcp_server.services.enhanced_image_service import EnhancedImageService
        import inspect

        sig = inspect.signature(EnhancedImageService._process_generated_image)
        assert "output_path" in sig.parameters


class TestOutputPathEdgeCases:
    """Test edge cases for output_path."""

    def test_path_with_spaces(self):
        """Path with spaces is handled correctly."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "my folder", "my image.png")
            result = resolve_output_path(output, "/default", "gen.png")
            assert "my folder" in result
            assert result.endswith("my image.png")
            assert Path(result).parent.exists()

    def test_path_with_unicode(self):
        """Path with unicode characters is handled correctly."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "图片", "照片.png")
            result = resolve_output_path(output, "/default", "gen.png")
            assert result.endswith("照片.png")
            assert Path(result).parent.exists()

    def test_very_long_path(self):
        """Very long paths are handled (up to filesystem limits)."""
        with TemporaryDirectory() as tmpdir:
            # Create a path that's long but within reasonable limits
            long_name = "a" * 100 + ".png"
            output = os.path.join(tmpdir, long_name)
            result = resolve_output_path(output, "/default", "gen.png")
            assert result.endswith(long_name)

    def test_uppercase_extension(self):
        """Uppercase extensions are recognized."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "IMAGE.PNG")
            result = resolve_output_path(output, "/default", "gen.png")
            # Should be recognized as a file path due to extension
            assert result.endswith("IMAGE.PNG")

    def test_mixed_case_extension(self):
        """Mixed case extensions are recognized."""
        with TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "photo.JpG")
            result = resolve_output_path(output, "/default", "gen.png")
            assert result.endswith("photo.JpG")


# Mark all tests as unit tests
pytestmark = pytest.mark.unit
