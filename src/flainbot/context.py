from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NodeTrace:
    node_name: str
    status: str
    error: str | None = None


@dataclass
class MessageContext:
    input_text: str
    output_text: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    trace: list[NodeTrace] = field(default_factory=list)

