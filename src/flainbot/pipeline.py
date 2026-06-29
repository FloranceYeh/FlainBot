from __future__ import annotations

from collections.abc import Iterable

from .context import MessageContext, NodeTrace
from .node import Node


class PipelineError(RuntimeError):
    def __init__(self, node_name: str, message: str) -> None:
        super().__init__(f"{node_name}: {message}")
        self.node_name = node_name


class Pipeline:
    def __init__(self, nodes: Iterable[Node] = ()) -> None:
        self._nodes = list(nodes)

    @property
    def nodes(self) -> tuple[Node, ...]:
        return tuple(self._nodes)

    def insert_after(self, existing_node_name: str, node: Node) -> None:
        for index, existing in enumerate(self._nodes):
            if existing.name == existing_node_name:
                self._nodes.insert(index + 1, node)
                return
        raise ValueError(f"node not found: {existing_node_name}")

    def run(self, context: MessageContext) -> MessageContext:
        for node in self._nodes:
            try:
                node.handle(context)
            except Exception as exc:
                context.trace.append(
                    NodeTrace(node_name=node.name, status="error", error=str(exc))
                )
                raise PipelineError(node.name, str(exc)) from exc
            context.trace.append(NodeTrace(node_name=node.name, status="ok"))
        return context

