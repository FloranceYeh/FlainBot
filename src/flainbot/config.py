from __future__ import annotations

from typing import Any

from .builtins import ChatInputNode, ChatOutputNode, PersonaNode, PromptBuilderNode
from .graph import Graph
from .providers import ProviderCallNode, Transport


def build_graph_from_config(
    config: dict[str, Any],
    message: str,
    transports: dict[str, Transport] | None = None,
) -> Graph:
    transports = transports or {}
    providers = {provider["id"]: provider for provider in config.get("providers", [])}
    personas = {persona["persona_id"]: persona for persona in config.get("personas", [])}
    graph = Graph()

    for node_config in config.get("nodes", []):
        graph.add_node(
            node_config["id"],
            build_node_from_config(node_config, message, transports, providers, personas),
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
    providers: dict[str, dict[str, Any]],
    personas: dict[str, dict[str, Any]] | None = None,
):
    node_type = node_config["type"]
    props = node_config.get("props", {})
    personas = personas or {}

    if node_type == "chat_input":
        return ChatInputNode(message)

    if node_type == "chat_output":
        return ChatOutputNode()

    if node_type == "prompt_builder":
        return PromptBuilderNode(
            system_prompt=props.get("system_prompt", ""),
            user_prompt=props.get("user_prompt", ""),
            tools_json=props.get("tools_json", "[]"),
            contexts_json=props.get("contexts_json", "[]"),
        )

    if node_type == "provider_call":
        provider_id = props["provider_id"]
        if provider_id not in providers:
            raise ValueError(f"provider not found: {provider_id}")
        provider = providers[provider_id]
        return ProviderCallNode(
            provider=provider,
            transport=transports.get(provider["format"]),
        )

    if node_type == "persona":
        persona_id = props["persona_id"]
        if persona_id not in personas:
            raise ValueError(f"persona not found: {persona_id}")
        return PersonaNode(persona=personas[persona_id])

    raise ValueError(f"unsupported node type: {node_type}")
