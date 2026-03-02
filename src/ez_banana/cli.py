from __future__ import annotations

import argparse
import sys

import requests

from .app import run_generation_flow
from .errors import CliError
from .openrouter import VALID_ASPECT_RATIOS, VALID_IMAGE_SIZES


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
    parser.add_argument(
        "--aspect-ratio",
        choices=VALID_ASPECT_RATIOS,
        default="1:1",
        help=f"Aspect ratio for generated image (default: 1:1). Choices: {', '.join(VALID_ASPECT_RATIOS)}",
    )
    parser.add_argument(
        "--image-size",
        choices=VALID_IMAGE_SIZES,
        default="1K",
        help=f"Resolution size for generated image (default: 1K). Choices: {', '.join(VALID_IMAGE_SIZES)}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        generation = run_generation_flow(
            prompt=args.prompt,
            image=args.image,
            out_dir=args.out_dir,
            aspect_ratio=args.aspect_ratio,
            image_size=args.image_size,
            post=requests.post,
        )
    except CliError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(generation.path)
    return 0
