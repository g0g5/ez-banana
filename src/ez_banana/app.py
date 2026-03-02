from __future__ import annotations

from typing import Any, Callable

import requests

from .config import DEFAULT_MODEL
from .models import GenerationSuccess
from .openrouter import build_openrouter_request, generate_image_from_openrouter
from .output import save_generated_image
from .validation import validate_input_values


def run_generation_flow(
    *,
    prompt: str,
    image: str | None = None,
    out_dir: str = ".",
    post: Callable[..., Any] = requests.post,
) -> GenerationSuccess:
    validated_input = validate_input_values(
        prompt=prompt,
        image=image,
        out_dir=out_dir,
    )
    openrouter_request = build_openrouter_request(validated_input)
    result = generate_image_from_openrouter(openrouter_request, post=post)
    saved_path = save_generated_image(result.image_bytes, validated_input.out_dir)

    return GenerationSuccess(
        path=saved_path,
        filename=saved_path.name,
        out_dir=validated_input.out_dir,
        model=DEFAULT_MODEL,
    )
