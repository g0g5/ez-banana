from __future__ import annotations

import json
from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from .app import run_generation_flow
from .errors import CliError

mcp = FastMCP("ez-banana")


def map_cli_error_to_mcp_payload(error: CliError) -> dict[str, str]:
    message = str(error)
    normalized = message.lower()

    if "timed out" in normalized:
        code = "timeout_error"
    elif normalized.startswith("openrouter ") or normalized.startswith(
        "generated image"
    ):
        code = "api_error"
    elif (
        normalized.startswith("unable to create output directory")
        or normalized.startswith("unable to write generated image")
        or normalized.startswith("reference image is not readable")
        or normalized.startswith("unable to read reference image bytes")
    ):
        code = "io_error"
    elif (
        normalized.startswith("missing api key")
        or normalized.startswith("--prompt must")
        or normalized.startswith("reference image not found")
        or normalized.startswith("unsupported reference image type")
        or normalized.startswith("output path is not a directory")
    ):
        code = "validation_error"
    else:
        code = "api_error"

    return {"code": code, "message": message}


@mcp.tool()
def generate_image(
    prompt: str,
    image: str | None = None,
    out_dir: str = ".",
    aspect_ratio: Annotated[
        Literal[
            "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
        ],
        Field(description="Aspect ratio for generated image", default="1:1"),
    ] = "1:1",
    image_size: Annotated[
        Literal["1K", "2K", "4K"],
        Field(description="Resolution size for generated image", default="1K"),
    ] = "1K",
) -> dict[str, str]:
    """Generate an image from a text prompt using OpenRouter.

    Args:
        prompt: Text description of the image to generate
        image: Optional path to a reference image for image-to-image generation
        out_dir: Directory where the generated image will be saved (default: current directory)
        aspect_ratio: Aspect ratio for the generated image (default: 1:1)
        image_size: Resolution size for the generated image (default: 1K)
    """
    try:
        generation = run_generation_flow(
            prompt=prompt,
            image=image,
            out_dir=out_dir,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        )
    except CliError as exc:
        error_payload = map_cli_error_to_mcp_payload(exc)
        raise ToolError(json.dumps(error_payload)) from exc

    return {
        "path": str(generation.path),
        "filename": generation.filename,
        "out_dir": str(generation.out_dir),
        "model": generation.model,
        "transport": "stdio",
    }


def main() -> None:
    mcp.run(transport="stdio")
