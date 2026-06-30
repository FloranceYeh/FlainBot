from __future__ import annotations

import os
from typing import Any

from .builtins import ChatInputNode, ChatOutputNode, PromptBuilderNode
from .graph import Graph
from .providers import AnthropicMessagesNode, OpenAIChatNode, Transport


def build_graph_from_config(
    config: dict[str, Any],
    message: str,
    transports: dict[str, Transport] | None = None,
) -> Graph:
    transports = transports or {}
    graph = Graph()

    for node_config in config.get("nodes", []):
        graph.add_node(
            node_config["id"],
            build_node_from_config(node_config, message, transports),
        )

    for edge in config.get("edges", []):
        graph.connect(
            edge["from_node"],
            edge["from_port"],
            edge["to_node"],
            edge["to_port"],
        )

    return graph


def build_node_from_config(
    node_config: dict[str, Any],
    message: str,
    transports: dict[str, Transport],
):
    node_type = node_config["type"]
    props = node_config.get("props", {})

    if node_type == "chat_input":
        return ChatInputNode(message)

    if node_type == "chat_output":
        return ChatOutputNode()

    if node_type == "prompt_builder":
        return PromptBuilderNode(
            system_prompt=props.get("system_prompt", ""),
            user_prompt=props.get("user_prompt", ""),
            tools_json=props.get("tools_json", "[]"),
            context_json=props.get("context_json", "{}"),
        )

    if node_type == "openai":
        return OpenAIChatNode(
            base_url=props["base_url"],
            api_key=api_key_from_props(props),
            model=props["model"],
            transport=transports.get("openai"),
        )

    if node_type == "anthropic":
        return AnthropicMessagesNode(
            base_url=props["base_url"],
            api_key=api_key_from_props(props),
            model=props["model"],
            transport=transports.get("anthropic"),
        )

    raise ValueError(f"unsupported node type: {node_type}")


def api_key_from_props(props: dict[str, Any]) -> str:
    if props.get("api_key"):
        return props["api_key"]
    if props.get("api_key_env"):
        return os.environ[props["api_key_env"]]
    raise ValueError("api_key or api_key_env is required")
