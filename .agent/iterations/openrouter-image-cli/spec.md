# Iteration Spec: openrouter-image-cli

## Goal
Build a simple Python 3.14 CLI client (managed by `uv`) for OpenRouter image generation using `requests`, with optional reference-image input.

## Confirmed Requirements
- Runtime: Python 3.14, dependency management and run workflow via `uv`.
- HTTP client: `requests`.
- CLI input:
  - `--prompt` (required text prompt).
  - `--image` (optional local reference image path).
  - `--out-dir` (optional output directory; default is current directory `.`).
- API key source: `OPENROUTER_API_KEY` environment variable.
- Default model: use the model shown in OpenRouter basic image-generation docs example (currently `google/gemini-2.5-flash-image-preview`, configurable in a code constant).
- Output file naming: `ezbanana_<timestamp>_<8-digit random string>.png`.
- Collision handling: regenerate random suffix and retry until a unique filename is created.

## External Dependencies
- `requests` (required)

## Library Research Notes (Implementation-Focused)
From latest `requests` docs and OpenRouter multimodal docs:

```python
resp = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json=payload,
    timeout=(3.05, 60),
)
resp.raise_for_status()
data = resp.json()
```

```python
# Save image from OpenRouter data URL
header, b64 = image_data_url.split(",", 1)
image_bytes = base64.b64decode(b64)
Path(output_path).write_bytes(image_bytes)
```

```python
try:
    resp = requests.post(url, headers=headers, json=payload, timeout=(3.05, 60))
    resp.raise_for_status()
except requests.exceptions.Timeout:
    ...
except requests.exceptions.HTTPError as e:
    ...
except requests.exceptions.RequestException:
    ...
```

## API Interaction Spec
- Endpoint: `POST https://openrouter.ai/api/v1/chat/completions`
- Headers:
  - `Authorization: Bearer <OPENROUTER_API_KEY>`
  - `Content-Type: application/json`
- Request body:
  - `model`: default model constant (doc example model)
  - `modalities`: for default Gemini text+image output, send `['image', 'text']` (image-only models may use `['image']`)
  - `messages`:
    - Without `--image`: user message with string prompt content
    - With `--image`: user message `content` must be an array with a text item first, then an image item:
      - `{ "type": "text", "text": "<prompt>" }`
      - `{ "type": "image_url", "image_url": { "url": "data:<mime>;base64,<payload>" } }`
- Response parsing:
  - Read generated image from `choices[0].message.images[0].image_url.url` (data URL)
  - Decode base64 payload and save as `.png`

## CLI Behavior
- Validate `OPENROUTER_API_KEY` exists; fail fast with clear error if missing.
- Validate `--prompt` is non-empty.
- If `--image` is provided, verify file exists and is readable; infer MIME type (`image/png`, `image/jpeg`, etc.) before constructing data URL.
- Create `--out-dir` if it does not exist.
- Generate filename:
  - `timestamp`: UTC format `YYYYMMDD_HHMMSS`
  - random suffix: 8 numeric digits (`00000000`-`99999999`)
- Print final saved file path on success.

## Non-Goals
- No GUI/web interface.
- No batch generation in this iteration.
- No advanced model parameter tuning flags (size/seed/steps/etc.) beyond core prompt + optional reference image.

## Acceptance Criteria
- Running CLI with `--prompt` and valid env key saves one generated image with required naming format.
- Running CLI with both `--prompt` and `--image` successfully sends reference image and saves output.
- Missing env key, invalid image path, API errors, and timeouts return actionable error messages and non-zero exit code.
- Output defaults to current directory, and `--out-dir` overrides it.
