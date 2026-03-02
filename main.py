from __future__ import annotations

import argparse
from datetime import UTC, datetime
import secrets
import sys
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from src.ez_banana import (
    CliError,
    DEFAULT_MODEL,
    OPENROUTER_API_KEY_ENV,
    OPENROUTER_CHAT_COMPLETIONS_URL,
    REQUEST_TIMEOUT,
    SUPPORTED_REFERENCE_IMAGE_MIME_TYPES,
    OpenRouterRequest,
    OpenRouterResult,
    ValidatedInput,
)
from src.ez_banana.cli import build_parser as _build_parser
from src.ez_banana.openrouter import (
    build_openrouter_request as _build_openrouter_request,
    build_request_headers as _build_request_headers,
    build_request_payload as _build_request_payload,
    decode_image_data_url as _decode_image_data_url,
    encode_reference_image_data_url as _encode_reference_image_data_url,
    extract_image_data_url as _extract_image_data_url,
    send_openrouter_request as _send_openrouter_request,
)
from src.ez_banana.output import (
    generate_unique_output_path as _generate_unique_output_path,
    save_generated_image as _save_generated_image,
)
from src.ez_banana.validation import (
    ensure_output_directory as _ensure_output_directory,
    require_api_key as _require_api_key,
    validate_inputs as _validate_inputs,
    validate_prompt as _validate_prompt,
    validate_reference_image as _validate_reference_image,
)


def build_parser() -> argparse.ArgumentParser:
    return _build_parser()


def require_api_key() -> str:
    return _require_api_key()


def validate_prompt(prompt: str) -> str:
    return _validate_prompt(prompt)


def validate_reference_image(image_value: str | None) -> tuple[Path | None, str | None]:
    return _validate_reference_image(image_value)


def ensure_output_directory(out_dir_value: str) -> Path:
    return _ensure_output_directory(out_dir_value)


def validate_inputs(args: argparse.Namespace) -> ValidatedInput:
    return _validate_inputs(args)


def build_request_headers(api_key: str) -> dict[str, str]:
    return _build_request_headers(api_key)


def encode_reference_image_data_url(image_path: Path, image_mime_type: str) -> str:
    return _encode_reference_image_data_url(image_path, image_mime_type)


def build_request_payload(validated: ValidatedInput) -> dict[str, Any]:
    return _build_request_payload(validated)


def build_openrouter_request(validated: ValidatedInput) -> OpenRouterRequest:
    return _build_openrouter_request(validated)


def send_openrouter_request(openrouter_request: OpenRouterRequest) -> dict[str, Any]:
    return _send_openrouter_request(openrouter_request, post=requests.post)


def extract_image_data_url(response_json: dict[str, Any]) -> str:
    return _extract_image_data_url(response_json)


def decode_image_data_url(image_data_url: str) -> bytes:
    return _decode_image_data_url(image_data_url)


def generate_image_from_openrouter(
    openrouter_request: OpenRouterRequest,
) -> OpenRouterResult:
    response_json = send_openrouter_request(openrouter_request)
    image_data_url = extract_image_data_url(response_json)
    image_bytes = decode_image_data_url(image_data_url)
    return OpenRouterResult(image_bytes=image_bytes, image_data_url=image_data_url)


def generate_unique_output_path(out_dir: Path) -> Path:
    return _generate_unique_output_path(
        out_dir,
        now_fn=lambda: datetime.now(UTC),
        randbelow_fn=secrets.randbelow,
    )


def save_generated_image(image_bytes: bytes, out_dir: Path) -> Path:
    return _save_generated_image(
        image_bytes,
        out_dir,
        now_fn=lambda: datetime.now(UTC),
        randbelow_fn=secrets.randbelow,
    )


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
