from pathlib import Path
from contextlib import redirect_stdout
import io
import sys
from urllib import request
import json
import tempfile
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

    def test_graph_config_store_persists_config_to_local_file(self):
        config = {
            "nodes": [{"id": "chat_input_1", "type": "chat_input", "props": {}}],
            "edges": [],
            "providers": [{"id": "local", "format": "openai_chat"}],
            "personas": [{"persona_id": "cat"}],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "flainbot_state.json"
            store = web_chat.GraphConfigStore(data_file=data_file)

            store.save(config)
            reloaded = web_chat.GraphConfigStore(data_file=data_file)

        self.assertEqual(reloaded.load(), config)

    def test_graph_config_store_persists_provider_and_persona_updates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "flainbot_state.json"
            store = web_chat.GraphConfigStore(data_file=data_file)
            store.save({"nodes": [{"id": "n", "type": "chat_input", "props": {}}], "edges": []})
            store.save_providers([{"id": "provider"}])
            store.save_personas([{"persona_id": "persona"}])

            reloaded = web_chat.GraphConfigStore(data_file=data_file)

        self.assertEqual(reloaded.load()["nodes"], [{"id": "n", "type": "chat_input", "props": {}}])
        self.assertEqual(reloaded.load_providers(), [{"id": "provider"}])
        self.assertEqual(reloaded.load_personas(), [{"persona_id": "persona"}])

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

        self.assertEqual(reply["reply"], "echo: hello")
        self.assertEqual(
            [item["node_id"] for item in reply["trace"]],
            ["chat_input_1", "echo_1", "chat_output_1"],
        )
        self.assertEqual(reply["trace"][0]["outputs"], {"text": "hello"})
        self.assertEqual(reply["trace"][2]["outputs"], {"reply": "echo: hello"})

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

        self.assertEqual(reply["reply"], "hello")
        self.assertEqual(
            reply["trace"],
            [
                {"node_id": "chat_input_1", "inputs": {}, "outputs": {"text": "hello"}},
                {"node_id": "chat_output_1", "inputs": {"text": "hello"}, "outputs": {"reply": "hello"}},
            ],
        )

    def test_run_chat_returns_all_chat_output_replies(self):
        store = web_chat.GraphConfigStore()
        store.save(
            {
                "nodes": [
                    {"id": "chat_input_1", "type": "chat_input", "props": {}},
                    {"id": "echo_1", "type": "provider_call", "props": {"provider_id": "openai_main"}},
                    {"id": "chat_output_1", "type": "chat_output", "props": {}},
                    {"id": "chat_output_2", "type": "chat_output", "props": {}},
                ],
                "edges": [
                    {"from_node": "chat_input_1", "from_port": "text", "to_node": "chat_output_1", "to_port": "text"},
                    {"from_node": "chat_input_1", "from_port": "text", "to_node": "echo_1", "to_port": "text"},
                    {"from_node": "echo_1", "from_port": "text", "to_node": "chat_output_2", "to_port": "text"},
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

        self.assertEqual(reply["replies"], ["hello", "echo: hello"])
        self.assertEqual(reply["reply"], "hello\necho: hello")
        self.assertEqual(
            sorted(item["node_id"] for item in reply["trace"]),
            ["chat_input_1", "chat_output_1", "chat_output_2", "echo_1"],
        )

    def test_run_chat_maintains_session_context_between_turns(self):
        requests = []

        def fake_transport(url, headers, body):
            requests.append(body)
            return {"choices": [{"message": {"content": f"reply {len(requests)}"}}]}

        store = web_chat.GraphConfigStore(
            initial_config={
                "nodes": [
                    {"id": "chat_input_1", "type": "chat_input", "props": {}},
                    {"id": "session_context_1", "type": "session_context", "props": {}},
                    {
                        "id": "prompt_builder_1",
                        "type": "prompt_builder",
                        "props": {
                            "system_prompt": "",
                            "user_prompt": "",
                            "tools_json": "[]",
                            "contexts_json": "[]",
                        },
                    },
                    {"id": "provider_1", "type": "provider_call", "props": {"provider_id": "openai_main"}},
                    {"id": "chat_output_1", "type": "chat_output", "props": {}},
                ],
                "edges": [
                    {"from_node": "chat_input_1", "from_port": "text", "to_node": "prompt_builder_1", "to_port": "user"},
                    {
                        "from_node": "session_context_1",
                        "from_port": "json",
                        "to_node": "prompt_builder_1",
                        "to_port": "contexts",
                    },
                    {
                        "from_node": "prompt_builder_1",
                        "from_port": "json",
                        "to_node": "provider_1",
                        "to_port": "json",
                    },
                    {"from_node": "provider_1", "from_port": "text", "to_node": "chat_output_1", "to_port": "text"},
                ],
                "providers": [
                    {
                        "id": "openai_main",
                        "format": "openai_chat",
                        "base_url": "https://api.openai.test/v1",
                        "api_key": "key",
                        "model": "gpt-test",
                    }
                ],
            }
        )

        first = web_chat.run_chat("hello", store, transports={"openai_chat": fake_transport})
        second = web_chat.run_chat("again", store, transports={"openai_chat": fake_transport})

        self.assertEqual(first["reply"], "reply 1")
        self.assertEqual(second["reply"], "reply 2")
        self.assertEqual(requests[0]["messages"], [{"role": "user", "content": "hello"}])
        self.assertEqual(
            requests[1]["messages"],
            [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "reply 1"},
                {"role": "user", "content": "again"},
            ],
        )
        self.assertEqual(
            store.load()["session_contexts"],
            [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "reply 1"},
                {"role": "user", "content": "again"},
                {"role": "assistant", "content": "reply 2"},
            ],
        )

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

    def test_provider_api_saves_and_loads_configs(self):
        store = web_chat.GraphConfigStore()
        server = ThreadingHTTPServer(("127.0.0.1", 0), web_chat.make_handler(store))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        providers = [
            {
                "id": "openai_main",
                "format": "openai_chat",
                "base_url": "https://api.openai.test/v1",
                "api_key": "key",
                "model": "gpt-test",
            },
            {
                "id": "anthropic_main",
                "format": "anthropic_messages",
                "base_url": "https://api.anthropic.test/v1",
                "api_key": "key",
                "model": "claude-test",
            },
        ]

        try:
            body = json.dumps(providers).encode("utf-8")
            req = request.Request(
                f"{base_url}/api/providers",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=5) as response:
                self.assertEqual(json.loads(response.read().decode("utf-8")), {"status": "ok"})

            with request.urlopen(f"{base_url}/api/providers", timeout=5) as response:
                self.assertEqual(json.loads(response.read().decode("utf-8")), providers)

            self.assertEqual(store.load().get("providers"), providers)
        finally:
            server.shutdown()
            server.server_close()

    def test_persona_api_saves_and_loads_configs(self):
        store = web_chat.GraphConfigStore()
        server = ThreadingHTTPServer(("127.0.0.1", 0), web_chat.make_handler(store))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        personas = [
            {
                "persona_id": "cat",
                "system_prompt": "You are a cat.",
                "begin_dialogs": ["Hi", "Meow."],
                "tools": [],
                "skills": [],
                "custom_error_message": None,
            }
        ]

        try:
            body = json.dumps(personas).encode("utf-8")
            req = request.Request(
                f"{base_url}/api/personas",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=5) as response:
                self.assertEqual(json.loads(response.read().decode("utf-8")), {"status": "ok"})

            with request.urlopen(f"{base_url}/api/personas", timeout=5) as response:
                self.assertEqual(json.loads(response.read().decode("utf-8")), personas)

            self.assertEqual(store.load().get("personas"), personas)
        finally:
            server.shutdown()
            server.server_close()

    def test_nodes_api_returns_dynamic_node_catalog(self):
        store = web_chat.GraphConfigStore()
        server = ThreadingHTTPServer(("127.0.0.1", 0), web_chat.make_handler(store))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"

        try:
            with request.urlopen(f"{base_url}/api/nodes", timeout=5) as response:
                catalog = json.loads(response.read().decode("utf-8"))

            self.assertTrue(all(package.get("kind") == "package" for package in catalog))
            package_ids = {package.get("id") for package in catalog}
            self.assertIn("core", package_ids)

            def collect_nodes(items):
                nodes = []
                for item in items:
                    if item["kind"] == "node":
                        nodes.append(item)
                    elif item["kind"] == "group":
                        nodes.extend(collect_nodes(item["items"]))
                return nodes

            def collect_groups(items):
                groups = []
                for item in items:
                    if item["kind"] == "group":
                        groups.append(item)
                        groups.extend(collect_groups(item["items"]))
                return groups

            nodes = []
            groups = []
            for package in catalog:
                nodes.extend(collect_nodes(package.get("items", [])))
                groups.extend(collect_groups(package.get("items", [])))

            self.assertTrue(any(group["kind"] == "group" for group in groups))
            self.assertTrue(any(item["kind"] == "group" for group in groups for item in group["items"]))
            node_types = {node["type"] for node in nodes}
            self.assertIn("chat_input", node_types)
            self.assertIn("chat_output", node_types)
            self.assertIn("prompt_builder", node_types)
            self.assertIn("persona", node_types)
            self.assertIn("provider_call", node_types)
            self.assertIn("session_context", node_types)
            self.assertNotIn("openai", node_types)
            self.assertNotIn("anthropic", node_types)
            class_names = {node["className"] for node in nodes}
            self.assertIn("ChatInputNode", class_names)
            self.assertIn("ChatOutputNode", class_names)
            self.assertIn("PromptBuilderNode", class_names)
            self.assertIn("PersonaNode", class_names)
            self.assertIn("ProviderCallNode", class_names)
            self.assertIn("SessionContextNode", class_names)
            def port_names(ports):
                return [port["name"] for port in ports]

            def port_types(ports):
                return [port["type"] for port in ports]

            self.assertTrue(
                all(
                    isinstance(port, dict) and {"name", "type"} <= set(port)
                    for node in nodes
                    for port in node["inputs"] + node["outputs"]
                )
            )
            prompt_builder = next(node for node in nodes if node["type"] == "prompt_builder")
            self.assertEqual(port_names(prompt_builder["outputs"]), ["json"])
            self.assertEqual(port_types(prompt_builder["outputs"]), ["json"])
            self.assertEqual(port_names(prompt_builder["inputs"]), ["system", "user", "tools", "contexts"])
            self.assertEqual(port_types(prompt_builder["inputs"]), ["text", "text", "json", "json"])
            self.assertIn("system_prompt", prompt_builder["defaults"])
            self.assertIn("user_prompt", prompt_builder["defaults"])
            self.assertIn("tools_json", prompt_builder["defaults"])
            self.assertIn("contexts_json", prompt_builder["defaults"])
            session_context = next(node for node in nodes if node["type"] == "session_context")
            self.assertEqual(port_names(session_context["inputs"]), [])
            self.assertEqual(port_types(session_context["inputs"]), [])
            self.assertEqual(port_names(session_context["outputs"]), ["json"])
            self.assertEqual(port_types(session_context["outputs"]), ["json"])
            provider_call = next(node for node in nodes if node["type"] == "provider_call")
            self.assertEqual(port_names(provider_call["inputs"]), ["text", "json"])
            self.assertEqual(port_types(provider_call["inputs"]), ["text", "json"])
            persona = next(node for node in nodes if node["type"] == "persona")
            self.assertEqual(port_names(persona["inputs"]), ["text", "json"])
            self.assertEqual(port_types(persona["inputs"]), ["text", "json"])
            self.assertEqual(port_names(persona["outputs"]), ["json"])
            self.assertEqual(port_types(persona["outputs"]), ["json"])
            self.assertIn("persona_id", persona["defaults"])
            meow = next(node for node in nodes if node["type"] == "meow_before_punctuation")
            self.assertEqual(meow["package"], "sample_text_tools")
            self.assertEqual(port_names(meow["inputs"]), ["text"])
            self.assertEqual(port_types(meow["inputs"]), ["text"])
            self.assertEqual(port_names(meow["outputs"]), ["text"])
            self.assertEqual(port_types(meow["outputs"]), ["text"])
            core_nodes = [node for node in nodes if node["type"] != "meow_before_punctuation"]
            self.assertTrue(all(node["package"] == "core" for node in core_nodes))
            self.assertTrue(all("inputs" in node and "outputs" in node for node in nodes))
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
                f"{base_url}/api/personas",
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
            self.assertTrue(
                "/src/frontend/main.js" in body or "/assets/" in body,
                body,
            )
            self.assertIn("id=\"app\"", body)
            self.assertNotIn("chat.js", body)
        finally:
            server.shutdown()
            server.server_close()

    def test_static_server_prefers_vue_dist_shell(self):
        dist_dir = web_chat.FRONTEND / "dist"
        dist_dir.mkdir(exist_ok=True)
        dist_index = dist_dir / "index.html"
        original = dist_index.read_text(encoding="utf-8") if dist_index.exists() else None
        dist_index.write_text("<!doctype html><title>Vue Dist Shell</title>", encoding="utf-8")

        store = web_chat.GraphConfigStore()
        server = ThreadingHTTPServer(("127.0.0.1", 0), web_chat.make_handler(store))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"

        try:
            with request.urlopen(f"{base_url}/", timeout=5) as response:
                body = response.read().decode("utf-8")

            self.assertIn("Vue Dist Shell", body)
        finally:
            server.shutdown()
            server.server_close()
            if original is None:
                dist_index.unlink()
                dist_dir.rmdir()
            else:
                dist_index.write_text(original, encoding="utf-8")

    def test_parse_args_does_not_require_provider(self):
        args = web_chat.parse_args([])

        self.assertEqual(args.host, "127.0.0.1")
        self.assertEqual(args.port, 8765)
        self.assertEqual(args.data_file, str(web_chat.DEFAULT_DATA_FILE))

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

        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "flainbot_state.json"
            with patch("scripts.web_chat.ThreadingHTTPServer", FakeServer):
                with redirect_stdout(stdout):
                    result = web_chat.main(["--data-file", str(data_file)])

        handler = captured["handler"]
        self.assertEqual(result, 0)
        self.assertEqual(captured["address"], ("127.0.0.1", 8765))
        self.assertEqual(handler.store.load(), {"nodes": [], "edges": [], "providers": [], "personas": []})
        self.assertIn("http://127.0.0.1:8765/", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
