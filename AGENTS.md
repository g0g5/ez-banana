## Project Overview

`ez-banana` is a Python CLI that generates images through OpenRouter from a required text prompt, with optional reference-image input. Built with Python 3.14 and `requests`, using local filesystem output storage, and tested with `unittest`.

## Structure Map

- `main.py` - thin CLI entrypoint/orchestrator that delegates to `src/ez_banana` modules.
- `src/ez_banana/` - core application package.
- `src/ez_banana/cli.py` - argparse CLI definition.
- `src/ez_banana/validation.py` - environment and input validation.
- `src/ez_banana/openrouter.py` - OpenRouter request/response handling and image data URL decoding.
- `src/ez_banana/output.py` - generated filename creation and image file writing.
- `src/ez_banana/models.py` - dataclass models used across modules.
- `src/ez_banana/config.py` - constants and configuration values.
- `src/ez_banana/errors.py` - shared CLI error types.
- `tests/` - automated CLI and behavior coverage for success and error paths.
- `docs/` - project notes and iteration context docs.

### Development Guide

Use `uv run python main.py --prompt "<prompt>" [--image <path>] [--out-dir <dir>]` to run locally and `uv run python -m unittest discover -s tests -v` to verify behavior. Build distributables with `uv build`.
