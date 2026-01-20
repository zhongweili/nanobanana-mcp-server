# Full Resolution Image Support - Technical Design

## Executive Summary
This document outlines the technical design for implementing full-resolution image generation support in the Nano Banana MCP Server. The design enables generation of images up to 4K resolution (3840x3840) with the Pro model and 2K resolution (2048x2048) with the Flash model, while maintaining backward compatibility and system performance.

## System Architecture

### Component Overview
```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Client Layer                        │
├─────────────────────────────────────────────────────────────┤
│                    Tools & Resources                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │generate_image│  │ edit_image   │  │ upload_file  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                   Resolution Manager                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Validator   │  │   Presets    │  │  Optimizer   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ImageService  │  │ProImageSvc   │  │StorageService│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                    Gemini API Layer                          │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Resolution Manager (New Component)
**Purpose**: Centralized resolution handling and validation

**Responsibilities**:
- Validate resolution parameters against model capabilities
- Convert between resolution formats (presets, dimensions, aspect ratios)
- Optimize resolution based on system resources
- Provide resolution recommendations

**Location**: `nanobanana_mcp_server/services/resolution_manager.py`

#### 2. Enhanced Image Services
**Changes to existing services**:
- `ImageService`: Add full resolution support for Flash model
- `ProImageService`: Enable 4K resolution generation
- `ImageStorageService`: Optimize for high-resolution storage

#### 3. Configuration Updates
**New configuration parameters**:
```python
@dataclass
class ResolutionConfig:
    flash_max_resolution: int = 2048
    pro_max_resolution: int = 3840
    default_resolution: str = "1024"
    enable_full_resolution: bool = True
    memory_limit_mb: int = 2048
    compression_quality: int = 85
    thumbnail_sizes: List[int] = field(default_factory=lambda: [256, 512, 1024])
```

## Detailed Design

### Resolution Parameter Handling

#### Input Formats
Support multiple resolution specification formats:

1. **Preset Strings**
   - "4k" → 3840x3840
   - "2k" → 2048x2048
   - "1080p" → 1920x1080
   - "720p" → 1280x720
   - "original" → Model's maximum
   - "high" → 75% of maximum
   - "medium" → 50% of maximum
   - "low" → 25% of maximum

2. **Dimension Specifications**
   - `{"width": 3840, "height": 2160}`
   - `"3840x2160"`
   - `[3840, 2160]`

3. **Aspect Ratio with Target Size**
   - `{"aspect_ratio": "16:9", "target_size": "4k"}`
   - `{"aspect_ratio": 1.778, "max_dimension": 3840}`

#### Resolution Validation Algorithm
```python
def validate_resolution(resolution, model_tier, config):
    # Parse resolution input
    width, height = parse_resolution(resolution)

    # Get model limits
    max_res = config.pro_max_resolution if model_tier == "pro" else config.flash_max_resolution

    # Validate dimensions
    if width > max_res or height > max_res:
        # Downscale proportionally
        scale = max_res / max(width, height)
        width = int(width * scale)
        height = int(height * scale)

    # Check memory constraints
    estimated_memory = width * height * 4 * 1.5  # RGBA + overhead
    if estimated_memory > config.memory_limit_mb * 1024 * 1024:
        raise ValueError(f"Resolution would exceed memory limit")

    return width, height
```

### API Modifications

#### generate_image Tool Enhancement
```python
@server.tool()
def generate_image(
    prompt: str,
    n: int = 1,
    size: Optional[str] = None,  # Deprecated, kept for compatibility
    resolution: Optional[Union[str, Dict, List]] = None,  # New parameter
    model_tier: str = "auto",
    enable_grounding: bool = False,
    thinking_level: str = "LOW",
    store_images: bool = True,
    enhance_prompt: bool = True,
    **kwargs
) -> ToolResult:
    # Resolution handling
    if resolution is None and size is not None:
        # Backward compatibility
        resolution = size
    elif resolution is None:
        # Use model-appropriate default
        resolution = "4k" if model_tier == "pro" else "1024"

    # Validate and normalize resolution
    res_manager = ResolutionManager(config)
    final_resolution = res_manager.process_resolution(
        resolution,
        model_tier,
        prompt_hints=extract_resolution_hints(prompt)
    )

    # Rest of implementation...
