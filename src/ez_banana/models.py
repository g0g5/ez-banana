from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ValidatedInput:
    api_key: str
    prompt: str
    image_path: Path | None
    image_mime_type: str | None
    out_dir: Path


@dataclass(frozen=True)
class OpenRouterRequest:
    headers: dict[str, str]
    payload: dict[str, Any]


@dataclass(frozen=True)
class OpenRouterResult:
    image_bytes: bytes
    image_data_url: str


@dataclass(frozen=True)
class GenerationSuccess:
    path: Path
    filename: str
    out_dir: Path
    model: str
