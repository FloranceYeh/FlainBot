from __future__ import annotations

from typing import Any

from ..builtins import (
    ChatInputNode,
    ChatOutputNode,
    DisplayDataNode,
    PersonaNode,
    PromptBuilderNode,
    SessionContextNode,
    TextInputNode,
)
from ..node_registry import NodeBuildContext, NodeBuilder
from ..providers import ProviderCallNode


def port(name: str, type_: str) -> dict[str, str]:
    return {"name": name, "type": type_}


def get_node_package() -> dict[str, Any]:
    return {
        "kind": "package",
        "id": "core",
        "title": "Core",
        "description": "Built-in nodes for web chat graphs.",
        "items": [
            {
                "kind": "group",
                "id": "io",
                "title": "Input / Output",
                "items": [
                    {
                        "kind": "group",
                        "id": "web-chat",
                        "title": "Web Chat",
                        "items": [
                            {
                                "kind": "node",
                                "package": "core",
                                "type": "chat_input",
                                "className": "ChatInputNode",
                                "title": "Web Chat Input",
                                "description": "Reads the user's message from the web chat input.",
                                "inputs": [],
                                "outputs": [port("text", "text")],
                                "defaults": {},
                            },
                            {
                                "kind": "node",
                                "package": "core",
                                "type": "chat_output",
                                "className": "ChatOutputNode",
                                "title": "Web Chat Output",
                                "description": "Sends model text to the web chat message list.",
                                "inputs": [port("text", "text")],
                                "outputs": [port("reply", "text")],
                                "defaults": {},
                            },
                        ],
                    }
                ],
            },
            {
                "kind": "group",
                "id": "processing",
                "title": "Processing",
                "items": [
                    {
                        "kind": "group",
                        "id": "prompting",
                        "title": "Prompting",
                        "items": [
                            {
                                "kind": "node",
                                "package": "core",
                                "type": "text_input",
                                "className": "TextInputNode",
                                "title": "Text Input",
                                "description": "Outputs manually configured text.",
                                "inputs": [],
                                "outputs": [port("text", "text")],
                                "defaults": {
                                    "text": "",
                                },
                            },
                            {
                                "kind": "node",
                                "package": "core",
                                "type": "display_data",
                                "className": "DisplayDataNode",
                                "title": "Display Data",
                                "description": "Formats text or raw JSON data for display.",
                                "inputs": [port("text", "text"), port("json", "json")],
                                "outputs": [port("text", "text"), port("json", "json")],
                                "defaults": {},
                            },
                            {
                                "kind": "node",
                                "package": "core",
                                "type": "session_context",
                                "className": "SessionContextNode",
                                "title": "Session Context",
                                "description": "Outputs the current web chat session history as JSON messages.",
                                "inputs": [],
                                "outputs": [port("json", "json")],
                                "defaults": {},
                            },
                            {
                                "kind": "node",
                                "package": "core",
                                "type": "prompt_builder",
                                "className": "PromptBuilderNode",
                                "title": "Prompt Builder",
                                "description": "Assembles system, user, tools, and context into a JSON prompt payload.",
                                "inputs": [
                                    port("system", "text"),
                                    port("user", "text"),
                                    port("tools", "json"),
                                    port("contexts", "json"),
                                ],
                                "outputs": [port("json", "json")],
                                "defaults": {
                                    "system_prompt": "",
                                    "user_prompt": "",
                                    "tools_json": "[]",
                                    "contexts_json": "[]",
                                },
                            },
                            {
                                "kind": "node",
                                "package": "core",
                                "type": "persona",
                                "className": "PersonaNode",
                                "title": "Apply Persona",
                                "description": "Applies a saved persona to text or a prompt JSON payload.",
                                "inputs": [port("text", "text"), port("json", "json")],
                                "outputs": [port("json", "json")],
                                "defaults": {
                                    "persona_id": "",
                                },
                            },
                        ],
                    },
                    {
                        "kind": "group",
                        "id": "providers",
                        "title": "Providers",
                        "items": [
                            {
                                "kind": "node",
                                "package": "core",
                                "type": "provider_call",
                                "className": "ProviderCallNode",
                                "title": "Call Provider",
                                "description": "Consumes text or prompt JSON and calls a configured provider.",
                                "inputs": [port("text", "text"), port("json", "json")],
                                "outputs": [
                                    port("text", "text"),
                                    port("request", "json"),
                                    port("response", "json"),
                                ],
                                "defaults": {
                                    "provider_id": "",
                                },
                            }
                        ],
                    },
                ],
            },
        ],
    }


def get_node_builders() -> dict[str, NodeBuilder]:
    return {
        "chat_input": build_chat_input,
        "chat_output": build_chat_output,
        "text_input": build_text_input,
        "display_data": build_display_data,
        "session_context": build_session_context,
        "prompt_builder": build_prompt_builder,
        "persona": build_persona,
        "provider_call": build_provider_call,
    }


def build_chat_input(node_config: dict[str, Any], context: NodeBuildContext) -> ChatInputNode:
    return ChatInputNode(context.message)


def build_chat_output(node_config: dict[str, Any], context: NodeBuildContext) -> ChatOutputNode:
    return ChatOutputNode()


def build_text_input(node_config: dict[str, Any], context: NodeBuildContext) -> TextInputNode:
    return TextInputNode(node_config.get("props", {}).get("text", ""))


def build_display_data(node_config: dict[str, Any], context: NodeBuildContext) -> DisplayDataNode:
    return DisplayDataNode()


def build_session_context(
    node_config: dict[str, Any],
    context: NodeBuildContext,
) -> SessionContextNode:
    return SessionContextNode(context.session_contexts)


def build_prompt_builder(
    node_config: dict[str, Any],
    context: NodeBuildContext,
) -> PromptBuilderNode:
    props = node_config.get("props", {})
    return PromptBuilderNode(
        system_prompt=props.get("system_prompt", ""),
        user_prompt=props.get("user_prompt", ""),
        tools_json=props.get("tools_json", "[]"),
        contexts_json=props.get("contexts_json", "[]"),
    )


def build_persona(node_config: dict[str, Any], context: NodeBuildContext) -> PersonaNode:
    props = node_config.get("props", {})
    persona_id = props["persona_id"]
    if persona_id not in context.personas:
        raise ValueError(f"persona not found: {persona_id}")
    return PersonaNode(persona=context.personas[persona_id])


def build_provider_call(
    node_config: dict[str, Any],
    context: NodeBuildContext,
) -> ProviderCallNode:
    props = node_config.get("props", {})
    provider_id = props["provider_id"]
    if provider_id not in context.providers:
        raise ValueError(f"provider not found: {provider_id}")
    provider = context.providers[provider_id]
    return ProviderCallNode(
        provider=provider,
        transport=context.transports.get(provider["format"]),
    )
