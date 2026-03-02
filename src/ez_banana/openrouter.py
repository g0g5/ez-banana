from __future__ import annotations

import base64
import binascii
from pathlib import Path
from typing import Any, Callable

import requests

from .config import DEFAULT_MODEL, OPENROUTER_CHAT_COMPLETIONS_URL, REQUEST_TIMEOUT
from .errors import CliError
from .models import OpenRouterRequest, OpenRouterResult, ValidatedInput


def build_request_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def encode_reference_image_data_url(image_path: Path, image_mime_type: str) -> str:
    try:
        image_bytes = image_path.read_bytes()
    except OSError as exc:
        raise CliError(
            f"Unable to read reference image bytes: {image_path} ({exc})"
        ) from exc

    encoded_payload = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{image_mime_type};base64,{encoded_payload}"


def build_request_payload(validated: ValidatedInput) -> dict[str, Any]:
    if validated.image_path and validated.image_mime_type:
        reference_image_data_url = encode_reference_image_data_url(
            image_path=validated.image_path,
            image_mime_type=validated.image_mime_type,
        )
        message_content: str | list[dict[str, Any]] = [
            {"type": "text", "text": validated.prompt},
            {
                "type": "image_url",
                "image_url": {"url": reference_image_data_url},
            },
        ]
    else:
        message_content = validated.prompt

    return {
        "model": DEFAULT_MODEL,
        "modalities": ["image", "text"],
        "messages": [{"role": "user", "content": message_content}],
    }


def build_openrouter_request(validated: ValidatedInput) -> OpenRouterRequest:
    return OpenRouterRequest(
        headers=build_request_headers(validated.api_key),
        payload=build_request_payload(validated),
    )


def send_openrouter_request(
    openrouter_request: OpenRouterRequest,
    *,
    post: Callable[..., Any] = requests.post,
) -> dict[str, Any]:
    try:
        response = post(
            OPENROUTER_CHAT_COMPLETIONS_URL,
            headers=openrouter_request.headers,
            json=openrouter_request.payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise CliError(
            "Request to OpenRouter timed out. Try again or increase timeout settings."
        ) from exc
    except requests.exceptions.HTTPError as exc:
        status_code = (
            exc.response.status_code if exc.response is not None else "unknown"
        )
        details = ""
        if exc.response is not None:
            try:
                error_payload = exc.response.json()
            except ValueError:
                error_payload = None

            if isinstance(error_payload, dict):
                message = error_payload.get("error", {}).get("message")
                if isinstance(message, str) and message.strip():
                    details = f" Details: {message.strip()}"
        raise CliError(
            f"OpenRouter API request failed (HTTP {status_code}).{details}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise CliError(f"OpenRouter API request failed: {exc}") from exc

    try:
        response_json = response.json()
    except ValueError as exc:
        raise CliError("OpenRouter response was not valid JSON.") from exc

    if not isinstance(response_json, dict):
        raise CliError("OpenRouter response JSON has unexpected format.")

    return response_json


def extract_image_data_url(response_json: dict[str, Any]) -> str:
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        raise CliError("OpenRouter response missing choices data.")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise CliError("OpenRouter response choice has unexpected format.")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise CliError("OpenRouter response missing message payload.")

    images = message.get("images")
    if not isinstance(images, list) or not images:
        raise CliError("OpenRouter response did not include generated images.")

    first_image = images[0]
    if not isinstance(first_image, dict):
        raise CliError("OpenRouter response image entry has unexpected format.")

    image_url = first_image.get("image_url")
    if not isinstance(image_url, dict):
        raise CliError("OpenRouter response missing image_url object.")

    data_url = image_url.get("url")
    if not isinstance(data_url, str) or not data_url.strip():
        raise CliError("OpenRouter response missing generated image URL.")

    return data_url


def decode_image_data_url(image_data_url: str) -> bytes:
    if not image_data_url.startswith("data:"):
        raise CliError("Generated image URL is not a data URL.")
    if "," not in image_data_url:
        raise CliError("Generated image data URL is malformed.")

    header, encoded_payload = image_data_url.split(",", 1)
    if ";base64" not in header:
        raise CliError("Generated image data URL is not base64-encoded.")

    try:
        image_bytes = base64.b64decode(encoded_payload, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise CliError(
            "Generated image data URL contained invalid base64 data."
        ) from exc

    if not image_bytes:
        raise CliError("Generated image content was empty.")

    return image_bytes


def generate_image_from_openrouter(
    openrouter_request: OpenRouterRequest,
    *,
    post: Callable[..., Any] = requests.post,
) -> OpenRouterResult:
    response_json = send_openrouter_request(openrouter_request, post=post)
    image_data_url = extract_image_data_url(response_json)
    image_bytes = decode_image_data_url(image_data_url)
    return OpenRouterResult(image_bytes=image_bytes, image_data_url=image_data_url)
