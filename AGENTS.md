## Project Overview

`ez-banana` is a Python CLI that generates images through OpenRouter from a required text prompt, with optional reference-image input. Built with Python 3.14 and `requests`, using local filesystem output storage, and tested with `unittest`.

## Structure Map

- `main.py` - CLI entrypoint, input validation, OpenRouter request/response handling, and image file output.
- `tests/` - automated CLI and behavior coverage for success and error paths.
- `docs/` - project notes and iteration context docs.

### Development Guide

Use `uv run python main.py --prompt "<prompt>" [--image <path>] [--out-dir <dir>]` to run locally and `uv run python -m unittest discover -s tests -v` to verify behavior. Build distributables with `uv build`.
