from __future__ import annotations

import argparse
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from flainbot import GraphExecutor
from flainbot.config import build_graph_from_config
from flainbot.node_registry import discover_node_registry

FRONTEND = ROOT / "frontend"
VUE_DIST = FRONTEND / "dist"
VUE_ENTRY = ROOT / "index.html"
DEFAULT_DATA_FILE = ROOT / "data" / "flainbot_state.json"


def empty_config() -> dict:
    return {
        "nodes": [],
        "edges": [],
        "providers": [],
        "personas": [],
    }


class GraphConfigStore:
    def __init__(self, initial_config: dict | None = None, data_file: Path | str | None = None) -> None:
        self._data_file = Path(data_file) if data_file is not None else None
        if initial_config is not None:
            self._config = initial_config
            self._persist()
            return
        self._config = self._load_from_file() if self._data_file else empty_config()

    def save(self, config: dict) -> None:
        self._config = config
        self._persist()

    def load(self) -> dict:
        return self._config

    def save_providers(self, providers: list[dict]) -> None:
        self._config = {**self._config, "providers": providers}
        self._persist()

    def load_providers(self) -> list[dict]:
        return self._config.get("providers", [])

    def save_personas(self, personas: list[dict]) -> None:
        self._config = {**self._config, "personas": personas}
        self._persist()

    def load_personas(self) -> list[dict]:
        return self._config.get("personas", [])

    def _load_from_file(self) -> dict:
        if self._data_file is None or not self._data_file.exists():
            return empty_config()
        return json.loads(self._data_file.read_text(encoding="utf-8"))

    def _persist(self) -> None:
        if self._data_file is None:
            return
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        self._data_file.write_text(
            json.dumps(self._config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def run_chat(message: str, store: GraphConfigStore, transports=None) -> dict[str, str]:
    config = store.load()
    graph = build_graph_from_config(
        config,
        message=message,
        transports=transports,
        session_contexts=config.get("session_contexts", []),
    )
    executor = GraphExecutor(graph)
    outputs = executor.run()
    reply_node_ids = find_chat_output_node_ids(config)
    replies = [outputs[node_id]["reply"] for node_id in reply_node_ids]
    reply = "\n".join(replies)
    store.save(
        {
            **config,
            "session_contexts": config.get("session_contexts", [])
            + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": reply},
            ],
        }
    )
    return {"reply": reply, "replies": replies, "trace": executor.trace}


def find_chat_output_node_id(config: dict) -> str:
    return find_chat_output_node_ids(config)[0]


def find_chat_output_node_ids(config: dict) -> list[str]:
    node_ids = [
        node["id"]
        for node in config.get("nodes", [])
        if node["type"] == "chat_output"
    ]
    if node_ids:
        return node_ids
    raise ValueError("graph config must include a chat_output node")


def make_handler(store: GraphConfigStore):
    class WebChatHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/api/graph":
                self.send_json(store.load())
                return
            if self.path == "/api/providers":
                self.send_json(store.load_providers())
                return
            if self.path == "/api/personas":
                self.send_json(store.load_personas())
                return
            if self.path == "/api/nodes":
                self.send_json(discover_node_registry().catalog())
                return

            file_path = static_file_path(self.path)
            if file_path is None:
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

            if self.path == "/api/providers":
                payload = self.read_json()
                store.save_providers(payload)
                self.send_json({"status": "ok"})
                return

            if self.path == "/api/personas":
                payload = self.read_json()
                store.save_personas(payload)
                self.send_json({"status": "ok"})
                return

            if self.path != "/api/chat":
                self.send_error(404)
                return

            payload = self.read_json()
            self.send_json(run_chat(payload["message"], store))

        def do_OPTIONS(self) -> None:
            if self.path not in {
                "/api/graph",
                "/api/chat",
                "/api/nodes",
                "/api/providers",
                "/api/personas",
            }:
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


def static_root() -> Path:
    return VUE_DIST if (VUE_DIST / "index.html").exists() else ROOT


def static_file_path(path: str) -> Path | None:
    root = static_root()
    request_path = "/index.html" if path == "/" else path
    file_path = (root / request_path.lstrip("/")).resolve()
    if not str(file_path).startswith(str(root.resolve())):
        return None
    return file_path


def content_type_for(path: Path) -> str:
    if path.suffix == ".html":
        return "text/html; charset=utf-8"
    if path.suffix == ".css":
        return "text/css; charset=utf-8"
    if path.suffix == ".js":
        return "text/javascript; charset=utf-8"
    if path.suffix == ".vue":
        return "text/plain; charset=utf-8"
    return "application/octet-stream"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run FlainBot web chat.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--data-file", default=str(DEFAULT_DATA_FILE))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    store = GraphConfigStore(data_file=args.data_file)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(store))
    print(f"FlainBot web chat: http://{args.host}:{args.port}/")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
