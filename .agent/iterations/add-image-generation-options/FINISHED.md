# Iteration: add-image-generation-options

## Summary

Added `aspect_ratio` and `image_size` parameters to both CLI and MCP interfaces for image generation.

## Changes

### CLI (`src/ez_banana/cli.py`)
- Added `--aspect-ratio` argument with choices validation (10 ratios supported)
- Added `--image-size` argument with choices validation (1K, 2K, 4K)
- Defaults: `1:1` for aspect ratio, `1K` for image size

### MCP Server (`src/ez_banana/mcp_server.py`)
- Added `aspect_ratio` parameter with `Annotated[Literal[...], Field()]` pattern
- Added `image_size` parameter with same pattern
- Added docstring to `generate_image` tool

### Core Logic
- `src/ez_banana/models.py`: Extended `ValidatedInput` dataclass with new fields
- `src/ez_banana/openrouter.py`: Added validation constants and conditional `image_config` payload building (only includes non-default values)
- `src/ez_banana/validation.py`: Added validation functions and integrated into input flow
- `src/ez_banana/app.py`: Updated flow to pass new parameters through

### Tests
- `tests/test_main.py`: Added 6 CLI tests covering argument passing, defaults, and validation
- `tests/test_mcp_server.py`: Added 4 MCP tests for parameter passing and defaults

## Validation

All tests pass:
```bash
uv run python -m unittest discover -s tests -v
```

## Files Modified

- src/ez_banana/app.py
- src/ez_banana/cli.py
- src/ez_banana/mcp_server.py
- src/ez_banana/models.py
- src/ez_banana/openrouter.py
- src/ez_banana/validation.py
- tests/test_main.py
- tests/test_mcp_server.py
