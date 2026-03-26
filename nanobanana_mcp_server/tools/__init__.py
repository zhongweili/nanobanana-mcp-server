from .generate_image import register_generate_image_tool
from .generate_svg import register_generate_svg_tool
from .maintenance import register_maintenance_tool
from .output_stats import register_output_stats_tool
from .upload_file import register_upload_file_tool

__all__ = [
    "register_generate_image_tool",
    "register_generate_svg_tool",
    "register_upload_file_tool",
    "register_output_stats_tool",
    "register_maintenance_tool",
]
