from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flainbot import GraphExecutor
from scripts.smoke_chat import DEFAULT_MODELS, build_chat_graph, build_node

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def run_chat(message: str, graph_runner: Callable[[str], dict]) -> dict[str, str]:
    outputs = graph_runner(message)
    return {"reply": outputs["output"]["reply"]}


def make_graph_runner(provider: str, model: str, base_url: str | None):
    def graph_runner(message: str) -> dict:
        node = build_node(provider, os.environ, base_url, model)
        graph = build_chat_graph(message, node)
        return GraphExecutor(graph).run()

    return graph_runner


def make_handler(graph_runner: Callable[[str], dict]):
    class WebChatHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
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
            if self.path != "/api/chat":
                self.send_error(404)
                return

            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            response = run_chat(payload["message"], graph_runner)
            body = json.dumps(response).encode("utf-8")

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
    runner = make_graph_runner(args.provider, model, args.base_url)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(runner))
    print(f"FlainBot web chat: http://{args.host}:{args.port}/")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

