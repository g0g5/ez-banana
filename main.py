from __future__ import annotations

import argparse
import base64
import binascii
from datetime import UTC, datetime
import mimetypes
import os
import secrets
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-2.5-flash-image-preview"
REQUEST_TIMEOUT: tuple[float, float] = (3.05, 60.0)
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"
SUPPORTED_REFERENCE_IMAGE_MIME_TYPES = frozenset(
    {
        "image/bmp",
        "image/gif",
        "image/jpeg",
        "image/png",
        "image/tiff",
        "image/webp",
    }
)


class CliError(Exception):
    pass


@dataclass(frozen=True)
class ValidatedInput:
    api_key: str
    prompt: str
    image_path: Path | None
    image_mime_type: str | None
    out_dir: Path


@dataclass(frozen=True)
class OpenRouterRequest:
    headers: dict[str, str]
    payload: dict[str, Any]


@dataclass(frozen=True)
class OpenRouterResult:
    image_bytes: bytes
    image_data_url: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ez-banana",
        description="Generate images with OpenRouter from a text prompt.",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Text prompt to generate an image from.",
    )
    parser.add_argument(
        "--image",
        help="Optional local reference image path.",
    )
    parser.add_argument(
        "--out-dir",
        default=".",
        help="Output directory for generated image files (default: current directory).",
    )
    return parser


def require_api_key() -> str:
    api_key = os.getenv(OPENROUTER_API_KEY_ENV, "").strip()
    if not api_key:
        raise CliError(
            f"Missing API key. Set {OPENROUTER_API_KEY_ENV} in your environment."
        )
    return api_key


def validate_prompt(prompt: str) -> str:
    trimmed_prompt = prompt.strip()
    if not trimmed_prompt:
        raise CliError("--prompt must be non-empty.")
    return trimmed_prompt


def validate_reference_image(image_value: str | None) -> tuple[Path | None, str | None]:
    if not image_value:
        return None, None

    image_path = Path(image_value)
    if not image_path.exists() or not image_path.is_file():
        raise CliError(f"Reference image not found: {image_path}")

    try:
        with image_path.open("rb"):
            pass
    except OSError as exc:
        raise CliError(
            f"Reference image is not readable: {image_path} ({exc})"
        ) from exc

    guessed_mime_type, _ = mimetypes.guess_type(str(image_path))
    if guessed_mime_type not in SUPPORTED_REFERENCE_IMAGE_MIME_TYPES:
        supported_types = ", ".join(sorted(SUPPORTED_REFERENCE_IMAGE_MIME_TYPES))
        raise CliError(
            "Unsupported reference image type. "
            f"Detected: {guessed_mime_type or 'unknown'}. "
            f"Supported: {supported_types}."
        )

    return image_path, guessed_mime_type


def ensure_output_directory(out_dir_value: str) -> Path:
    out_dir = Path(out_dir_value)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise CliError(f"Unable to create output directory: {out_dir} ({exc})") from exc

    if not out_dir.is_dir():
        raise CliError(f"Output path is not a directory: {out_dir}")

    return out_dir


def validate_inputs(args: argparse.Namespace) -> ValidatedInput:
    api_key = require_api_key()
    prompt = validate_prompt(args.prompt)
    image_path, image_mime_type = validate_reference_image(args.image)
    out_dir = ensure_output_directory(args.out_dir)
    return ValidatedInput(
        api_key=api_key,
        prompt=prompt,
        image_path=image_path,
        image_mime_type=image_mime_type,
        out_dir=out_dir,
    )


def build_request_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def encode_reference_image_data_url(image_path: Path, image_mime_type: str) -> str:
    try:
        image_bytes = image_path.read_bytes()
    except OSError as exc:
        raise CliError(
            f"Unable to read reference image bytes: {image_path} ({exc})"
        ) from exc

    encoded_payload = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{image_mime_type};base64,{encoded_payload}"


def build_request_payload(validated: ValidatedInput) -> dict[str, Any]:
    if validated.image_path and validated.image_mime_type:
        reference_image_data_url = encode_reference_image_data_url(
            image_path=validated.image_path,
            image_mime_type=validated.image_mime_type,
        )
        message_content: str | list[dict[str, Any]] = [
            {"type": "text", "text": validated.prompt},
            {
                "type": "image_url",
                "image_url": {"url": reference_image_data_url},
            },
        ]
    else:
        message_content = validated.prompt

    return {
        "model": DEFAULT_MODEL,
        "modalities": ["image", "text"],
        "messages": [{"role": "user", "content": message_content}],
    }


