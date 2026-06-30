from __future__ import annotations

import argparse
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flainbot import GraphExecutor
from flainbot.config import build_graph_from_config
from flainbot.node_catalog import builtin_node_catalog

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


def make_handler(store: GraphConfigStore):
    class WebChatHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/api/graph":
                self.send_json(store.load())
                return
            if self.path == "/api/nodes":
                self.send_json(builtin_node_catalog())
                return

            path = "/index.html" if self.path == "/" else self.path
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

        def do_OPTIONS(self) -> None:
            if self.path not in {"/api/graph", "/api/chat", "/api/nodes"}:
                self.send_error(404)
                return

            self.send_response(204)
            self.send_cors_headers()
            self.send_header("Content-Length", "0")
            self.end_headers()

        def read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(length).decode("utf-8"))

        def send_json(self, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_cors_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def log_message(self, format: str, *args) -> None:
            return

    WebChatHandler.store = store
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
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    store = GraphConfigStore()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(store))
    print(f"FlainBot web chat: http://{args.host}:{args.port}/")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
