from __future__ import annotations

import argparse

from scripts import web_chat


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the FlainBot web UI and chat server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--data-file", default=str(web_chat.DEFAULT_DATA_FILE))
    return parser.parse_args(argv)


def build_web_chat_argv(args: argparse.Namespace) -> list[str]:
    return [
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--data-file",
        args.data_file,
    ]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(f"FlainBot chat URL: http://{args.host}:{args.port}/#chat")
    return web_chat.main(build_web_chat_argv(args))


if __name__ == "__main__":
    raise SystemExit(main())
