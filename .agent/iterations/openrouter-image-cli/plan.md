# Implementation Plan: openrouter-image-cli

## Phase 1: Project Setup and CLI Skeleton
1. Confirm the Python project is configured for Python 3.14 and managed with `uv`.
2. Add `requests` as the required dependency.
3. Create the CLI entry module and argument parser with:
   - required `--prompt`
   - optional `--image`
   - optional `--out-dir` defaulting to `.`
4. Define core constants for endpoint URL, default model (`google/gemini-2.5-flash-image-preview`), and request timeout.

## Phase 2: Input Validation and File Utilities
1. Implement environment validation for `OPENROUTER_API_KEY` with a clear fail-fast error.
2. Validate `--prompt` is non-empty after trimming whitespace.
3. If `--image` is provided, validate the file exists and is readable.
4. Infer reference image MIME type from file metadata/extension and reject unsupported or unknown types.
5. Ensure output directory exists by creating `--out-dir` when missing.

## Phase 3: Request Payload Construction
1. Build a payload factory for two request modes:
   - prompt-only text message
   - prompt + reference image message array (`text` then `image_url` data URL)
2. Encode reference image bytes to base64 and construct `data:<mime>;base64,<payload>` URL.
3. Set request headers with bearer token and JSON content type.
4. Include `modalities` as `['image', 'text']` for the default model flow.

## Phase 4: API Execution and Response Handling
1. Send `POST` requests to `https://openrouter.ai/api/v1/chat/completions` using `requests` with configured timeout.
2. Implement structured error handling for timeout, HTTP errors, and generic request failures.
3. Parse JSON response and extract generated image data URL from `choices[0].message.images[0].image_url.url`.
4. Validate response shape and return actionable errors when expected fields are missing.
5. Decode base64 image bytes from the data URL and prepare `.png` output bytes.

## Phase 5: Output Naming, Saving, and User Feedback
1. Generate filenames using `ezbanana_<timestamp>_<8-digit random string>.png` with UTC `YYYYMMDD_HHMMSS` timestamp.
2. Check for collisions in target directory; regenerate suffix until a unique filename is found.
3. Write image bytes to disk in the selected output directory.
4. Print the final saved file path on success.
5. Ensure all failure paths return non-zero exit codes and clear, actionable messages.

## Phase 6: Verification and Acceptance Checks
1. Validate prompt-only flow saves one image in current directory by default.
2. Validate prompt + `--image` flow sends reference image successfully and saves output.
3. Validate error behavior for missing API key, invalid image path, API HTTP failures, and timeouts.
4. Validate `--out-dir` override behavior and automatic directory creation.
5. Confirm filename format and collision retry logic match requirements.

### Phase 6 Completion Notes
- Added automated acceptance tests in `tests/test_main.py` covering all five verification goals.
- Verification command: `uv run python -m unittest discover -s tests -v`
- Current result: `Ran 8 tests ... OK`.
