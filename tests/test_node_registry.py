from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flainbot import ChatInputNode, ProviderCallNode
from flainbot.node_registry import NodeBuildContext, discover_node_registry


def collect_nodes(items):
    nodes = []
    for item in items:
        if item["kind"] == "node":
            nodes.append(item)
        elif item["kind"] == "group":
            nodes.extend(collect_nodes(item["items"]))
    return nodes


class NodeRegistryTests(unittest.TestCase):
    def test_discovers_node_packages_as_catalog(self):
        registry = discover_node_registry()

        catalog = registry.catalog()

        package_ids = [package["id"] for package in catalog]
        self.assertIn("core", package_ids)
        core = next(package for package in catalog if package["id"] == "core")
        self.assertEqual(core["kind"], "package")
        self.assertTrue(any(item["kind"] == "group" for item in core["items"]))
        node_types = {node["type"] for node in collect_nodes(core["items"])}
        self.assertIn("chat_input", node_types)
        self.assertIn("provider_call", node_types)

    def test_builds_nodes_from_registered_builders(self):
        registry = discover_node_registry()
        context = NodeBuildContext(
            message="hello",
            transports={"openai_chat": lambda *_: {"choices": [{"message": {"content": "ok"}}]}},
            providers={
                "openai_main": {
                    "id": "openai_main",
                    "format": "openai_chat",
                    "base_url": "https://api.openai.test/v1",
                    "api_key": "key",
                    "model": "your-model-name",
                }
            },
            personas={},
        )

        chat_input = registry.build({"id": "input_1", "type": "chat_input", "props": {}}, context)
        provider = registry.build(
            {"id": "provider_1", "type": "provider_call", "props": {"provider_id": "openai_main"}},
            context,
        )

        self.assertIsInstance(chat_input, ChatInputNode)
        self.assertIsInstance(provider, ProviderCallNode)

    def test_unknown_node_type_fails_clearly(self):
        registry = discover_node_registry()
        context = NodeBuildContext(message="", transports={}, providers={}, personas={})

        with self.assertRaisesRegex(ValueError, "unsupported node type: missing"):
            registry.build({"id": "missing_1", "type": "missing", "props": {}}, context)


if __name__ == "__main__":
    unittest.main()
