from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import requests
from fastmcp.exceptions import ToolError

from src.ez_banana import app
from src.ez_banana import config
from src.ez_banana import mcp_server


class FakeResponse:
    def __init__(self, payload: dict, *, http_error: Exception | None = None) -> None:
        self._payload = payload
        self._http_error = http_error

    def raise_for_status(self) -> None:
        if self._http_error is not None:
            raise self._http_error

    def json(self) -> dict:
        return self._payload


class McpServerTests(unittest.TestCase):
    def assert_tool_error(self, exc: ToolError, expected_code: str) -> dict[str, str]:
        payload = json.loads(str(exc))
        self.assertEqual(payload["code"], expected_code)
        self.assertIsInstance(payload["message"], str)
        self.assertTrue(payload["message"])
        return payload

    def test_prompt_only_returns_saved_path_and_metadata(self) -> None:
        image_data_url = "data:image/png;base64," + base64.b64encode(
            b"mcp-bytes"
        ).decode("ascii")

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)

            def fake_post(*args, **kwargs):
                self.assertEqual(args[0], config.OPENROUTER_CHAT_COMPLETIONS_URL)
                self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
                self.assertEqual(kwargs["json"]["modalities"], ["image", "text"])
                self.assertEqual(kwargs["json"]["messages"][0]["content"], "a banana")
                return FakeResponse(
                    {
                        "choices": [
                            {
                                "message": {
                                    "images": [{"image_url": {"url": image_data_url}}]
                                }
                            }
                        ]
                    }
                )

            def run_flow_with_fake_post(
                *, prompt: str, image: str | None, out_dir: str
            ):
                return app.run_generation_flow(
                    prompt=prompt,
                    image=image,
                    out_dir=out_dir,
                    post=fake_post,
                )

            with (
                patch.dict(
                    os.environ, {config.OPENROUTER_API_KEY_ENV: "test-key"}, clear=False
                ),
                patch(
                    "src.ez_banana.mcp_server.run_generation_flow",
                    side_effect=run_flow_with_fake_post,
                ),
            ):
                result = mcp_server.generate_image(
                    prompt="a banana", out_dir=str(out_dir)
                )

            saved_path = Path(result["path"])
            self.assertTrue(saved_path.exists())
            self.assertEqual(result["filename"], saved_path.name)
            self.assertEqual(Path(result["out_dir"]).resolve(), out_dir.resolve())
            self.assertEqual(result["model"], config.DEFAULT_MODEL)
            self.assertEqual(result["transport"], "stdio")

    def test_prompt_with_image_builds_multimodal_request(self) -> None:
        generated_data_url = "data:image/png;base64," + base64.b64encode(
            b"generated-bytes"
        ).decode("ascii")

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            reference_image = temp_path / "ref.png"
            reference_image.write_bytes(b"reference-bytes")
            out_dir = temp_path / "generated"

            def fake_post(*args, **kwargs):
                self.assertEqual(args[0], config.OPENROUTER_CHAT_COMPLETIONS_URL)
                content = kwargs["json"]["messages"][0]["content"]
                self.assertIsInstance(content, list)
                self.assertEqual(content[0]["type"], "text")
                self.assertEqual(content[0]["text"], "with ref")
                self.assertEqual(content[1]["type"], "image_url")
                self.assertTrue(
                    content[1]["image_url"]["url"].startswith("data:image/png;base64,")
                )
                return FakeResponse(
                    {
                        "choices": [
                            {
                                "message": {
                                    "images": [
                                        {"image_url": {"url": generated_data_url}}
                                    ]
                                }
                            }
                        ]
                    }
                )

            def run_flow_with_fake_post(
                *, prompt: str, image: str | None, out_dir: str
            ):
                return app.run_generation_flow(
                    prompt=prompt,
                    image=image,
                    out_dir=out_dir,
                    post=fake_post,
                )

            with (
                patch.dict(
                    os.environ, {config.OPENROUTER_API_KEY_ENV: "test-key"}, clear=False
                ),
                patch(
                    "src.ez_banana.mcp_server.run_generation_flow",
                    side_effect=run_flow_with_fake_post,
                ),
            ):
                result = mcp_server.generate_image(
                    prompt="with ref",
                    image=str(reference_image),
                    out_dir=str(out_dir),
                )

            self.assertTrue(Path(result["path"]).exists())
            self.assertEqual(Path(result["out_dir"]).resolve(), out_dir.resolve())

    def test_missing_api_key_maps_to_validation_error(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(config.OPENROUTER_API_KEY_ENV, None)
            with self.assertRaises(ToolError) as ctx:
                mcp_server.generate_image(prompt="x")

        payload = self.assert_tool_error(ctx.exception, "validation_error")
        self.assertIn("Missing API key", payload["message"])

    def test_invalid_image_path_maps_to_validation_error(self) -> None:
        with patch.dict(
            os.environ, {config.OPENROUTER_API_KEY_ENV: "test-key"}, clear=False
        ):
            with self.assertRaises(ToolError) as ctx:
                mcp_server.generate_image(prompt="x", image="not-real.png")

        payload = self.assert_tool_error(ctx.exception, "validation_error")
        self.assertIn("Reference image not found", payload["message"])

    def test_http_error_maps_to_api_error(self) -> None:
        error_response = requests.Response()
        error_response.status_code = 401
        error_response._content = b'{"error":{"message":"Invalid API key"}}'
        error_response.headers["Content-Type"] = "application/json"
        http_error = requests.exceptions.HTTPError(response=error_response)

        def fake_post(*_args, **_kwargs):
            return FakeResponse({}, http_error=http_error)

        def run_flow_with_http_error(*, prompt: str, image: str | None, out_dir: str):
            return app.run_generation_flow(
                prompt=prompt,
                image=image,
                out_dir=out_dir,
                post=fake_post,
            )

        with (
            patch.dict(
                os.environ, {config.OPENROUTER_API_KEY_ENV: "test-key"}, clear=False
            ),
            patch(
                "src.ez_banana.mcp_server.run_generation_flow",
                side_effect=run_flow_with_http_error,
            ),
        ):
            with self.assertRaises(ToolError) as ctx:
                mcp_server.generate_image(prompt="x")

        payload = self.assert_tool_error(ctx.exception, "api_error")
        self.assertIn("HTTP 401", payload["message"])

    def test_timeout_maps_to_timeout_error(self) -> None:
        def fake_post(*_args, **_kwargs):
            raise requests.exceptions.Timeout("timed out")

        def run_flow_with_timeout(*, prompt: str, image: str | None, out_dir: str):
            return app.run_generation_flow(
                prompt=prompt,
                image=image,
                out_dir=out_dir,
                post=fake_post,
            )

        with (
            patch.dict(
                os.environ, {config.OPENROUTER_API_KEY_ENV: "test-key"}, clear=False
            ),
            patch(
                "src.ez_banana.mcp_server.run_generation_flow",
                side_effect=run_flow_with_timeout,
            ),
        ):
            with self.assertRaises(ToolError) as ctx:
                mcp_server.generate_image(prompt="x")

        payload = self.assert_tool_error(ctx.exception, "timeout_error")
        self.assertIn("timed out", payload["message"].lower())


if __name__ == "__main__":
    unittest.main()
