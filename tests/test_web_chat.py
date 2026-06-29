from pathlib import Path
import sys
from urllib import request
import json
import unittest
from http.server import ThreadingHTTPServer
import threading

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
                    {"id": "echo_1", "type": "openai", "props": {"base_url": "x", "api_key": "k", "model": "m"}},
                    {"id": "chat_output_1", "type": "chat_output", "props": {}},
                ],
                "edges": [
                    {"from_node": "chat_input_1", "from_port": "text", "to_node": "echo_1", "to_port": "text"},
                    {"from_node": "echo_1", "from_port": "text", "to_node": "chat_output_1", "to_port": "text"},
                ],
            }
        )

        def fake_transport(url, headers, body):
            return {"choices": [{"message": {"content": f"echo: {body['messages'][0]['content']}"}}]}

        reply = web_chat.run_chat("hello", store, transports={"openai": fake_transport})

        self.assertEqual(reply, {"reply": "echo: hello"})

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


if __name__ == "__main__":
    unittest.main()