```

### Memory Management Strategy

#### Streaming Implementation
```python
class StreamingImageProcessor:
    def __init__(self, chunk_size: int = 8192):
        self.chunk_size = chunk_size

    async def process_large_image(self, image_data: bytes) -> AsyncIterator[bytes]:
        """Process image in chunks to avoid memory spikes"""
        for i in range(0, len(image_data), self.chunk_size):
            chunk = image_data[i:i + self.chunk_size]
            processed_chunk = await self._process_chunk(chunk)
            yield processed_chunk

    async def save_streaming(self, image_stream: AsyncIterator[bytes], path: Path):
        """Save image using streaming to minimize memory usage"""
        async with aiofiles.open(path, 'wb') as f:
            async for chunk in image_stream:
                await f.write(chunk)
```

#### Memory Monitoring
```python
class MemoryMonitor:
    def __init__(self, limit_mb: int):
        self.limit_bytes = limit_mb * 1024 * 1024

    def check_available(self, required_bytes: int) -> bool:
        """Check if sufficient memory is available"""
        import psutil
        available = psutil.virtual_memory().available
        return available > required_bytes + self.limit_bytes * 0.2  # 20% buffer

    @contextmanager
    def track_allocation(self, operation: str):
        """Track memory usage for an operation"""
        import tracemalloc
        tracemalloc.start()
        yield
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        logger.info(f"{operation}: Current={current/1024/1024:.2f}MB, Peak={peak/1024/1024:.2f}MB")
```

### Storage Optimization

#### Progressive Storage Strategy
```python
class OptimizedImageStorage:
    def __init__(self, storage_service: ImageStorageService):
        self.storage = storage_service
        self.compression_levels = {
            "thumbnail": 70,
            "preview": 80,
            "display": 85,
            "original": 95
        }

    async def store_with_variants(self, image: Image, metadata: Dict) -> Dict:
        """Store image with multiple resolution variants"""
        results = {}

        # Store original (with compression)
        if image.width > 2048 or image.height > 2048:
            # High-res images get compressed
            results["original"] = await self._store_compressed(
                image,
                quality=self.compression_levels["original"]
            )
        else:
            results["original"] = await self.storage.store(image)

        # Generate and store variants
        variants = [
            ("thumbnail", 256),
            ("preview", 512),
            ("display", 1024)
        ]

        for variant_name, size in variants:
            if image.width > size or image.height > size:
                variant = self._resize_image(image, size)
                results[variant_name] = await self._store_compressed(
                    variant,
                    quality=self.compression_levels[variant_name]
                )

        return results
```

### Configuration Schema Updates

#### Updated Settings Structure
```python
# config/settings.py additions
@dataclass
class ResolutionConfig:
    """Configuration for resolution handling"""
    # Model-specific limits
    flash_max_resolution: int = 2048
    pro_max_resolution: int = 3840

    # Default settings
    default_resolution: str = "1024"
    enable_full_resolution: bool = True

    # Memory management
    memory_limit_mb: int = 2048
    enable_streaming: bool = True
    chunk_size_kb: int = 8192

    # Storage optimization
    compression_quality: int = 85
    use_webp: bool = True
    thumbnail_sizes: List[int] = field(default_factory=lambda: [256, 512, 1024])

    # Resolution presets
    presets: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        "4k": (3840, 3840),
        "2k": (2048, 2048),
        "1080p": (1920, 1080),
        "720p": (1280, 720),
        "480p": (854, 480)
    })

@dataclass
class Settings:
    # ... existing fields ...
    resolution: ResolutionConfig = field(default_factory=ResolutionConfig)