def build_openrouter_request(validated: ValidatedInput) -> OpenRouterRequest:
    return OpenRouterRequest(
        headers=build_request_headers(validated.api_key),
        payload=build_request_payload(validated),
    )


def send_openrouter_request(openrouter_request: OpenRouterRequest) -> dict[str, Any]:
    try:
        response = requests.post(
            OPENROUTER_CHAT_COMPLETIONS_URL,
            headers=openrouter_request.headers,
            json=openrouter_request.payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise CliError(
            "Request to OpenRouter timed out. Try again or increase timeout settings."
        ) from exc
    except requests.exceptions.HTTPError as exc:
        status_code = (
            exc.response.status_code if exc.response is not None else "unknown"
        )
        details = ""
        if exc.response is not None:
            try:
                error_payload = exc.response.json()
            except ValueError:
                error_payload = None

            if isinstance(error_payload, dict):
                message = error_payload.get("error", {}).get("message")
                if isinstance(message, str) and message.strip():
                    details = f" Details: {message.strip()}"
        raise CliError(
            f"OpenRouter API request failed (HTTP {status_code}).{details}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise CliError(f"OpenRouter API request failed: {exc}") from exc

    try:
        response_json = response.json()
    except ValueError as exc:
        raise CliError("OpenRouter response was not valid JSON.") from exc

    if not isinstance(response_json, dict):
        raise CliError("OpenRouter response JSON has unexpected format.")

    return response_json


def extract_image_data_url(response_json: dict[str, Any]) -> str:
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        raise CliError("OpenRouter response missing choices data.")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise CliError("OpenRouter response choice has unexpected format.")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise CliError("OpenRouter response missing message payload.")

    images = message.get("images")
    if not isinstance(images, list) or not images:
        raise CliError("OpenRouter response did not include generated images.")

    first_image = images[0]
    if not isinstance(first_image, dict):
        raise CliError("OpenRouter response image entry has unexpected format.")

    image_url = first_image.get("image_url")
    if not isinstance(image_url, dict):
        raise CliError("OpenRouter response missing image_url object.")

    data_url = image_url.get("url")
    if not isinstance(data_url, str) or not data_url.strip():
        raise CliError("OpenRouter response missing generated image URL.")

    return data_url


def decode_image_data_url(image_data_url: str) -> bytes:
    if not image_data_url.startswith("data:"):
        raise CliError("Generated image URL is not a data URL.")
    if "," not in image_data_url:
        raise CliError("Generated image data URL is malformed.")

    header, encoded_payload = image_data_url.split(",", 1)
    if ";base64" not in header:
        raise CliError("Generated image data URL is not base64-encoded.")

    try:
        image_bytes = base64.b64decode(encoded_payload, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise CliError(
            "Generated image data URL contained invalid base64 data."
        ) from exc

    if not image_bytes:
        raise CliError("Generated image content was empty.")

    return image_bytes


def generate_image_from_openrouter(
    openrouter_request: OpenRouterRequest,
) -> OpenRouterResult:
    response_json = send_openrouter_request(openrouter_request)
    image_data_url = extract_image_data_url(response_json)
    image_bytes = decode_image_data_url(image_data_url)
    return OpenRouterResult(image_bytes=image_bytes, image_data_url=image_data_url)


def generate_unique_output_path(out_dir: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    while True:
        suffix = f"{secrets.randbelow(100_000_000):08d}"
        output_path = out_dir / f"ezbanana_{timestamp}_{suffix}.png"
        if not output_path.exists():
            return output_path


def save_generated_image(image_bytes: bytes, out_dir: Path) -> Path:
    output_path = generate_unique_output_path(out_dir)
    try:
        output_path.write_bytes(image_bytes)
    except OSError as exc:
        raise CliError(
            f"Unable to write generated image: {output_path} ({exc})"
        ) from exc
    return output_path


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        validated_input = validate_inputs(args)
        openrouter_request = build_openrouter_request(validated_input)
        result = generate_image_from_openrouter(openrouter_request)
        saved_path = save_generated_image(result.image_bytes, validated_input.out_dir)
    except CliError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(saved_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
