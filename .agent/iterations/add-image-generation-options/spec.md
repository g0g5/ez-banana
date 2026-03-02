# SPEC: Add Image Generation Options

**Iteration Name:** add-image-generation-options  
**Goal:** Refactor CLI and MCP interfaces to support `image_size` and `aspect_ratio` parameters for image generation.

## Background
OpenRouter image generation models support two configuration options in the `image_config` parameter:
- **aspect_ratio**: Controls image dimensions (e.g., `1:1`, `16:9`)
- **image_size**: Controls resolution (e.g., `1K`, `2K`, `4K`)

Reference: https://openrouter.ai/docs/guides/overview/multimodal/image-generation

## Requirements

### 1. Supported Values

**Aspect Ratio:**
- Standard ratios: `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`
- Default: `1:1` (1024×1024)

**Image Size:**
- Supported sizes: `1K`, `2K`, `4K`
- Default: `1K`

### 2. CLI Interface

Add two optional arguments to the CLI:
- `--aspect-ratio` with choices validation
- `--image-size` with choices validation
- Both should use defaults from OpenRouter (`1:1` and `1K`)

**argparse patterns:**
```python
parser.add_argument('--aspect-ratio', choices=['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9'], default='1:1')
parser.add_argument('--image-size', choices=['1K', '2K', '4K'], default='1K')
```

### 3. MCP Interface

Add two optional parameters to the MCP tool using FastMCP's Annotated + Field pattern:

```python
from typing import Annotated, Literal
from pydantic import Field

@mcp.tool()
def generate_image(
    prompt: str,
    aspect_ratio: Annotated[
        Literal["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        Field(description="Aspect ratio for generated image", default="1:1")
    ] = "1:1",
    image_size: Annotated[
        Literal["1K", "2K", "4K"],
        Field(description="Resolution size for generated image", default="1K")
    ] = "1K"
) -> str:
    """Generate an image from a text prompt."""
    ...
```

### 4. OpenRouter Integration

Conditionally build the `image_config` payload:

```python
payload = {
    "model": model,
    "messages": [{"role": "user", "content": prompt}],
    "modalities": ["image", "text"]
}

# Only include image_config if non-default values are provided
image_config = {}
if aspect_ratio != "1:1":
    image_config["aspect_ratio"] = aspect_ratio
if image_size != "1K":
    image_config["image_size"] = image_size

if image_config:
    payload["image_config"] = image_config
```

Alternative: Always include with defaults (simpler, OpenRouter handles defaults)

### 5. Implementation Files

**Modify:**
- `src/ez_banana/cli.py` - Add argparse arguments
- `src/ez_banana/mcp_server.py` - Add MCP tool parameters
- `src/ez_banana/generator.py` - Update generation logic to include image_config

### 6. Testing

Add tests for:
- CLI argument parsing with valid/invalid values
- MCP tool invocation with various parameter combinations
- OpenRouter payload construction with/without image_config

## Success Criteria

- [ ] CLI accepts `--aspect-ratio` and `--image-size` arguments with validation
- [ ] MCP tool accepts `aspect_ratio` and `image_size` parameters with validation
- [ ] Both interfaces pass valid parameters to OpenRouter in `image_config`
- [ ] Default values work correctly when parameters are omitted
- [ ] All existing tests pass
- [ ] New tests added for the new options

## Notes

- Both parameters are optional with sensible defaults
- Validation ensures only supported values are accepted
- Implementation should be backward compatible (existing code without these parameters still works)
