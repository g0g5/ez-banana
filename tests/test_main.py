from __future__ import annotations

import base64
from datetime import UTC, datetime
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import requests

import main as cli


class FakeResponse:
    def __init__(self, payload: dict, *, http_error: Exception | None = None) -> None:
        self._payload = payload
        self._http_error = http_error

    def raise_for_status(self) -> None:
        if self._http_error is not None:
            raise self._http_error

    def json(self) -> dict:
        return self._payload


class OpenRouterCliTests(unittest.TestCase):
    def run_main(self, argv: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.dict(
            os.environ,
            {cli.OPENROUTER_API_KEY_ENV: "test-key"},
            clear=False,
        ):
            with (
                patch("main.load_dotenv", return_value=False),
                patch("sys.stdout", stdout),
                patch("sys.stderr", stderr),
            ):
                code = cli.main(argv)
        return code, stdout.getvalue().strip(), stderr.getvalue().strip()

    def test_prompt_only_uses_current_directory_default(self) -> None:
        image_data_url = "data:image/png;base64," + base64.b64encode(
            b"png-bytes"
        ).decode("ascii")
        response = FakeResponse(
            {
                "choices": [
                    {"message": {"images": [{"image_url": {"url": image_data_url}}]}}
                ]
            }
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            previous_cwd = Path.cwd()
            os.chdir(tmp_dir)
            try:
                with patch("main.requests.post", return_value=response):
                    code, stdout, stderr = self.run_main(["--prompt", "a cat"])
            finally:
                os.chdir(previous_cwd)

            self.assertEqual(code, 0)
            self.assertEqual(stderr, "")
            saved_path = (Path(tmp_dir) / stdout).resolve()
            self.assertTrue(saved_path.exists())
            self.assertEqual(saved_path.parent.resolve(), Path(tmp_dir).resolve())
            self.assertRegex(saved_path.name, r"^ezbanana_\d{8}_\d{6}_\d{8}\.png$")

    def test_prompt_with_reference_image_builds_multimodal_payload(self) -> None:
        generated_data_url = "data:image/png;base64," + base64.b64encode(
            b"result-bytes"
        ).decode("ascii")
        image_bytes = b"reference-bytes"

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            reference_image = temp_path / "ref.png"
            reference_image.write_bytes(image_bytes)

            out_dir = temp_path / "generated"

            def fake_post(*args, **kwargs):
                self.assertEqual(args[0], cli.OPENROUTER_CHAT_COMPLETIONS_URL)
                self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
                self.assertEqual(kwargs["json"]["modalities"], ["image", "text"])

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

            with patch("main.requests.post", side_effect=fake_post):
                code, stdout, stderr = self.run_main(
                    [
                        "--prompt",
                        "with ref",
                        "--image",
                        str(reference_image),
                        "--out-dir",
                        str(out_dir),
                    ]
                )

            self.assertEqual(code, 0)
            self.assertEqual(stderr, "")
            saved_path = Path(stdout)
            self.assertTrue(saved_path.exists())
            self.assertEqual(saved_path.parent.resolve(), out_dir.resolve())

    def test_missing_api_key_returns_actionable_error(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(cli.OPENROUTER_API_KEY_ENV, None)
            with (
                patch("main.load_dotenv", return_value=False),
                patch("sys.stdout", stdout),
                patch("sys.stderr", stderr),
            ):
                code = cli.main(["--prompt", "x"])

        self.assertEqual(code, 1)
        self.assertIn("Missing API key", stderr.getvalue())

    def test_invalid_image_path_returns_actionable_error(self) -> None:
        code, _stdout, stderr = self.run_main(
            ["--prompt", "x", "--image", "not-real.png"]
        )
        self.assertEqual(code, 1)
        self.assertIn("Reference image not found", stderr)

    def test_http_error_returns_actionable_error(self) -> None:
        error_response = requests.Response()
        error_response.status_code = 401
        error_response._content = b'{"error":{"message":"Invalid API key"}}'
        error_response.headers["Content-Type"] = "application/json"
        http_error = requests.exceptions.HTTPError(response=error_response)
        response = FakeResponse({}, http_error=http_error)

        with patch("main.requests.post", return_value=response):
            code, _stdout, stderr = self.run_main(["--prompt", "x"])

        self.assertEqual(code, 1)
        self.assertIn("HTTP 401", stderr)
        self.assertIn("Invalid API key", stderr)

    def test_timeout_returns_actionable_error(self) -> None:
        with patch(
            "main.requests.post",
            side_effect=requests.exceptions.Timeout("timed out"),
        ):
            code, _stdout, stderr = self.run_main(["--prompt", "x"])

        self.assertEqual(code, 1)
        self.assertIn("timed out", stderr.lower())

    def test_out_dir_is_created_when_missing(self) -> None:
        image_data_url = "data:image/png;base64," + base64.b64encode(b"data").decode(
            "ascii"
        )
        response = FakeResponse(
            {
                "choices": [
                    {"message": {"images": [{"image_url": {"url": image_data_url}}]}}
                ]
            }
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "nested" / "output"
            self.assertFalse(out_dir.exists())

            with patch("main.requests.post", return_value=response):
                code, stdout, _stderr = self.run_main(
                    ["--prompt", "x", "--out-dir", str(out_dir)]
                )

            self.assertEqual(code, 0)
            self.assertTrue(out_dir.exists())
            self.assertEqual(Path(stdout).parent.resolve(), out_dir.resolve())

    def test_collision_retry_uses_new_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)
            fixed_datetime = datetime(2026, 2, 3, 4, 5, 6, tzinfo=UTC)
            colliding = out_dir / "ezbanana_20260203_040506_00000001.png"
            colliding.write_bytes(b"exists")

            with (
                patch("main.datetime") as mock_datetime,
                patch("main.secrets.randbelow", side_effect=[1, 2]),
            ):
                mock_datetime.now.return_value = fixed_datetime
                output_path = cli.generate_unique_output_path(out_dir)

            self.assertEqual(output_path.name, "ezbanana_20260203_040506_00000002.png")


if __name__ == "__main__":
    unittest.main()
