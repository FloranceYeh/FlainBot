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
        contexts_json: str = "[]",
    ) -> None:
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.tools_json = tools_json
        self.contexts_json = contexts_json

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        tools = inputs.get("tools", self.tools_json)
        contexts = inputs.get("contexts", self.contexts_json)
        return {
            "json": {
                "system_prompt": inputs.get("system", self.system_prompt),
                "prompt": inputs.get("user", self.user_prompt),
                "tools": parse_json_value(tools, []),
                "contexts": parse_contexts(contexts),
            }
        }


def parse_json_value(value: Any, empty_value: Any) -> Any:
    if value == "":
        return empty_value
    if isinstance(value, str):
        return json.loads(value)
    return value


def parse_contexts(value: Any) -> list[dict[str, Any]]:
    contexts = parse_json_value(value, [])
    if contexts == {}:
        return []
    if not isinstance(contexts, list):
        raise TypeError("contexts must be a list of messages")
    return contexts
