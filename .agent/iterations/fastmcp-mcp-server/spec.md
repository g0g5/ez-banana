# Iteration Spec: fastmcp-mcp-server

## Goal
Add an MCP server interface for `ez-banana` using FastMCP, with executable command `ez-banana-mcp`, exposing a v1 image-generation tool that mirrors current CLI behavior.

## Confirmed Requirements
- Iteration name: `fastmcp-mcp-server`.
- Framework: `FastMCP`.
- MCP executable command: `ez-banana-mcp`.
- MCP surface for v1: tools only (no resources/prompts).
- Initial tool set: single `generate_image`-style tool that maps to existing CLI flow.
- Default transport: `stdio`.
- Tool input contract: mirror existing CLI arguments/validation:
  - required prompt,
  - optional reference image path,
  - optional output directory.
- Config source: reuse existing environment variable flow (`OPENROUTER_API_KEY` and current config constants).
- Success result: return saved file path plus metadata.
- Failure result: structured MCP errors mapped from existing `CliError`/validation/network errors.
- Quality gate: unit tests only.

## External Dependencies (Key)
- `fastmcp` (required for MCP server/tool definition and stdio runtime).
- `requests` (already used by core OpenRouter pipeline, reused by MCP tool execution path).

## Library Research Notes (Implementation-Focused)

### FastMCP
```python
from fastmcp import FastMCP

mcp = FastMCP("ez-banana")

@mcp.tool
def generate_image(prompt: str, image: str | None = None, out_dir: str = ".") -> dict:
    # call existing app pipeline
    return {"path": "...", "model": "..."}

def main() -> None:
    mcp.run(transport="stdio")
```

```toml
[project.scripts]
ez-banana-mcp = "ez_banana.mcp_server:main"
```

### requests
```python
resp = requests.post(url, headers=headers, json=payload, timeout=(3.05, 60))
resp.raise_for_status()
data = resp.json()
```

```python
try:
    resp = requests.post(url, json=payload, timeout=(3.05, 60))
    resp.raise_for_status()
except requests.exceptions.Timeout:
    ...
except requests.exceptions.HTTPError as e:
    ...
except requests.exceptions.RequestException:
    ...
```

## Functional Design
- Add new module `src/ez_banana/mcp_server.py` containing:
  - FastMCP app instance.
  - One registered tool for image generation.
  - `main()` entrypoint that runs FastMCP on `stdio`.
- Tool implementation should reuse existing domain pipeline instead of duplicating logic:
  - validate inputs via `validate_inputs` (or extracted shared validator helper),
  - construct request via `build_openrouter_request`,
  - call `generate_image_from_openrouter`,
  - save file via `save_generated_image`.
- Add/adjust small shared helper(s) if needed so CLI and MCP both call the same orchestration function.

## MCP Tool Contract (v1)
- Tool name: `generate_image` (or equivalent clear snake_case name).
- Inputs:
  - `prompt: str` (required, non-empty after trim).
  - `image: str | None` (optional local file path, same MIME/type checks as CLI).
  - `out_dir: str` (optional, default `"."`, auto-create directory).
- Success output object:
  - `path: str` (saved image file path).
  - `filename: str`.
  - `out_dir: str`.
  - `model: str` (from config default model constant).
  - `transport: "stdio"` (informational metadata).
- Error behavior:
  - Catch `CliError` and raise/return structured MCP tool error with stable fields:
    - `code` (e.g., `validation_error`, `api_error`, `timeout_error`, `io_error`),
    - `message` (actionable text already used by CLI where possible).

## Packaging and Command Exposure
- Update `pyproject.toml` `[project.scripts]` with:
  - `ez-banana-mcp = "ez_banana.mcp_server:main"`.
- Keep existing `ez-banana` command unchanged.

## Testing Plan (unittest)
- Add MCP-focused unit tests (new test module under `tests/`), covering:
  - happy path prompt-only call returns path + metadata,
  - prompt + image call builds multimodal request behavior,
  - missing API key maps to structured MCP error,
  - invalid image path maps to structured MCP error,
  - OpenRouter HTTP error maps to structured MCP error,
  - timeout maps to structured MCP error.
- Mock network calls (`requests.post`) and filesystem behavior similarly to existing tests.

## Acceptance Criteria
- Running `ez-banana-mcp` starts MCP server over `stdio`.
- MCP client can invoke v1 generate tool with required/optional args and receive saved path + metadata.
- Input validation and OpenRouter failure modes are surfaced as structured MCP errors.
- Existing CLI command behavior remains unchanged.
- Unit tests for new MCP interface pass with `uv run python -m unittest discover -s tests -v`.

## Non-Goals
- No MCP resources or prompts in this iteration.
- No HTTP transport as default runtime.
- No new model-parameter surface beyond existing CLI-equivalent inputs.
