from pathlib import Path
from contextlib import redirect_stdout
import io
import sys
from urllib import request
import json
import unittest
from http.server import ThreadingHTTPServer
import threading
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import web_chat


class WebChatTests(unittest.TestCase):
    def test_save_and_load_active_graph_config(self):
        store = web_chat.GraphConfigStore()
        config = {"nodes": [], "edges": []}

        store.save(config)

        self.assertEqual(store.load(), config)

    def test_run_chat_uses_active_graph_config(self):
        store = web_chat.GraphConfigStore()
        store.save(
            {
                "nodes": [
                    {"id": "chat_input_1", "type": "chat_input", "props": {}},
                    {"id": "echo_1", "type": "provider_call", "props": {"provider_id": "openai_main"}},
                    {"id": "chat_output_1", "type": "chat_output", "props": {}},
                ],
                "edges": [
                    {"from_node": "chat_input_1", "from_port": "text", "to_node": "echo_1", "to_port": "text"},
                    {"from_node": "echo_1", "from_port": "text", "to_node": "chat_output_1", "to_port": "text"},
                ],
                "providers": [
                    {
                        "id": "openai_main",
                        "format": "openai_chat",
                        "base_url": "x",
                        "api_key": "k",
                        "model": "m",
                    }
                ],
            }
        )

        def fake_transport(url, headers, body):
            return {"choices": [{"message": {"content": f"echo: {body['messages'][0]['content']}"}}]}

        reply = web_chat.run_chat("hello", store, transports={"openai_chat": fake_transport})

        self.assertEqual(reply, {"reply": "echo: hello"})

    def test_run_chat_can_echo_direct_input_to_output_graph(self):
        store = web_chat.GraphConfigStore()
        store.save(
            {
                "nodes": [
                    {"id": "chat_input_1", "type": "chat_input", "props": {}},
                    {"id": "chat_output_1", "type": "chat_output", "props": {}},
                ],
                "edges": [
                    {"from_node": "chat_input_1", "from_port": "text", "to_node": "chat_output_1", "to_port": "text"},
                ],
            }
        )

        reply = web_chat.run_chat("hello", store)

        self.assertEqual(reply, {"reply": "hello"})

    def test_graph_api_saves_and_loads_config(self):
        store = web_chat.GraphConfigStore()
        server = ThreadingHTTPServer(("127.0.0.1", 0), web_chat.make_handler(store))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        config = {"nodes": [{"id": "chat_input_1", "type": "chat_input", "props": {}}], "edges": []}

        try:
            body = json.dumps(config).encode("utf-8")
            req = request.Request(
                f"{base_url}/api/graph",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=5) as response:
                self.assertEqual(json.loads(response.read().decode("utf-8")), {"status": "ok"})

            with request.urlopen(f"{base_url}/api/graph", timeout=5) as response:
                self.assertEqual(json.loads(response.read().decode("utf-8")), config)
        finally:
            server.shutdown()
            server.server_close()

    def test_nodes_api_returns_builtin_node_catalog(self):
        store = web_chat.GraphConfigStore()
        server = ThreadingHTTPServer(("127.0.0.1", 0), web_chat.make_handler(store))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"

        try:
            with request.urlopen(f"{base_url}/api/nodes", timeout=5) as response:
                catalog = json.loads(response.read().decode("utf-8"))

            node_types = {node["type"] for node in catalog}
            self.assertIn("chat_input", node_types)
            self.assertIn("chat_output", node_types)
            self.assertIn("prompt_builder", node_types)
            self.assertIn("provider_call", node_types)
            self.assertNotIn("openai", node_types)
            self.assertNotIn("anthropic", node_types)
            class_names = {node["className"] for node in catalog}
            self.assertIn("ChatInputNode", class_names)
            self.assertIn("ChatOutputNode", class_names)
            self.assertIn("PromptBuilderNode", class_names)
            self.assertIn("ProviderCallNode", class_names)
            prompt_builder = next(node for node in catalog if node["type"] == "prompt_builder")
            self.assertEqual(prompt_builder["outputs"], ["json"])
            self.assertIn("system_prompt", prompt_builder["defaults"])
            self.assertIn("user_prompt", prompt_builder["defaults"])
            self.assertIn("tools_json", prompt_builder["defaults"])
            self.assertIn("context_json", prompt_builder["defaults"])
            self.assertTrue(all("inputs" in node and "outputs" in node for node in catalog))
        finally:
            server.shutdown()
            server.server_close()

    def test_graph_api_accepts_browser_preflight_from_static_server(self):
        store = web_chat.GraphConfigStore()
        server = ThreadingHTTPServer(("127.0.0.1", 0), web_chat.make_handler(store))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"

        try:
            req = request.Request(
                f"{base_url}/api/graph",
                headers={
                    "Origin": "http://127.0.0.1:5500",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type",
                },
                method="OPTIONS",
            )
            with request.urlopen(req, timeout=5) as response:
                self.assertEqual(response.status, 204)
                self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")
                self.assertIn("POST", response.headers["Access-Control-Allow-Methods"])
                self.assertIn("Content-Type", response.headers["Access-Control-Allow-Headers"])
        finally:
            server.shutdown()
            server.server_close()

    def test_root_serves_single_index_shell(self):
        store = web_chat.GraphConfigStore()
        server = ThreadingHTTPServer(("127.0.0.1", 0), web_chat.make_handler(store))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"

        try:
            with request.urlopen(f"{base_url}/", timeout=5) as response:
                body = response.read().decode("utf-8")

            self.assertIn("FlainBot Node Planner", body)
            self.assertIn("FlainBot Chat", body)
            self.assertIn("app.js", body)
            self.assertNotIn("chat.js", body)
        finally:
            server.shutdown()
            server.server_close()

    def test_parse_args_does_not_require_provider(self):
        args = web_chat.parse_args([])

        self.assertEqual(args.host, "127.0.0.1")
        self.assertEqual(args.port, 8765)

    def test_main_starts_with_empty_graph_config(self):
        stdout = io.StringIO()
        captured = {}

        class FakeServer:
            server_port = 8765

            def __init__(self, address, handler):
                captured["address"] = address
                captured["handler"] = handler

            def serve_forever(self):
                return None

        with patch("scripts.web_chat.ThreadingHTTPServer", FakeServer):
            with redirect_stdout(stdout):
                result = web_chat.main([])

        handler = captured["handler"]
        self.assertEqual(result, 0)
        self.assertEqual(captured["address"], ("127.0.0.1", 8765))
        self.assertEqual(handler.store.load(), {"nodes": [], "edges": []})
        self.assertIn("http://127.0.0.1:8765/", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
