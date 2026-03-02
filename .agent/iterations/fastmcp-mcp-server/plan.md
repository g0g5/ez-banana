# Implementation Plan: fastmcp-mcp-server

## Phase 1: Align Shared Generation Flow
- Review current CLI orchestration (`validate_inputs` -> OpenRouter request -> generation -> file save).
- Extract a reusable application-level helper (or equivalent) that accepts prompt/image/out_dir inputs and returns normalized success data needed by both CLI and MCP.
- Keep existing CLI behavior/output unchanged while switching it to the shared helper.

## Phase 2: Implement MCP Server Module
- Create `src/ez_banana/mcp_server.py` with a FastMCP server instance.
- Register a single v1 tool (`generate_image`) using CLI-equivalent inputs: `prompt`, optional `image`, optional `out_dir` defaulting to `"."`.
- Implement tool logic by calling the shared generation helper to avoid duplicating domain behavior.
- Return success payload with `path`, `filename`, `out_dir`, `model`, and `transport`.

## Phase 3: Define Structured MCP Error Mapping
- Add MCP-oriented error mapping from existing `CliError` messages into stable error codes (`validation_error`, `api_error`, `timeout_error`, `io_error`).
- Ensure tool failures are surfaced as structured MCP errors with `code` and `message`.
- Keep error messages actionable and consistent with current CLI messaging where possible.

## Phase 4: Expose Executable Command
- Update `pyproject.toml` to add `ez-banana-mcp = "ez_banana.mcp_server:main"` under `[project.scripts]`.
- Ensure `main()` in the MCP module runs FastMCP with `stdio` transport.
- Confirm existing `ez-banana` script entry remains unchanged.

## Phase 5: Add Unit Test Coverage
- Add a new MCP-focused test module in `tests/`.
- Cover prompt-only success result shape (path + metadata).
- Cover prompt + reference image path flow and multimodal request behavior.
- Cover structured error mapping for missing API key, invalid image path, HTTP errors, and timeout errors.
- Mock network and filesystem interactions similarly to existing test patterns.

## Phase 6: Verify and Polish
- Run full unit test suite with `uv run python -m unittest discover -s tests -v`.
- Fix any regressions in shared CLI flow or MCP tool behavior.
- Validate that the implementation matches all spec acceptance criteria and non-goals.
