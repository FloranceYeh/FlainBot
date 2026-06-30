from __future__ import annotations

from typing import Any

from .graph import Graph
from .node_registry import NodeBuildContext, NodePackageRegistry, discover_node_registry
from .providers import Transport


def build_graph_from_config(
    config: dict[str, Any],
    message: str,
    transports: dict[str, Transport] | None = None,
    registry: NodePackageRegistry | None = None,
    session_contexts: list[dict[str, Any]] | None = None,
) -> Graph:
    transports = transports or {}
    providers = {provider["id"]: provider for provider in config.get("providers", [])}
    personas = {persona["persona_id"]: persona for persona in config.get("personas", [])}
    registry = registry or discover_node_registry()
    context = NodeBuildContext(
        message=message,
        transports=transports,
        providers=providers,
        personas=personas,
        session_contexts=session_contexts or [],
    )
    graph = Graph()

    for node_config in config.get("nodes", []):
        graph.add_node(
            node_config["id"],
            build_node_from_config(node_config, context, registry),
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
    context: NodeBuildContext,
    registry: NodePackageRegistry | None = None,
):
    return (registry or discover_node_registry()).build(node_config, context)
