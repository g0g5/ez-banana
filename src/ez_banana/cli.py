from __future__ import annotations

import argparse
import sys

import requests

from .app import run_generation_flow
from .errors import CliError


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
        generation = run_generation_flow(
            prompt=args.prompt,
            image=args.image,
            out_dir=args.out_dir,
            post=requests.post,
        )
    except CliError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(generation.path)
    return 0
