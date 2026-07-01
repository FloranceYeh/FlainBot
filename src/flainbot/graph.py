from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from .node import Node


class GraphError(RuntimeError):
    pass


class NodeExecutionError(GraphError):
    def __init__(self, node_id: str, node_type: str, original: Exception) -> None:
        self.node_id = node_id
        self.node_type = node_type
        self.original = original
        super().__init__(f"node {node_id} failed: {original}")


class NodeBuildError(GraphError):
    def __init__(self, node_id: str, node_type: str, original: Exception) -> None:
        self.node_id = node_id
        self.node_type = node_type
        self.original = original
        super().__init__(f"node {node_id} failed to build: {original}")


@dataclass(frozen=True)
class GraphEdge:
    from_node: str
    from_port: str
    to_node: str
    to_port: str


class Graph:
    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._edges: list[GraphEdge] = []

    @property
    def nodes(self) -> dict[str, Node]:
        return dict(self._nodes)

    @property
    def edges(self) -> tuple[GraphEdge, ...]:
        return tuple(self._edges)

    def add_node(self, node_id: str, node: Node) -> None:
        if node_id in self._nodes:
            raise GraphError(f"duplicate node id: {node_id}")
        self._nodes[node_id] = node

    def connect(
        self,
        from_node: str,
        from_port: str,
        to_node: str,
        to_port: str,
    ) -> None:
        if from_node not in self._nodes:
            raise GraphError(f"unknown node: {from_node}")
        if to_node not in self._nodes:
            raise GraphError(f"unknown node: {to_node}")
        self._edges.append(GraphEdge(from_node, from_port, to_node, to_port))


class GraphExecutor:
    def __init__(self, graph: Graph) -> None:
        self._graph = graph
        self._trace: list[dict[str, Any]] = []

    @property
    def trace(self) -> list[dict[str, Any]]:
        return list(self._trace)

    def run(self, inputs: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
        order = self._topological_order()
        outputs: dict[str, dict[str, Any]] = {}
        self._trace = []

        for node_id in order:
            node_inputs = self._inputs_for(node_id, outputs)
            if inputs and node_id in inputs:
                node_inputs.update(inputs[node_id])
            node = self._graph.nodes[node_id]
            try:
                outputs[node_id] = node.run(node_inputs)
            except Exception as exc:
                raise NodeExecutionError(node_id, getattr(node, "name", type(node).__name__), exc) from exc
            self._trace.append(
                {
                    "node_id": node_id,
                    "inputs": dict(node_inputs),
                    "outputs": outputs[node_id],
                }
            )

        return outputs

    def _inputs_for(
        self,
        node_id: str,
        outputs: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        node_inputs: dict[str, Any] = {}
        for edge in self._graph.edges:
            if edge.to_node == node_id:
                node_inputs[edge.to_port] = outputs[edge.from_node][edge.from_port]
        return node_inputs

    def _topological_order(self) -> list[str]:
        nodes = self._graph.nodes
        incoming_count = {node_id: 0 for node_id in nodes}
        outgoing: dict[str, list[str]] = defaultdict(list)

        for edge in self._graph.edges:
            incoming_count[edge.to_node] += 1
            outgoing[edge.from_node].append(edge.to_node)

        ready = deque(node_id for node_id, count in incoming_count.items() if count == 0)
        order: list[str] = []

        while ready:
            node_id = ready.popleft()
            order.append(node_id)
            for target in outgoing[node_id]:
                incoming_count[target] -= 1
                if incoming_count[target] == 0:
                    ready.append(target)

        if len(order) != len(nodes):
            raise GraphError("graph contains a cycle")
        return order
