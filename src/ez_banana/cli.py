from __future__ import annotations

import argparse


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
