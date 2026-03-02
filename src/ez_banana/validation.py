from __future__ import annotations

import argparse
import mimetypes
import os
from pathlib import Path

from .config import OPENROUTER_API_KEY_ENV, SUPPORTED_REFERENCE_IMAGE_MIME_TYPES
from .errors import CliError
from .models import ValidatedInput


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
    return validate_input_values(
        prompt=args.prompt,
        image=args.image,
        out_dir=args.out_dir,
    )


def validate_input_values(
    *, prompt: str, image: str | None, out_dir: str
) -> ValidatedInput:
    api_key = require_api_key()
    validated_prompt = validate_prompt(prompt)
    image_path, image_mime_type = validate_reference_image(image)
    validated_out_dir = ensure_output_directory(out_dir)
    return ValidatedInput(
        api_key=api_key,
        prompt=validated_prompt,
        image_path=image_path,
        image_mime_type=image_mime_type,
        out_dir=validated_out_dir,
    )
