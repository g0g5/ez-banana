from __future__ import annotations

import argparse
import sys

import requests

from .errors import CliError
from .openrouter import build_openrouter_request, generate_image_from_openrouter
from .output import save_generated_image
from .validation import validate_inputs


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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        validated_input = validate_inputs(args)
        openrouter_request = build_openrouter_request(validated_input)
        result = generate_image_from_openrouter(openrouter_request, post=requests.post)
        saved_path = save_generated_image(result.image_bytes, validated_input.out_dir)
    except CliError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(saved_path)
    return 0
