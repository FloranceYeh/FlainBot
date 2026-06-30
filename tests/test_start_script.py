from contextlib import redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import start


class StartScriptTests(unittest.TestCase):
    def test_default_arguments_launch_openai_server(self):
        stdout = io.StringIO()
        env = {"OPENAI_API_KEY": "sk-test"}

        with patch.dict(os.environ, env, clear=True):
            with patch("scripts.web_chat.main", return_value=0) as web_chat_main:
                with redirect_stdout(stdout):
                    result = start.main([])

        self.assertEqual(result, 0)
        self.assertEqual(web_chat_main.call_args.args[0], ["openai", "--host", "127.0.0.1", "--port", "8765"])
        self.assertIn("http://127.0.0.1:8765/#chat", stdout.getvalue())

    def test_anthropic_arguments_launch_with_model_and_base_url(self):
        stdout = io.StringIO()
        env = {"ANTHROPIC_API_KEY": "sk-ant-test"}

        with patch.dict(os.environ, env, clear=True):
            with patch("scripts.web_chat.main", return_value=0) as web_chat_main:
                with redirect_stdout(stdout):
                    result = start.main([
                        "--provider",
                        "anthropic",
                        "--host",
                        "0.0.0.0",
                        "--port",
                        "9000",
                        "--model",
                        "claude-sonnet-4-5",
                        "--base-url",
                        "https://example.com/v1",
                    ])

        self.assertEqual(result, 0)
        self.assertIn("http://0.0.0.0:9000/#chat", stdout.getvalue())
        self.assertEqual(
            web_chat_main.call_args.args[0],
            [
                "anthropic",
                "--host",
                "0.0.0.0",
                "--port",
                "9000",
                "--model",
                "claude-sonnet-4-5",
                "--base-url",
                "https://example.com/v1",
            ],
        )

    def test_missing_api_key_returns_error_without_launching(self):
        stderr = io.StringIO()

        with patch.dict(os.environ, {}, clear=True):
            with patch("scripts.web_chat.main") as web_chat_main:
                with redirect_stderr(stderr):
                    result = start.main([])

        self.assertEqual(result, 2)
        self.assertFalse(web_chat_main.called)
        self.assertIn("OPENAI_API_KEY", stderr.getvalue())

    def test_anthropic_requires_anthropic_api_key(self):
        stderr = io.StringIO()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            with patch("scripts.web_chat.main") as web_chat_main:
                with redirect_stderr(stderr):
                    result = start.main(["--provider", "anthropic"])

        self.assertEqual(result, 2)
        self.assertFalse(web_chat_main.called)
        self.assertIn("ANTHROPIC_API_KEY", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
