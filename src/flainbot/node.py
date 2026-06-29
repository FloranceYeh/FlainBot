from __future__ import annotations

from typing import Protocol

from .context import MessageContext


class Node(Protocol):
    name: str

    def handle(self, context: MessageContext) -> None:
        ...

