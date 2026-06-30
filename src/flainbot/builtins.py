from __future__ import annotations

import json
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


class PromptBuilderNode:
    name = "prompt_builder"

    def __init__(
        self,
        system_prompt: str = "",
        user_prompt: str = "",
        tools_json: str = "[]",
        context_json: str = "{}",
    ) -> None:
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.tools_json = tools_json
        self.context_json = context_json

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        tools = inputs.get("tools", self.tools_json)
        context = inputs.get("context", self.context_json)
        return {
            "json": {
                "system": inputs.get("system", self.system_prompt),
                "user": inputs.get("user", self.user_prompt),
                "tools": parse_json_value(tools, []),
                "context": parse_json_value(context, {}),
            }
        }


def parse_json_value(value: Any, empty_value: Any) -> Any:
    if value == "":
        return empty_value
    if isinstance(value, str):
        return json.loads(value)
    return value
