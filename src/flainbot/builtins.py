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


class TextInputNode:
    name = "text_input"

    def __init__(self, text: str = "") -> None:
        self.text = text

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return {"text": self.text}


class DisplayDataNode:
    name = "display_data"

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        raw = inputs["json"] if "json" in inputs else inputs.get("text", "")
        if isinstance(raw, str):
            text = raw
        else:
            text = json.dumps(raw, ensure_ascii=False, indent=2)
        return {"text": text, "json": raw}


class SessionContextNode:
    name = "session_context"

    def __init__(self, contexts: list[dict[str, Any]] | None = None) -> None:
        self.contexts = contexts or []

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return {"json": self.contexts}


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


class PersonaNode:
    name = "persona"

    def __init__(self, persona: dict[str, Any]) -> None:
        self.persona = normalize_persona(persona)

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        payload = prompt_payload_from_persona_inputs(inputs)
        persona_prompt = self.persona["system_prompt"]
        payload_prompt = payload.get("system_prompt", "")
        system_prompt = "\n\n".join(
            part for part in [persona_prompt, payload_prompt] if part
        )
        contexts = processed_begin_dialogs(self.persona["begin_dialogs"]) + parse_contexts(
            payload.get("contexts", [])
        )
        persona_tools = self.persona["tools"]
        tools = parse_json_value(persona_tools, []) if persona_tools is not None else parse_json_value(
            payload.get("tools", []), []
        )
        return {
            "json": {
                "system_prompt": system_prompt,
                "prompt": payload.get("prompt", ""),
                "contexts": contexts,
                "tools": tools,
                "skills": self.persona["skills"] or [],
                "custom_error_message": self.persona["custom_error_message"],
                "persona_id": self.persona["persona_id"],
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


def prompt_payload_from_persona_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    payload = inputs.get("json")
    if payload is None:
        payload = {"prompt": inputs.get("text", "")}
    if not isinstance(payload, dict):
        raise TypeError("persona json input must be an object")
    return {
        "system_prompt": payload.get("system_prompt", ""),
        "prompt": payload.get("prompt", ""),
        "contexts": payload.get("contexts", []),
        "tools": payload.get("tools", []),
    }


def normalize_persona(persona: dict[str, Any]) -> dict[str, Any]:
    return {
        "persona_id": str(persona.get("persona_id", "")).strip(),
        "system_prompt": str(persona.get("system_prompt", "")).strip(),
        "begin_dialogs": persona.get("begin_dialogs") or [],
        "tools": persona.get("tools"),
        "skills": persona.get("skills"),
        "custom_error_message": persona.get("custom_error_message"),
    }


def processed_begin_dialogs(begin_dialogs: list[str]) -> list[dict[str, Any]]:
    if len(begin_dialogs) % 2 != 0:
        raise ValueError("persona begin_dialogs must contain user/assistant pairs")
    messages = []
    user_turn = True
    for dialog in begin_dialogs:
        messages.append(
            {
                "role": "user" if user_turn else "assistant",
                "content": dialog,
                "_no_save": True,
            }
        )
        user_turn = not user_turn
    return messages
