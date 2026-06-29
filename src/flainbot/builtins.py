from __future__ import annotations

from typing import Any

Request = dict[str, Any]
Response = dict[str, Any]


class ChatInputNode:
    name = "chat_input"

    def __init__(self, text: str) -> None:
        self.text = text

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return {"text": self.text}


class ChatOutputNode:
    name = "chat_output"

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return {"reply": inputs["text"]}
