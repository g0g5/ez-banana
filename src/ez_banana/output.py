from __future__ import annotations

import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from .errors import CliError


def generate_unique_output_path(
    out_dir: Path,
    *,
    now_fn: Callable[[], datetime] | None = None,
    randbelow_fn: Callable[[int], int] = secrets.randbelow,
) -> Path:
    if now_fn is None:
        now_fn = lambda: datetime.now(UTC)

    timestamp = now_fn().strftime("%Y%m%d_%H%M%S")
    while True:
        suffix = f"{randbelow_fn(100_000_000):08d}"
        output_path = out_dir / f"ezbanana_{timestamp}_{suffix}.png"
        if not output_path.exists():
            return output_path


def save_generated_image(
    image_bytes: bytes,
    out_dir: Path,
    *,
    now_fn: Callable[[], datetime] | None = None,
    randbelow_fn: Callable[[int], int] = secrets.randbelow,
) -> Path:
    output_path = generate_unique_output_path(
        out_dir,
        now_fn=now_fn,
        randbelow_fn=randbelow_fn,
    )
    try:
        output_path.write_bytes(image_bytes)
    except OSError as exc:
        raise CliError(
            f"Unable to write generated image: {output_path} ({exc})"
        ) from exc
    return output_path
