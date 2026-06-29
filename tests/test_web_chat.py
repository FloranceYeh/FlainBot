from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import web_chat


class WebChatTests(unittest.TestCase):
    def test_run_chat_returns_reply_from_graph_runner(self):
        def fake_runner(message):
            return {"output": {"reply": f"echo: {message}"}}

        reply = web_chat.run_chat("hello", fake_runner)

        self.assertEqual(reply, {"reply": "echo: hello"})


if __name__ == "__main__":
    unittest.main()
