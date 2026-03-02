## Project Overview

`ez-banana` is a Python app that generates images from prompts through OpenRouter, exposed as both a CLI and a FastMCP stdio server tool. Built with Python 3.14, `requests`, and FastMCP, using local filesystem output storage, and tested with `unittest`.

## Structure Map

- `main.py` - top-level local CLI entrypoint.
- `src/ez_banana/` - application package (CLI flow, shared generation logic, OpenRouter integration, MCP server, models, validation).
- `tests/` - unit tests for CLI and MCP behavior.
- `docs/` - project and MCP notes.

### Development Guide

Run `uv sync`, then execute `uv run python main.py --prompt "<prompt>"` for CLI usage or `uv run ez-banana-mcp` for MCP stdio server usage. Verify with `uv run python -m unittest discover -s tests -v` and build with `uv build`.
