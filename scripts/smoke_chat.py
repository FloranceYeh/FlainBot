from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flainbot import (
    AnthropicMessagesNode,
    Graph,
    GraphExecutor,
    InputNode,
    OpenAIChatNode,
    OutputNode,
)

DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
}

DEFAULT_MODELS = {
    "openai": "gpt-4.1-mini",
    "anthropic": "claude-sonnet-4-5",
}

API_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def build_node(
    provider: str,
    env: Mapping[str, str],
    base_url: str | None,
    model: str,
):
    if provider == "openai":
        api_key = env.get(API_KEY_ENV[provider])
        if not api_key:
            raise SystemExit(f"{API_KEY_ENV[provider]} is required")
        return OpenAIChatNode(
            base_url=base_url or DEFAULT_BASE_URLS[provider],
            api_key=api_key,
            model=model,
        )

    if provider == "anthropic":
        api_key = env.get(API_KEY_ENV[provider])
        if not api_key:
            raise SystemExit(f"{API_KEY_ENV[provider]} is required")
        return AnthropicMessagesNode(
            base_url=base_url or DEFAULT_BASE_URLS[provider],
            api_key=api_key,
            model=model,
        )

    raise SystemExit(f"unsupported provider: {provider}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a real FlainBot chat graph.")
    parser.add_argument("provider", choices=["openai", "anthropic"])
    parser.add_argument(
        "--message",
        default="Reply with exactly: flainbot smoke ok",
        help="Message sent through the graph.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name. Defaults to a provider-specific smoke-test model.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override provider base URL, for compatible gateways or proxies.",
    )
    return parser.parse_args(argv)


def build_chat_graph(message: str, provider_node) -> Graph:
    graph = Graph()
    graph.add_node("input", InputNode(message))
    graph.add_node("provider", provider_node)
    graph.add_node("output", OutputNode())
    graph.connect("input", "text", "provider", "text")
    graph.connect("provider", "text", "output", "text")
    return graph


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    model = args.model or DEFAULT_MODELS[args.provider]
    node = build_node(
        provider=args.provider,
        env=os.environ,
        base_url=args.base_url,
        model=model,
    )

    graph = build_chat_graph(args.message, node)
    outputs = GraphExecutor(graph).run()

    print(f"provider: {args.provider}")
    print(f"base_url: {node.base_url}")
    print(f"model: {node.model}")
    print(f"reply: {outputs['output']['reply']}")
    print("nodes:")
    for node_id in outputs:
        print(f"- {node_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
