from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flainbot import GraphExecutor
from flainbot.config import build_graph_from_config
from scripts.smoke_chat import DEFAULT_MODELS, build_chat_graph, build_node

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


class GraphConfigStore:
    def __init__(self, initial_config: dict | None = None) -> None:
        self._config = initial_config or {"nodes": [], "edges": []}

    def save(self, config: dict) -> None:
        self._config = config

    def load(self) -> dict:
        return self._config


def run_chat(message: str, store: GraphConfigStore, transports=None) -> dict[str, str]:
    graph = build_graph_from_config(store.load(), message=message, transports=transports)
    outputs = GraphExecutor(graph).run()
    reply_node_id = find_chat_output_node_id(store.load())
    return {"reply": outputs[reply_node_id]["reply"]}


def find_chat_output_node_id(config: dict) -> str:
    for node in config.get("nodes", []):
        if node["type"] == "chat_output":
            return node["id"]
    raise ValueError("graph config must include a chat_output node")


def default_graph_config(provider: str, model: str, base_url: str | None) -> dict:
    api_key_env = "OPENAI_API_KEY" if provider == "openai" else "ANTHROPIC_API_KEY"
    provider_node = {
        "id": f"{provider}_1",
        "type": provider,
        "props": {
            "base_url": base_url or ("https://api.openai.com/v1" if provider == "openai" else "https://api.anthropic.com/v1"),
            "api_key_env": api_key_env,
            "model": model,
        },
    }
    return {
        "nodes": [
            {"id": "chat_input_1", "type": "chat_input", "props": {}, "x": 48, "y": 48},
            provider_node,
            {"id": "chat_output_1", "type": "chat_output", "props": {}, "x": 680, "y": 48},
        ],
        "edges": [
            {"from_node": "chat_input_1", "from_port": "text", "to_node": provider_node["id"], "to_port": "text"},
            {"from_node": provider_node["id"], "from_port": "text", "to_node": "chat_output_1", "to_port": "text"},
        ],
    }


def make_handler(store: GraphConfigStore):
    class WebChatHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/api/graph":
                self.send_json(store.load())
                return

            path = "/chat.html" if self.path == "/" else self.path
            file_path = (FRONTEND / path.lstrip("/")).resolve()
            if not str(file_path).startswith(str(FRONTEND.resolve())):
                self.send_error(404)
                return
            if not file_path.exists():
                self.send_error(404)
                return

            body = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type_for(file_path))
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            if self.path == "/api/graph":
                payload = self.read_json()
                store.save(payload)
                self.send_json({"status": "ok"})
                return

            if self.path != "/api/chat":
                self.send_error(404)
                return

            payload = self.read_json()
            self.send_json(run_chat(payload["message"], store))

        def read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(length).decode("utf-8"))

        def send_json(self, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:
            return

    return WebChatHandler


def content_type_for(path: Path) -> str:
    if path.suffix == ".html":
        return "text/html; charset=utf-8"
    if path.suffix == ".css":
        return "text/css; charset=utf-8"
    if path.suffix == ".js":
        return "text/javascript; charset=utf-8"
    return "application/octet-stream"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run FlainBot web chat.")
    parser.add_argument("provider", choices=["openai", "anthropic"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    model = args.model or DEFAULT_MODELS[args.provider]
    store = GraphConfigStore(default_graph_config(args.provider, model, args.base_url))
    server = ThreadingHTTPServer((args.host, args.port), make_handler(store))
    print(f"FlainBot web chat: http://{args.host}:{args.port}/")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
