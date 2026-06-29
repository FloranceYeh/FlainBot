from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flainbot import ChatInputNode, ChatOutputNode, GraphExecutor
from flainbot.config import build_graph_from_config


class GraphConfigTests(unittest.TestCase):
    def test_chat_boundary_nodes_pass_message_to_reply(self):
        self.assertEqual(ChatInputNode("hello").run({}), {"text": "hello"})
        self.assertEqual(ChatOutputNode().run({"text": "reply"}), {"reply": "reply"})

    def test_build_graph_from_config_executes_chat_graph(self):
        def fake_transport(url, headers, body):
            return {"choices": [{"message": {"content": f"echo: {body['messages'][0]['content']}"}}]}

        config = {
            "nodes": [
                {"id": "chat_input_1", "type": "chat_input", "props": {}},
                {
                    "id": "openai_1",
                    "type": "openai",
                    "props": {
                        "base_url": "https://api.openai.test/v1",
                        "api_key": "key",
                        "model": "gpt-test",
                    },
                },
                {"id": "chat_output_1", "type": "chat_output", "props": {}},
            ],
            "edges": [
                {
                    "from_node": "chat_input_1",
                    "from_port": "text",
                    "to_node": "openai_1",
                    "to_port": "text",
                },
                {
                    "from_node": "openai_1",
                    "from_port": "text",
                    "to_node": "chat_output_1",
                    "to_port": "text",
                },
            ],
        }

        graph = build_graph_from_config(config, message="hello", transports={"openai": fake_transport})
        outputs = GraphExecutor(graph).run()

        self.assertEqual(outputs["chat_output_1"]["reply"], "echo: hello")


if __name__ == "__main__":
    unittest.main()
