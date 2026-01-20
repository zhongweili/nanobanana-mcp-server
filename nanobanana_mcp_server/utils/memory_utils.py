"""Memory management utilities for high-resolution image processing."""

import asyncio
import logging
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import AsyncIterator, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import tracemalloc
    TRACEMALLOC_AVAILABLE = True
except ImportError:
    TRACEMALLOC_AVAILABLE = False

try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

from ..config.constants import (
    BYTES_PER_PIXEL_RGBA,
    IMAGE_OVERHEAD_MULTIPLIER,
    MEMORY_BUFFER_PERCENT,
)


class MemoryMonitor:
    """Monitor and manage memory usage for image operations."""

    def __init__(self, limit_mb: int = 2048):
        """Initialize memory monitor.

        Args:
            limit_mb: Memory limit in megabytes
        """
        self.limit_bytes = limit_mb * 1024 * 1024
        self.logger = logging.getLogger(__name__)

    def check_available(self, required_bytes: int) -> bool:
        """Check if sufficient memory is available.

        Args:
            required_bytes: Bytes required for operation

        Returns:
            True if sufficient memory available
        """
        if not PSUTIL_AVAILABLE:
            # If psutil not available, be conservative
            return required_bytes < self.limit_bytes

        try:
            available = psutil.virtual_memory().available
            # Ensure buffer space
            required_with_buffer = required_bytes + self.limit_bytes * MEMORY_BUFFER_PERCENT
            return available > required_with_buffer
        except Exception as e:
            self.logger.warning(f"Could not check memory: {e}")
            return required_bytes < self.limit_bytes

    def get_memory_usage(self) -> dict:
        """Get current memory usage statistics.

        Returns:
            Dictionary with memory stats
        """
        stats = {
            "available": False,
            "total_mb": 0,
            "used_mb": 0,
            "available_mb": 0,
            "percent": 0,
        }

        if PSUTIL_AVAILABLE:
            try:
                mem = psutil.virtual_memory()
                stats.update({
                    "available": True,
                    "total_mb": mem.total / (1024 * 1024),
                    "used_mb": mem.used / (1024 * 1024),
                    "available_mb": mem.available / (1024 * 1024),
                    "percent": mem.percent,
                })
            except Exception:
                pass

        return stats

    @contextmanager
    def track_allocation(self, operation: str):
        """Track memory usage for an operation.

        Args:
            operation: Name of the operation being tracked

        Yields:
            None
        """
        if not TRACEMALLOC_AVAILABLE:
            yield
            return

        tracemalloc.start()
        try:
            yield
        finally:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            self.logger.info(
                f"Memory usage for {operation}: "
                f"Current={current/1024/1024:.2f}MB, "
                f"Peak={peak/1024/1024:.2f}MB"
            )

    def estimate_image_memory(
        self,
        width: int,
        height: int,
        format: str = "png"
    ) -> int:
        """Estimate memory required for an image.

        Args:
            width: Image width
            height: Image height
            format: Image format

        Returns:
            Estimated bytes required
        """
        bytes_per_pixel = BYTES_PER_PIXEL_RGBA if format in ["png", "webp"] else 3
        base_memory = width * height * bytes_per_pixel
        return int(base_memory * IMAGE_OVERHEAD_MULTIPLIER)


class StreamingImageProcessor:
    """Process large images using streaming to minimize memory usage."""

    def __init__(self, chunk_size: int = 8192):
        """Initialize streaming processor.

        Args:
            chunk_size: Size of chunks for streaming (bytes)
        """
        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)

    async def process_large_image(
        self,
        image_data: bytes
    ) -> AsyncIterator[bytes]:
        """Process image in chunks to avoid memory spikes.

        Args:
            image_data: Full image data

        Yields:
            Processed chunks of image data
        """
        for i in range(0, len(image_data), self.chunk_size):
            chunk = image_data[i:i + self.chunk_size]
            # Process chunk if needed (placeholder for actual processing)
            processed_chunk = await self._process_chunk(chunk)
            yield processed_chunk

    async def _process_chunk(self, chunk: bytes) -> bytes:
        """Process a single chunk of image data.

        Args:
            chunk: Image data chunk

        Returns:
            Processed chunk
        """
        # Placeholder for actual chunk processing
        # In real implementation, this could apply transformations
        await asyncio.sleep(0)  # Yield control
        return chunk

    async def save_streaming(
        self,
        image_stream: AsyncIterator[bytes],
        path: Path
    ) -> int:
        """Save image using streaming to minimize memory usage.

        Args:
            image_stream: Async iterator of image chunks
            path: Path to save image

        Returns:
            Total bytes written
        """
        if not AIOFILES_AVAILABLE:
            # Fallback to synchronous write
            return await self._save_sync(image_stream, path)

        total_bytes = 0
        async with aiofiles.open(path, 'wb') as f:
            async for chunk in image_stream:
                await f.write(chunk)
                total_bytes += len(chunk)

        self.logger.debug(f"Saved {total_bytes} bytes to {path}")
        return total_bytes

    async def _save_sync(
        self,
        image_stream: AsyncIterator[bytes],
        path: Path
    ) -> int:
        """Synchronous fallback for saving image.

        Args:
            image_stream: Async iterator of image chunks
            path: Path to save image

        Returns:
            Total bytes written
        """
        total_bytes = 0
        with open(path, 'wb') as f:
            async for chunk in image_stream:
                f.write(chunk)
                total_bytes += len(chunk)
        return total_bytes

    async def read_streaming(
        self,
        path: Path,
        chunk_size: Optional[int] = None
    ) -> AsyncIterator[bytes]:
        """Read image file in chunks.

        Args:
            path: Path to image file
            chunk_size: Size of chunks (uses default if None)

        Yields:
            Chunks of image data
        """
        chunk_size = chunk_size or self.chunk_size

        if AIOFILES_AVAILABLE:
            async with aiofiles.open(path, 'rb') as f:
                while True:
                    chunk = await f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        else:
            # Fallback to synchronous read
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk


