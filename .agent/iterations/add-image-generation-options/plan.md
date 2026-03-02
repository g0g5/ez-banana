# Implementation Plan: Add Image Generation Options

**Iteration:** add-image-generation-options

## Phase 1: Core Generation Logic Updates

### Step 1.1: Update Generator Function Signature
- Modify `src/ez_banana/generator.py` to accept optional `aspect_ratio` and `image_size` parameters
- Add constants for valid aspect ratios and image sizes at module level

### Step 1.2: Build image_config Payload
- Implement conditional payload construction in the OpenRouter request function
- Only include `image_config` in payload when non-default values are provided
- Ensure `image_config` dict contains `aspect_ratio` and/or `image_size` keys as appropriate

### Step 1.3: Validation
- Add validation logic for aspect ratio values
- Add validation logic for image size values
- Raise appropriate errors for invalid values

## Phase 2: CLI Interface Updates

### Step 2.1: Add CLI Arguments
- Open `src/ez_banana/cli.py`
- Add `--aspect-ratio` argument with choices and default value
- Add `--image-size` argument with choices and default value
- Add help text for both arguments

### Step 2.2: Pass CLI Arguments to Generator
- Update the function that calls the generator to pass the new CLI arguments
- Ensure backward compatibility (arguments are optional)

### Step 2.3: Update Help Documentation
- Verify help output shows the new options with defaults

## Phase 3: MCP Interface Updates

### Step 3.1: Import Required Types
- Add imports for `Annotated`, `Literal` from typing
- Add import for `Field` from pydantic

### Step 3.2: Update MCP Tool Definition
- Open `src/ez_banana/mcp_server.py`
- Add `aspect_ratio` parameter with `Annotated[..., Field(...)]` pattern
- Add `image_size` parameter with `Annotated[..., Field(...)]` pattern
- Update docstring to document new parameters

### Step 3.3: Pass MCP Parameters to Generator
- Update the tool function to pass parameters to the generator
- Ensure default values are properly handled

## Phase 4: Testing

### Step 4.1: Generator Tests
- Add test for generator with valid aspect ratios
- Add test for generator with valid image sizes
- Add test for generator without new options (backward compatibility)

### Step 4.2: CLI Tests
- Add test for CLI parsing of `--aspect-ratio`
- Add test for CLI parsing of `--image-size`
- Add test for CLI with invalid values (should error)

### Step 4.3: MCP Tests
- Add test for MCP tool with all parameters
- Add test for MCP tool with default values
- Add test for MCP tool validation

### Step 4.4: Run Full Test Suite
- Execute `uv run python -m unittest discover -s tests -v`
- Fix any failing tests

## Phase 5: Verification

### Step 5.1: Manual CLI Test
- Test CLI with different aspect ratios
- Test CLI with different image sizes
- Test CLI without new options

### Step 5.2: Manual MCP Test
- Test MCP server with various parameter combinations
- Verify default behavior

### Step 5.3: Code Review
- Review all modified files for consistency
- Check for any missing validation or error handling
