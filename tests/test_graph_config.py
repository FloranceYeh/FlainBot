from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flainbot import ChatInputNode, ChatOutputNode, GraphExecutor, PersonaNode, PromptBuilderNode, ProviderCallNode
from flainbot.config import build_graph_from_config


class GraphConfigTests(unittest.TestCase):
    def test_chat_boundary_nodes_pass_message_to_reply(self):
        self.assertEqual(ChatInputNode("hello").run({}), {"text": "hello"})
        self.assertEqual(ChatOutputNode().run({"text": "reply"}), {"reply": "reply"})

    def test_prompt_builder_outputs_json_payload(self):
        node = PromptBuilderNode(
            system_prompt="You are concise.",
            user_prompt="Summarize this.",
            tools_json='[{"name": "search"}]',
            contexts_json='[{"role": "system", "content": "Use zh-CN."}]',
        )

        outputs = node.run({})

        self.assertEqual(
            outputs,
            {
                "json": {
                    "system_prompt": "You are concise.",
                    "prompt": "Summarize this.",
                    "tools": [{"name": "search"}],
                    "contexts": [{"role": "system", "content": "Use zh-CN."}],
                }
            },
        )

    def test_prompt_builder_inputs_override_default_props(self):
        node = PromptBuilderNode(
            system_prompt="default system",
            user_prompt="default user",
            tools_json="[]",
            contexts_json="[]",
        )

        outputs = node.run(
            {
                "system": "input system",
                "user": "input user",
                "tools": [{"name": "calculator"}],
                "contexts": '[{"role": "assistant", "content": "previous"}]',
            }
        )

        self.assertEqual(
            outputs["json"],
            {
                "system_prompt": "input system",
                "prompt": "input user",
                "tools": [{"name": "calculator"}],
                "contexts": [{"role": "assistant", "content": "previous"}],
            },
        )

    def test_persona_node_applies_persona_to_prompt_payload(self):
        node = PersonaNode(
            persona={
                "persona_id": "cat",
                "system_prompt": "You are a cat.",
                "begin_dialogs": ["Hi", "Meow."],
                "tools": [{"type": "function", "function": {"name": "scratch"}}],
                "skills": ["roleplay"],
                "custom_error_message": "Hiss.",
            }
        )

        outputs = node.run(
            {
                "json": {
                    "system_prompt": "Answer briefly.",
                    "prompt": "Hello",
                    "contexts": [{"role": "assistant", "content": "Previous"}],
                    "tools": [{"type": "function", "function": {"name": "search"}}],
                }
            }
        )

        self.assertEqual(
            outputs["json"],
            {
                "system_prompt": "You are a cat.\n\nAnswer briefly.",
                "prompt": "Hello",
                "contexts": [
                    {"role": "user", "content": "Hi", "_no_save": True},
                    {"role": "assistant", "content": "Meow.", "_no_save": True},
                    {"role": "assistant", "content": "Previous"},
                ],
                "tools": [{"type": "function", "function": {"name": "scratch"}}],
                "skills": ["roleplay"],
                "custom_error_message": "Hiss.",
                "persona_id": "cat",
            },
        )

    def test_persona_node_can_create_prompt_payload_from_text(self):
        node = PersonaNode(
            persona={
                "persona_id": "default",
                "system_prompt": "You are helpful.",
                "begin_dialogs": [],
                "tools": None,
                "skills": None,
                "custom_error_message": None,
            }
        )

        outputs = node.run({"text": "Hello"})

        self.assertEqual(
            outputs["json"],
            {
                "system_prompt": "You are helpful.",
                "prompt": "Hello",
                "contexts": [],
                "tools": [],
                "skills": [],
                "custom_error_message": None,
                "persona_id": "default",
            },
        )

    def test_build_graph_from_config_executes_chat_graph(self):
        def fake_transport(url, headers, body):
            return {"choices": [{"message": {"content": f"echo: {body['messages'][0]['content']}"}}]}

        config = {
            "nodes": [
                {"id": "chat_input_1", "type": "chat_input", "props": {}},
                {
                    "id": "provider_1",
                    "type": "provider_call",
                    "props": {
                        "provider_id": "openai_main",
                    },
                },
                {"id": "chat_output_1", "type": "chat_output", "props": {}},
            ],
            "edges": [
                {
                    "from_node": "chat_input_1",
                    "from_port": "text",
                    "to_node": "provider_1",
                    "to_port": "text",
                },
                {
                    "from_node": "provider_1",
                    "from_port": "text",
                    "to_node": "chat_output_1",
                    "to_port": "text",
                },
            ],
            "providers": [
                {
                    "id": "openai_main",
                    "format": "openai_chat",
                    "base_url": "https://api.openai.test/v1",
                    "api_key": "key",
                    "model": "gpt-test",
                },
            ],
        }

        graph = build_graph_from_config(config, message="hello", transports={"openai_chat": fake_transport})
        outputs = GraphExecutor(graph).run()

        self.assertEqual(outputs["chat_output_1"]["reply"], "echo: hello")

    def test_build_graph_from_config_resolves_provider_call_node(self):
        config = {
            "nodes": [
                {"id": "provider_1", "type": "provider_call", "props": {"provider_id": "anthropic_main"}},
            ],
            "edges": [],
            "providers": [
                {
                    "id": "anthropic_main",
                    "format": "anthropic_messages",
                    "base_url": "https://api.anthropic.test/v1",
                    "api_key": "key",
                    "model": "claude-test",
                },
            ],
        }

        graph = build_graph_from_config(config, message="", transports={"anthropic_messages": lambda *_: {"content": [{"text": "ok"}]}})

        self.assertIsInstance(graph.nodes["provider_1"], ProviderCallNode)

    def test_build_graph_from_config_executes_prompt_builder(self):
        config = {
            "nodes": [
                {
                    "id": "prompt_builder_1",
                    "type": "prompt_builder",
                    "props": {
                        "system_prompt": "System",
                        "user_prompt": "User",
                        "tools_json": '[{"name": "search"}]',
                        "contexts_json": "[]",
                    },
                },
            ],
            "edges": [],
        }

        graph = build_graph_from_config(config, message="")
        outputs = GraphExecutor(graph).run()

        self.assertEqual(
            outputs["prompt_builder_1"]["json"],
            {
                "system_prompt": "System",
                "prompt": "User",
                "tools": [{"name": "search"}],
                "contexts": [],
            },
        )

    def test_build_graph_from_config_executes_persona_node(self):
        config = {
            "nodes": [
                {"id": "chat_input_1", "type": "chat_input", "props": {}},
                {
                    "id": "persona_1",
                    "type": "persona",
                    "props": {
                        "persona_id": "cat",
                    },
                },
            ],
            "edges": [
                {
                    "from_node": "chat_input_1",
                    "from_port": "text",
                    "to_node": "persona_1",
                    "to_port": "text",
                },
            ],
            "personas": [
                {
                    "persona_id": "cat",
                    "system_prompt": "You are a cat.",
                    "begin_dialogs": ["Hi", "Meow."],
                    "tools": [],
                    "skills": [],
                    "custom_error_message": None,
                }
            ],
        }

        graph = build_graph_from_config(config, message="hello")
        outputs = GraphExecutor(graph).run()

        self.assertEqual(outputs["persona_1"]["json"]["persona_id"], "cat")
        self.assertEqual(outputs["persona_1"]["json"]["system_prompt"], "You are a cat.")
        self.assertEqual(outputs["persona_1"]["json"]["prompt"], "hello")


if __name__ == "__main__":
    unittest.main()
