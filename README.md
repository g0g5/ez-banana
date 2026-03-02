# ez-banana

`ez-banana` is a small Python CLI that generates an image from a required text prompt using OpenRouter, with optional reference-image input.

## Requirements

- Python 3.14+
- An OpenRouter API key

## Setup

```bash
uv sync
```

Set your API key:

```bash
export OPENROUTER_API_KEY="your_api_key_here"
```

On PowerShell:

```powershell
$env:OPENROUTER_API_KEY="your_api_key_here"
```

## Usage

Run via the project entrypoint:

```bash
uv run python main.py --prompt "a banana-shaped spaceship"
```

With a reference image and custom output directory:

```bash
uv run python main.py --prompt "retro comic style" --image ./ref.png --out-dir ./generated
```

### CLI flags

- `--prompt` (required): Text prompt for generation
- `--image` (optional): Local reference image (`bmp`, `gif`, `jpeg`, `png`, `tiff`, `webp`)
- `--out-dir` (optional): Output directory (default: current directory)

On success, the CLI prints the saved image path and exits with code `0`. Errors are printed to stderr and exit with code `1`.

## MCP Usage (stdio)

`ez-banana` also exposes an MCP server over stdio.

Start the server:

```bash
uv run ez-banana-mcp
```

### Tool

- `generate_image(prompt, image=None, out_dir=".")`
  - `prompt` (required): Text prompt for generation
  - `image` (optional): Local reference image path
  - `out_dir` (optional): Output directory (default: current directory)

Successful response shape:

```json
{
  "path": "generated/image.png",
  "filename": "image.png",
  "out_dir": "generated",
  "model": "...",
  "transport": "stdio"
}
```

Tool errors are returned with JSON payloads containing:

- `code`: one of `timeout_error`, `api_error`, `io_error`, `validation_error`
- `message`: human-readable error details

## Test

```bash
uv run python -m unittest discover -s tests -v
```

## Build

```bash
uv build
```