class TempFileManager:
    """Manage temporary files for large image operations."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize temp file manager.

        Args:
            base_dir: Base directory for temp files (uses system temp if None)
        """
        self.base_dir = base_dir or Path(tempfile.gettempdir())
        self.logger = logging.getLogger(__name__)
        self._temp_files: list[Path] = []

    def create_temp_file(
        self,
        prefix: str = "nanobanana_",
        suffix: str = ".tmp"
    ) -> Path:
        """Create a temporary file.

        Args:
            prefix: File prefix
            suffix: File suffix

        Returns:
            Path to temporary file
        """
        fd, path = tempfile.mkstemp(
            prefix=prefix,
            suffix=suffix,
            dir=self.base_dir
        )
        os.close(fd)  # Close file descriptor
        temp_path = Path(path)
        self._temp_files.append(temp_path)
        self.logger.debug(f"Created temp file: {temp_path}")
        return temp_path

    def cleanup(self) -> None:
        """Clean up all temporary files."""
        for path in self._temp_files:
            try:
                if path.exists():
                    path.unlink()
                    self.logger.debug(f"Deleted temp file: {path}")
            except Exception as e:
                self.logger.warning(f"Could not delete temp file {path}: {e}")
        self._temp_files.clear()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temp files."""
        self.cleanup()


def optimize_for_memory(width: int, height: int) -> dict:
    """Get optimization settings based on image dimensions.

    Args:
        width: Image width
        height: Image height

    Returns:
        Dictionary with optimization settings
    """
    total_pixels = width * height

    # Define thresholds
    small = 1024 * 1024    # 1 megapixel
    medium = 2048 * 2048   # 4 megapixels
    large = 3840 * 2160    # 8K

    if total_pixels <= small:
        return {
            "use_streaming": False,
            "chunk_size": 8192,
            "compression_quality": 95,
            "enable_cache": True,
        }
    elif total_pixels <= medium:
        return {
            "use_streaming": False,
            "chunk_size": 16384,
            "compression_quality": 90,
            "enable_cache": True,
        }
    elif total_pixels <= large:
        return {
            "use_streaming": True,
            "chunk_size": 32768,
            "compression_quality": 85,
            "enable_cache": False,
        }
    else:
        # Very large images
        return {
            "use_streaming": True,
            "chunk_size": 65536,
            "compression_quality": 80,
            "enable_cache": False,
        }


async def process_with_memory_limit(
    image_data: bytes,
    width: int,
    height: int,
    memory_limit_mb: int = 2048
) -> bytes:
    """Process image with memory limit enforcement.

    Args:
        image_data: Raw image data
        width: Image width
        height: Image height
        memory_limit_mb: Memory limit in MB

    Returns:
        Processed image data

    Raises:
        MemoryError: If operation would exceed memory limit
    """
    monitor = MemoryMonitor(memory_limit_mb)

    # Estimate memory requirement
    required_bytes = monitor.estimate_image_memory(width, height)

    # Check if we have enough memory
    if not monitor.check_available(required_bytes):
        raise MemoryError(
            f"Insufficient memory for {width}x{height} image. "
            f"Required: {required_bytes/(1024*1024):.1f}MB"
        )

    # Get optimization settings
    settings = optimize_for_memory(width, height)

    if settings["use_streaming"]:
        # Use streaming for large images
        processor = StreamingImageProcessor(settings["chunk_size"])

        # Create temp file for processed result
        with TempFileManager() as temp_mgr:
            temp_path = temp_mgr.create_temp_file(suffix=".png")

            # Process and save with streaming
            stream = processor.process_large_image(image_data)
            await processor.save_streaming(stream, temp_path)

            # Read back result
            result = b""
            async for chunk in processor.read_streaming(temp_path):
                result += chunk

            return result
    else:
        # Process directly for smaller images
        # Placeholder for actual processing
        await asyncio.sleep(0)  # Yield control
        return image_data