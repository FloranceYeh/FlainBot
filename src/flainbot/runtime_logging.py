from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import uuid4

LogSink = Callable[[dict[str, Any]], Any]


class RuntimeLogger:
    def __init__(
        self,
        sink: LogSink | None = None,
        run_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        self._sink = sink
        self.run_id = run_id or f"run_{uuid4().hex}"
        self.session_id = session_id

    def info(self, source: str, message: str, **details: Any) -> None:
        self._publish("info", source, message, details)

    def warning(self, source: str, message: str, **details: Any) -> None:
        self._publish("warning", source, message, details)

    def error(self, source: str, message: str, **details: Any) -> None:
        self._publish("error", source, message, details)

    def node_info(self, event: str, node_id: str, node_type: str, **details: Any) -> None:
        self.info(
            "node",
            event,
            event=event,
            node_id=node_id,
            node_type=node_type,
            **details,
        )

    def node_error(self, event: str, node_id: str, node_type: str, **details: Any) -> None:
        self.error(
            "node",
            event,
            event=event,
            node_id=node_id,
            node_type=node_type,
            **details,
        )

    def for_node(self, node_id: str, node_type: str) -> NodeRuntimeLogger:
        return NodeRuntimeLogger(self, node_id, node_type)

    def _publish(self, level: str, source: str, message: str, details: dict[str, Any]) -> None:
        if self._sink is None:
            return
        payload = {
            "run_id": self.run_id,
            "session_id": self.session_id,
            **details,
        }
        self._sink(
            {
                "level": level,
                "source": source,
                "message": message,
                "details": payload,
            }
        )


class NodeRuntimeLogger:
    def __init__(self, logger: RuntimeLogger, node_id: str, node_type: str) -> None:
        self._logger = logger
        self.node_id = node_id
        self.node_type = node_type

    def info(self, event: str, **details: Any) -> None:
        self._logger.node_info(event, self.node_id, self.node_type, **details)

    def error(self, event: str, **details: Any) -> None:
        self._logger.node_error(event, self.node_id, self.node_type, **details)


class NullRuntimeLogger(RuntimeLogger):
    def __init__(self) -> None:
        super().__init__(sink=None)
