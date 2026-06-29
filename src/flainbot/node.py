from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class Node(Protocol):
    name: str

    def run(self, inputs: Mapping[str, Any]) -> dict[str, Any]:
        ...
