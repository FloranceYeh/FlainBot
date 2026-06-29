from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import smoke_chat


class SmokeChatScriptTests(unittest.TestCase):
    def test_build_openai_node_from_environment(self):
        node = smoke_chat.build_node(
            provider="openai",
            env={"OPENAI_API_KEY": "key"},
            base_url=None,
            model="gpt-test",
        )

        self.assertEqual(node.base_url, "https://api.openai.com/v1")
        self.assertEqual(node.api_key, "key")
        self.assertEqual(node.model, "gpt-test")

    def test_build_anthropic_node_from_environment(self):
        node = smoke_chat.build_node(
            provider="anthropic",
            env={"ANTHROPIC_API_KEY": "key"},
            base_url=None,
            model="claude-test",
        )

        self.assertEqual(node.base_url, "https://api.anthropic.com/v1")
        self.assertEqual(node.api_key, "key")
        self.assertEqual(node.model, "claude-test")

    def test_missing_api_key_raises_clear_error(self):
        with self.assertRaisesRegex(SystemExit, "OPENAI_API_KEY is required"):
            smoke_chat.build_node(
                provider="openai",
                env={},
                base_url=None,
                model="gpt-test",
            )

    def test_unknown_provider_raises_clear_error(self):
        with self.assertRaisesRegex(SystemExit, "unsupported provider"):
            smoke_chat.build_node(
                provider="unknown",
                env={},
                base_url=None,
                model="test",
            )

    def test_build_chat_graph_connects_input_provider_output(self):
        provider = smoke_chat.build_node(
            provider="openai",
            env={"OPENAI_API_KEY": "key"},
            base_url=None,
            model="gpt-test",
        )

        graph = smoke_chat.build_chat_graph("hello", provider)

        self.assertEqual(set(graph.nodes), {"input", "provider", "output"})
        self.assertEqual(
            [(edge.from_node, edge.from_port, edge.to_node, edge.to_port) for edge in graph.edges],
            [
                ("input", "text", "provider", "text"),
                ("provider", "text", "output", "text"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
