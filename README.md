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

## Test

```bash
uv run python -m unittest discover -s tests -v
```

## Build

```bash
uv build
```