```

## Implementation Plan

### Phase 1: Core Resolution Support (Week 1)
1. Implement ResolutionManager service
2. Update configuration schema
3. Add resolution validation logic
4. Update generate_image tool signature

### Phase 2: Service Integration (Week 1-2)
1. Enhance ImageService for Flash model resolutions
2. Enable 4K in ProImageService
3. Implement resolution presets
4. Add backward compatibility layer

### Phase 3: Memory Optimization (Week 2)
1. Implement streaming image processor
2. Add memory monitoring
3. Implement graceful degradation
4. Add memory usage metrics

### Phase 4: Storage Optimization (Week 2-3)
1. Implement progressive storage strategy
2. Add compression options
3. Generate resolution variants
4. Update retrieval logic

### Phase 5: Testing & Documentation (Week 3)
1. Unit tests for ResolutionManager
2. Integration tests for high-res generation
3. Performance benchmarks
4. Update API documentation

## Testing Strategy

### Unit Tests
- Resolution parsing and validation
- Memory monitoring accuracy
- Compression quality verification
- Preset resolution mapping

### Integration Tests
- End-to-end 4K image generation
- Memory limit enforcement
- Storage optimization verification
- Backward compatibility

### Performance Tests
- Generation time vs resolution
- Memory usage patterns
- Storage efficiency
- Concurrent request handling

### Load Tests
- Multiple high-res requests
- Memory pressure scenarios
- Storage capacity limits
- API quota management

## Monitoring & Observability

### Metrics to Track
- Resolution distribution of requests
- Memory usage per resolution tier
- Generation time by resolution
- Storage usage by variant type
- API quota consumption rate

### Logging
- Resolution validation results
- Memory allocation events
- Compression ratios achieved
- Storage variant generation
- Performance bottlenecks

### Alerts
- Memory usage > 80% of limit
- Generation time > 2x expected
- Storage errors for high-res images
- API quota approaching limit

## Security Considerations

### Input Validation
- Prevent resolution values that could cause integer overflow
- Validate aspect ratios to prevent extreme dimensions
- Sanitize custom resolution parameters
- Rate limit high-resolution requests

### Resource Protection
- Implement per-user resolution limits
- Queue management for resource-intensive requests
- Graceful degradation under load
- Circuit breaker for API failures

## Migration Strategy

### Backward Compatibility
- Keep `size` parameter functional with deprecation warning
- Map old size values to new resolution presets
- Maintain existing default behaviors
- Version API responses appropriately

### Data Migration
- No data migration required (new feature)
- Existing images remain unchanged
- New metadata fields are optional

## Future Enhancements

### Planned Improvements
1. **Smart Resolution Selection**
   - Analyze prompt for resolution hints
   - Optimize based on subject matter
   - Learn from user preferences

2. **Advanced Processing**
   - AI-powered upscaling
   - Resolution-aware prompt enhancement
   - Batch processing optimization

3. **Enhanced Storage**
   - CDN integration for variants
   - Lazy variant generation
   - Intelligent cache management

## Appendix

### Resolution Preset Mappings
| Preset | Dimensions | Aspect Ratio | Use Case |
|--------|------------|--------------|----------|
| 4k | 3840x3840 | 1:1 | Maximum quality, Pro model |
| 2k | 2048x2048 | 1:1 | High quality, Flash model |
| 1080p | 1920x1080 | 16:9 | Standard HD, video |
| 720p | 1280x720 | 16:9 | Web display |
| square_lg | 1024x1024 | 1:1 | Default square |
| portrait_4k | 2160x3840 | 9:16 | Vertical 4K |
| landscape_4k | 3840x2160 | 16:9 | Horizontal 4K |

### API Examples

#### Basic 4K Generation
```python
result = generate_image(
    prompt="A stunning landscape",
    resolution="4k",
    model_tier="pro"
)
```

#### Custom Resolution
```python
result = generate_image(
    prompt="Product photo",
    resolution={"width": 3000, "height": 2000},
    model_tier="pro"
)
```

#### Aspect Ratio Preserved
```python
result = generate_image(
    prompt="Movie poster",
    resolution={"aspect_ratio": "2:3", "max_dimension": 3840},
    model_tier="pro"
)