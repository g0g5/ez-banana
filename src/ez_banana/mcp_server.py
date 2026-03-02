from __future__ import annotations

import json

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

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


@mcp.tool
def generate_image(
    prompt: str,
    image: str | None = None,
    out_dir: str = ".",
) -> dict[str, str]:
    try:
        generation = run_generation_flow(prompt=prompt, image=image, out_dir=out_dir)
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
