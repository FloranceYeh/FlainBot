from __future__ import annotations

from typing import Any

from .graph import Graph, NodeBuildError
from .node_registry import NodeBuildContext, NodePackageRegistry, discover_node_registry
from .providers import Transport
from .runtime_logging import RuntimeLogger


def build_graph_from_config(
    config: dict[str, Any],
    message: str,
    transports: dict[str, Transport] | None = None,
    registry: NodePackageRegistry | None = None,
    session_contexts: list[dict[str, Any]] | None = None,
    logger: RuntimeLogger | None = None,
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
        logger=logger or RuntimeLogger(),
    )
    graph = Graph()

    for node_config in config.get("nodes", []):
        try:
            node = build_node_from_config(node_config, context, registry)
        except Exception as exc:
            raise NodeBuildError(node_config["id"], node_config["type"], exc) from exc
        graph.add_node(node_config["id"], node)

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
