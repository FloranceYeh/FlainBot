from __future__ import annotations

import argparse
import os
import sys

from scripts import web_chat


API_KEY_ENV_BY_PROVIDER = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the FlainBot web UI and chat server.")
    parser.add_argument("--provider", choices=sorted(API_KEY_ENV_BY_PROVIDER), default="openai")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    return parser.parse_args(argv)


def build_web_chat_argv(args: argparse.Namespace) -> list[str]:
    web_chat_argv = [
        args.provider,
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if args.model:
        web_chat_argv.extend(["--model", args.model])
    if args.base_url:
        web_chat_argv.extend(["--base-url", args.base_url])
    return web_chat_argv


def validate_environment(provider: str) -> bool:
    api_key_env = API_KEY_ENV_BY_PROVIDER[provider]
    if os.environ.get(api_key_env):
        return True

    print(f"Missing {api_key_env}. Set it before starting FlainBot.", file=sys.stderr)
    return False


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not validate_environment(args.provider):
        return 2

    print(f"FlainBot chat URL: http://{args.host}:{args.port}/#chat")
    return web_chat.main(build_web_chat_argv(args))


if __name__ == "__main__":
    raise SystemExit(main())
