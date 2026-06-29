from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flainbot import AnthropicMessagesNode, InputNode, OpenAIChatNode, OutputNode


class ProviderNodeTests(unittest.TestCase):
    def test_input_node_outputs_user_text(self):
        outputs = InputNode("hello").run({})

        self.assertEqual(outputs, {"text": "hello"})

    def test_output_node_returns_reply_target(self):
        outputs = OutputNode().run({"text": "reply"})

        self.assertEqual(outputs, {"reply": "reply"})

    def test_openai_chat_node_posts_chat_completion_and_writes_output(self):
        calls = []

        def fake_transport(url, headers, body):
            calls.append((url, headers, body))
            return {"choices": [{"message": {"content": "hello from openai"}}]}

        node = OpenAIChatNode(
            base_url="https://api.openai.test/v1",
            api_key="test-key",
            model="gpt-test",
            transport=fake_transport,
        )

        outputs = node.run({"text": "hello"})

        self.assertEqual(node.base_url, "https://api.openai.test/v1")
        self.assertEqual(node.api_key, "test-key")
        self.assertEqual(node.model, "gpt-test")
        self.assertEqual(calls[0][0], "https://api.openai.test/v1/chat/completions")
        self.assertEqual(calls[0][1]["Authorization"], "Bearer test-key")
        self.assertEqual(calls[0][1]["Content-Type"], "application/json")
        self.assertEqual(
            calls[0][2],
            {
                "model": "gpt-test",
                "messages": [{"role": "user", "content": "hello"}],
            },
        )
        self.assertEqual(outputs["request"], calls[0][2])
        self.assertEqual(outputs["response"]["choices"][0]["message"]["content"], "hello from openai")
        self.assertEqual(outputs["text"], "hello from openai")

    def test_anthropic_messages_node_posts_message_and_writes_output(self):
        calls = []

        def fake_transport(url, headers, body):
            calls.append((url, headers, body))
            return {"content": [{"type": "text", "text": "hello from anthropic"}]}

        node = AnthropicMessagesNode(
            base_url="https://api.anthropic.test/v1",
            api_key="test-key",
            model="claude-test",
            transport=fake_transport,
        )

        outputs = node.run({"text": "hello"})

        self.assertEqual(node.base_url, "https://api.anthropic.test/v1")
        self.assertEqual(node.api_key, "test-key")
        self.assertEqual(node.model, "claude-test")
        self.assertEqual(calls[0][0], "https://api.anthropic.test/v1/messages")
        self.assertEqual(calls[0][1]["x-api-key"], "test-key")
        self.assertEqual(calls[0][1]["anthropic-version"], "2023-06-01")
        self.assertEqual(calls[0][1]["Content-Type"], "application/json")
        self.assertEqual(
            calls[0][2],
            {
                "model": "claude-test",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "hello"}],
            },
        )
        self.assertEqual(outputs["request"], calls[0][2])
        self.assertEqual(outputs["response"]["content"][0]["text"], "hello from anthropic")
        self.assertEqual(outputs["text"], "hello from anthropic")


if __name__ == "__main__":
    unittest.main()
